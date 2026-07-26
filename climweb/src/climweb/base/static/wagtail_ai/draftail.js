/*
 * ClimWeb override of wagtail-ai's Draftail "ai" control (the editor "magic
 * wand").
 *
 * WHY THIS FILE EXISTS
 * --------------------
 * 1. wagtail-ai's own `wagtail_ai/draftail.js` crashes on Wagtail 7.3.x with
 *    React error #200 because its loading/error UI uses
 *    `ReactDOM.createPortal(...)` into DOM nodes that no longer exist. This
 *    file reimplements the control WITHOUT any createPortal (loading = animated
 *    wand icon, errors = window.alert).
 * 2. The AI model returns Markdown. Inserted as plain text it shows literal
 *    `**bold**` / `## heading` in a rich-text field. So we convert the Markdown
 *    to Draft.js rich-text content (bold, italics, headings, lists, links,
 *    blockquotes) before inserting it. If conversion fails for any reason we
 *    fall back to plain-text insertion.
 *
 * `climweb.base` is listed before `wagtail_ai` in INSTALLED_APPS, so this file
 * shadows the packaged one. Everything else (endpoint, config, prompts, the
 * per-site CMS key) is reused unchanged.
 */
(function () {
  "use strict";

  var React = window.React;
  var Draftail = window.Draftail;
  var DraftJS = window.DraftJS;
  var h = React.createElement;

  // ------------------------------------------------------------------ //
  // Markdown -> HTML (minimal; covers what the models typically emit).
  // ------------------------------------------------------------------ //
  function escapeHtml(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function inlineMd(s) {
    s = escapeHtml(s);
    // links [text](url)
    s = s.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, '<a href="$2">$1</a>');
    // bold **x** or __x__
    s = s.replace(/(\*\*|__)(.+?)\1/g, "<strong>$2</strong>");
    // italic *x* or _x_
    s = s.replace(/(^|[^\w*_])([*_])(?!\s)(.+?)(?!\s)\2(?![\w])/g, "$1<em>$3</em>");
    // inline code `x`
    s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
    return s;
  }

  function markdownToHtml(md) {
    var lines = (md || "").replace(/\r\n?/g, "\n").split("\n");
    var html = "";
    var i = 0;
    var isListItem = function (l) { return /^\s*[-*+]\s+/.test(l); };
    var isOrdered = function (l) { return /^\s*\d+\.\s+/.test(l); };
    while (i < lines.length) {
      var line = lines[i];
      if (/^\s*$/.test(line)) { i++; continue; }

      var head = line.match(/^\s*(#{1,6})\s+(.*)$/);
      if (head) {
        var lvl = head[1].length;
        html += "<h" + lvl + ">" + inlineMd(head[2]) + "</h" + lvl + ">";
        i++;
        continue;
      }

      if (isListItem(line)) {
        html += "<ul>";
        while (i < lines.length && isListItem(lines[i])) {
          html += "<li>" + inlineMd(lines[i].replace(/^\s*[-*+]\s+/, "")) + "</li>";
          i++;
        }
        html += "</ul>";
        continue;
      }

      if (isOrdered(line)) {
        html += "<ol>";
        while (i < lines.length && isOrdered(lines[i])) {
          html += "<li>" + inlineMd(lines[i].replace(/^\s*\d+\.\s+/, "")) + "</li>";
          i++;
        }
        html += "</ol>";
        continue;
      }

      if (/^\s*>\s?/.test(line)) {
        html += "<blockquote>" + inlineMd(line.replace(/^\s*>\s?/, "")) + "</blockquote>";
        i++;
        continue;
      }

      // paragraph: gather consecutive non-blank, non-block lines
      var para = [line];
      i++;
      while (
        i < lines.length &&
        !/^\s*$/.test(lines[i]) &&
        !/^\s*#{1,6}\s/.test(lines[i]) &&
        !isListItem(lines[i]) &&
        !isOrdered(lines[i]) &&
        !/^\s*>\s?/.test(lines[i])
      ) {
        para.push(lines[i]);
        i++;
      }
      html += "<p>" + inlineMd(para.join(" ")) + "</p>";
    }
    return html;
  }

  // ------------------------------------------------------------------ //
  // Insertion helpers.
  // ------------------------------------------------------------------ //

  // Convert Markdown to a Draft.js content fragment and insert it. `replace`
  // true swaps the whole field; false appends after the existing content.
  function insertMarkdown(editorState, markdown, replace) {
    var html = markdownToHtml(markdown);
    var parsed = DraftJS.convertFromHTML(html);
    if (!parsed || !parsed.contentBlocks || parsed.contentBlocks.length === 0) {
      throw new Error("empty conversion");
    }
    var fragmentContent = DraftJS.ContentState.createFromBlockArray(
      parsed.contentBlocks,
      parsed.entityMap
    );
    var fragment = fragmentContent.getBlockMap();
    var content = editorState.getCurrentContent();
    var selection;
    if (replace) {
      var blockMap = content.getBlockMap();
      selection = new DraftJS.SelectionState({
        anchorKey: blockMap.first().getKey(),
        anchorOffset: 0,
        focusKey: blockMap.last().getKey(),
        focusOffset: blockMap.last().getLength(),
      });
    } else {
      var last = content.getBlockMap().last();
      selection = new DraftJS.SelectionState({
        anchorKey: last.getKey(),
        anchorOffset: last.getLength(),
        focusKey: last.getKey(),
        focusOffset: last.getLength(),
      });
    }
    var newContent = DraftJS.Modifier.replaceWithFragment(content, selection, fragment);
    return DraftJS.EditorState.push(editorState, newContent, "insert-fragment");
  }

  // Plain-text fallbacks (used if Markdown conversion fails).
  function appendPlain(editorState, text) {
    var withNewline = DraftJS.RichUtils.insertSoftNewline(
      DraftJS.EditorState.moveSelectionToEnd(editorState)
    );
    var content = withNewline.getCurrentContent();
    var newContent = DraftJS.Modifier.replaceText(
      content,
      DraftJS.EditorState.moveSelectionToEnd(withNewline).getSelection(),
      text
    );
    return DraftJS.EditorState.push(withNewline, newContent, "insert-characters");
  }

  function replacePlain(editorState, text) {
    var content = editorState.getCurrentContent();
    var blockMap = content.getBlockMap();
    var selectAll = new DraftJS.SelectionState({
      anchorKey: blockMap.first().getKey(),
      anchorOffset: 0,
      focusKey: blockMap.last().getKey(),
      focusOffset: blockMap.last().getLength(),
    });
    var newContent = DraftJS.Modifier.replaceText(content, selectAll, text);
    return DraftJS.EditorState.push(editorState, newContent, "insert-characters");
  }

  // Apply the AI result: rich text if possible, plain text otherwise.
  function applyResult(editorState, text, isAppend) {
    try {
      return insertMarkdown(editorState, text, !isAppend);
    } catch (e) {
      return isAppend ? appendPlain(editorState, text) : replacePlain(editorState, text);
    }
  }

  // POST the whole field text + chosen prompt to wagtail-ai's endpoint.
  function requestCompletion(editorState, prompt, signal) {
    var text = editorState.getCurrentContent().getPlainText();
    var body = new FormData();
    body.append("text", text);
    body.append("prompt", prompt.uuid);
    var urls = window.wagtailAI.config.urls;
    var headers = {};
    headers[window.wagtailConfig.CSRF_HEADER_NAME] = window.wagtailConfig.CSRF_TOKEN;
    return fetch(urls.TEXT_COMPLETION, {
      method: "POST",
      headers: headers,
      body: body,
      signal: signal,
    }).then(function (response) {
      return response.json().then(function (data) {
        if (response.ok) return data.message;
        throw new Error(data.error || "The AI request failed. Please try again.");
      });
    });
  }

  // The dropdown listing the available prompts.
  function PromptDropdown(props) {
    return h(
      "div",
      { className: "Draftail-AI-ButtonDropdown" },
      props.aiPrompts.map(function (prompt) {
        return h(
          "button",
          {
            type: "button",
            key: prompt.uuid,
            onMouseDown: function () {
              props.onAction(prompt);
            },
          },
          h("span", null, prompt.label),
          " ",
          prompt.description
        );
      })
    );
  }

  // The toolbar control: a wand button that opens the prompt dropdown.
  function AIControl(props) {
    var getEditorState = props.getEditorState;
    var onChange = props.onChange;
    var aiPrompts = window.wagtailAI.config.aiPrompts;

    var loadingState = React.useState(false);
    var loading = loadingState[0];
    var setLoading = loadingState[1];

    var openState = React.useState(false);
    var open = openState[0];
    var setOpen = openState[1];

    function runPrompt(prompt) {
      setOpen(false);
      setLoading(true);
      var controller = new AbortController();
      var isAppend = prompt.method === "append";
      requestCompletion(getEditorState(), prompt, controller.signal)
        .then(function (message) {
          onChange(applyResult(getEditorState(), message, isAppend));
        })
        .catch(function (err) {
          if (err && err.name !== "AbortError") {
            window.alert(err.message || String(err));
          }
        })
        .then(function () {
          setLoading(false);
        });
    }

    return h(
      React.Fragment,
      null,
      h(Draftail.ToolbarButton, {
        name: "AI Tools",
        title: "AI prompts",
        icon: h(Draftail.Icon, {
          icon: loading ? "#icon-wand-animated" : "#icon-wand",
        }),
        onClick: function () {
          setOpen(!open);
        },
      }),
      open
        ? h(PromptDropdown, { aiPrompts: aiPrompts, onAction: runPrompt })
        : null
    );
  }

  window.draftail.registerPlugin({ type: "ai", inline: AIControl }, "controls");
})();
