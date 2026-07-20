# AI Assistant

ClimWeb can add AI-powered writing tools (drafting, rewriting, correcting and
summarising text) directly inside the rich text editor, powered by
[Wagtail AI](https://wagtail-ai.readthedocs.io/).

The assistant is **optional and off by default**. 

## What you need

- An account and API key with one of the supported providers:
  - **OpenAI** — get a key at <https://platform.openai.com/api-keys>
  - **Anthropic (Claude)** — get a key at <https://console.anthropic.com/>

There is a cost per request charged by the provider. If your service cannot take
on a provider subscription, simply leave the assistant disabled — the rest of
the CMS works exactly as before.

## Turning it on

1. In the CMS, go to **Settings → AI Assistant**.
2. Tick **Enable AI assistant**.
3. Choose your **Provider** (OpenAI or Anthropic/Claude).
4. (Optional) **Model** — leave blank to use a sensible default
   (`gpt-4o-mini` for OpenAI, `claude-haiku-4.5` for Claude). Only set this if
   you specifically want a different model. Note: provider model names change
   over time — if you get a "model not found" (404) error, enter a current model
   id here (for Claude, run `llm models` to list the available ones).
5. Paste your **API key**.
6. **Save.**

The AI tools will now appear in the rich text editor toolbar. Editors select
some text, pick an action (for example *rewrite* or *correct spelling*), and the
suggested text is returned.

## About the API key

Your API key is **encrypted before it is stored** in the database,, and it is **write-only** in the form: after saving, the
field shows blank rather than displaying the key back. To change it, paste a new
key and save; to keep the current one, leave the field blank.


## Notes for administrators / deployment

- The `wagtail_ai` app is only loaded if the `wagtail-ai` package is present in
  the image. It is included in `requirements/base.in`
  (`wagtail-ai`, plus `llm-anthropic` for the Claude models). OpenAI models are
  built into the underlying "LLM" library; the `llm-anthropic` plugin is what
  makes the Claude option work.
- The provider, model and API key are read at request time from the
  `AISettings` CMS setting by a custom backend
  (`climweb.base.ai.backend.CMSConfiguredLLMBackend`), so no `OPENAI_API_KEY` /
  `ANTHROPIC_API_KEY` environment variable is required.
- If the assistant is enabled but no valid key is configured, the editor will
  show a clear error when an AI action is used, rather than failing silently.
- Beyond the editor wand, Wagtail AI's "agent" features — content feedback, image
  title/description, and the search-description suggestion on the page **Promote**
  tab — are also wired to the same per-site CMS key (via a small override of
  wagtail-ai's provider resolver in `climweb.base.ai.agent_provider`). No
  environment variable is needed. The agent path uses a different library
  (`any_llm`) whose model names differ slightly from the editor's; if an agent
  feature reports a "model not found", set an explicit, current model id in the
  **Model** field. The AI page-title panel is not enabled globally (title panels
  are defined per page type in ClimWeb); it can be added per model with
  `wagtail_ai.panels.AITitleFieldPanel`.


