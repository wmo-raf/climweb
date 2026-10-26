class Accordion {
    constructor(id, options = {}) {
        this.$accordion = $(`#${id}`);
        this.$accordion_header = this.$accordion.find(".js-accordion-header");

        // Default settings
        this.settings = {
            speed: 400, // Animation speed
            firstOpen: true, // Close all other accordion items if true
        };

        // Extend default settings with user-provided options
        $.extend(this.settings, options);

        this.init();
    }

    init() {
        // Headers are headings, not buttons: make them focusable and operable by keyboard
        this.$accordion_header.each((i, header) => {
            const body = $(header).next(".js-accordion-body")[0];
            if (body && !body.id) body.id = `${this.$accordion.attr("id")}-panel-${i}`;
            header.setAttribute("role", "button");
            header.setAttribute("tabindex", "0");
            if (body) header.setAttribute("aria-controls", body.id);
        });

        this.$accordion_header.on("click", (event) => {
            this.toggle($(event.currentTarget));
        });

        this.$accordion_header.on("keydown", (event) => {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                this.toggle($(event.currentTarget));
            }
        });

        // Some pages change the open items after init (e.g. collapsed on mobile)
        this.$accordion_header.on("focus", () => this.syncExpanded());

        if (this.settings.firstOpen) {
            this.$accordion.find(".js-accordion-item:first").addClass("active");
            this.$accordion.find(".js-accordion-item.active:not(:first)").removeClass("active");
        }

        // Reveal the active accordion bodies
        this.$accordion.find(".js-accordion-item.active").find("> .js-accordion-body").show();
        this.syncExpanded();
    }

    syncExpanded() {
        this.$accordion_header.each((i, header) => {
            const open = $(header).closest(".js-accordion-item").hasClass("active");
            header.setAttribute("aria-expanded", open ? "true" : "false");
        });
    }

    toggle($this) {
        if (
            this.settings.oneOpen &&
            $this[0] !=
            $this
                .closest(".js-accordion")
                .find("> .js-accordion-item.active > .js-accordion-header")[0]
        ) {
            $this
                .closest(".js-accordion")
                .find("> .js-accordion-item")
                .removeClass("active")
                .find(".js-accordion-body")
                .slideUp();
        }

        // Show/hide the clicked accordion item
        $this.closest(".js-accordion-item").toggleClass("active");
        $this
            .next()
            .stop()
            .slideToggle(this.settings.speed);
        this.syncExpanded();
    }
}


function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie != '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


const getParams = function (url) {
    const params = {};
    const parser = document.createElement('a');
    parser.href = url;
    const query = parser.search.substring(1);

    if (query) {
        const vars = query.split('&');

        for (let i = 0; i < vars.length; i++) {
            if (vars[i]) {
                const pair = vars[i].split('=');
                params[pair[0]] = decodeURIComponent(pair[1]);

            }
        }
    }
    return params
};

function markCheckboxesFromUrlParams(className, params = [], callback) {

    // take params and check appropriate checkboxes
    for (const param in params) {
        const split_param = params[param].split(',').filter(Boolean);

        const $filter = $(`.${className}.${param}`);

        $filter.each(function () {
            const $this = $(this);
            if (split_param.includes($this.val())) {
                $this.prop("checked", true)
            }
        });

        if (callback) {
            // pass params to callback
            callback(params)
        }
    }
}


function filterChangeListener(className, params = {}, callback) {

    const $filterInput = $(`.${className}`);


    $filterInput.on('click change', function (e) {

        const clicked = $(this);

        const nodeName = clicked.get(0).nodeName

        let changed = false
        let scrollToResults = true

        // If is input
        if (nodeName === 'INPUT') {
            if (e.type === 'change') {
                if (clicked.is(':checkbox')) {
                    const param = clicked.attr('name')
                    const value = clicked.val()
                    changed = true

                    if (clicked.is(':checked')) {
                        // add
                        if (params[param]) {
                            const param_values = params[param].split(',')
                            param_values.push(value)
                            params[param] = param_values.join(',')

                        } else {
                            params[param] = value
                        }
                    } else {
                        //remove
                        if (params[param]) {
                            const param_values = params[param].split(',')

                            const index = param_values.indexOf(value);

                            if (index !== -1) {
                                param_values.splice(index, 1);
                                params[param] = param_values.join(',')

                                if (!params[param]) {
                                    delete params[param]
                                }
                            }
                        }
                    }
                }
            }

        }

        // If is SELECT
        else if (nodeName === 'SELECT') {
            if (e.type === 'change') {
                const param = clicked.attr('name')
                params[param] = clicked.val()

                changed = true
                scrollToResults = false
            }
        }
        // If is button
        else if (nodeName === 'BUTTON' && clicked.attr('name') === 'view') {
            if (!clicked.hasClass('active')) {
                params['view'] = clicked.val()
            }
            changed = true
        }

        // if anything changed
        if (changed) {
            const url_params = urlParamsFromObject(params)

            if (callback) {
                callback(clicked, url_params, scrollToResults)
            }
        }
    });
}

function urlParamsFromObject(paramsObject, exclude = []) {

    return Object.keys(paramsObject).reduce(function (all, key) {
        const value = paramsObject[key]

        if (!exclude.includes(key)) {
            if (value) {
                if (all) {
                    all = all + `&${key}=${value}`
                } else {
                    all = `${key}=${value}`
                }
            }

        }
        return all
    }, '')
}


function copyToClipboard(value) {
    const $temp = $("<input>");
    $("body").append($temp);
    $temp.val(value).select();
    document.execCommand("copy");
    $temp.remove();
}


const topAlert = $('.top-alert');

function setNotificationStorage(config) {
    try {
        localStorage.setItem("notification", JSON.stringify(config))
    } catch (e) {
        console.log("Error with setting localstorage", e)
    }
}


function initializeNotification(notification_id) {


    let notificationConfig = JSON.parse(localStorage.getItem("notification"))

    if (!notificationConfig || notificationConfig.id !== notification_id) {
        notificationConfig = {"id": notification_id, "show": true}
        setNotificationStorage(notificationConfig)

    }
    if (notificationConfig.show) {
        topAlert.css({display: "flex"})
    }


}

function hideAlert(notification_id) {
    let notificationConfig = JSON.parse(localStorage.getItem("notification"))

    if (notificationConfig && notificationConfig.id === notification_id) {
        notificationConfig = {"id": notification_id, "show": false}
        setNotificationStorage(notificationConfig)
    }

    topAlert.fadeOut()
}

function ga_reg_event(action, gtag_data) {
    gtag('event', action, gtag_data);
}


function ga_reg_event_from_el(el) {
    const $this = $(el)
    let action = 'click'
    const gtag_data = {
        "event_category": "Link",
        "event_label": $this.text().trim().substring(0, 30)
    };
    if ($this.data('ga-event-category')) {
        gtag_data['event_category'] = $this.data('ga-event-category');
    }
    if ($this.data('ga-event-label')) {
        gtag_data['event_label'] = $this.data('ga-event-label');
    }
    if ($this.data('ga-value')) {
        gtag_data['value'] = $this.data('ga-value');
    }
    if ($this.data('ga-action')) {
        action = $this.data('ga-action');
    }
    ga_reg_event(action, gtag_data)
}

/**
 * Read a message out to screen reader users via the live regions in base.html.
 * Pass assertive=true for errors that should interrupt.
 */
function announce(message, assertive) {
    const region = document.getElementById(assertive ? "a11y-announcer-assertive" : "a11y-announcer-polite");
    if (!region || !message) return;

    // Messages may contain HTML; parse as an inert document so only the text is read
    const text = typeof message === "string"
        ? new DOMParser().parseFromString(message, "text/html").body.textContent
        : message.textContent;

    // Clear first so repeating the same message is announced again
    region.textContent = "";
    setTimeout(function () {
        region.textContent = (text || "").trim();
    }, 100);
}


$(document).ready(function () {

        const $navbarMenu = $("nav.navbar .main-nav.navbar-menu");
        const $navbarBurger = $("#navBurger");

        // close navbar menu on clicking outside
        $(document).click(function (event) {
            const clickOver = $(event.target);

            const isMenuActive = $navbarMenu.hasClass("is-active");

            if (isMenuActive === true && !clickOver.hasClass("is-active")) {
                $navbarMenu.removeClass('is-active');
                $navbarBurger.removeClass('is-active');
            }
        });

        /* ── SEARCH TOGGLE ── */
        const searchTrigger = document.getElementById('search-trigger');
        const searchInput   = document.getElementById('search-input');
        const inputEl       = document.getElementById('input-el');

        const setSearchOpen = function (open) {
            searchInput.style.display = open ? 'block' : 'none';
            searchTrigger.setAttribute('aria-expanded', open ? 'true' : 'false');
        };

        if (searchTrigger && searchInput) {
        searchTrigger.addEventListener('click', function (e) {
            e.stopPropagation();
            const isVisible = searchInput.style.display !== 'none';
            setSearchOpen(!isVisible);
            if (!isVisible && inputEl) inputEl.focus();
        });

        /* close when clicking outside the search area */
        document.addEventListener('click', function (e) {
            if (
            searchInput.style.display !== 'none' &&
            !searchInput.contains(e.target) &&
            !searchTrigger.contains(e.target)
            ) {
            setSearchOpen(false);
            }
        });
        }

        /* submit on Enter */
        if (inputEl) {
        inputEl.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
            e.preventDefault();
            const q = this.value.trim();
            if (q) this.closest('form').submit();
            }
        });
        }

        /* close search on Escape */
        document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && searchInput && searchInput.style.display !== 'none') {
            setSearchOpen(false);
            searchTrigger.focus();
        }
        });

        /* ── LANGUAGE MENU ── opens on hover (CSS) or click/Enter/Space; Esc closes */
        $(".util-dropdown").each(function () {
            const dropdown = this;
            const trigger = dropdown.querySelector(".util-dropdown-trigger");
            if (!trigger) return;

            const setOpen = function (open) {
                dropdown.classList.toggle("is-open", open);
                trigger.setAttribute("aria-expanded", open ? "true" : "false");
            };

            trigger.addEventListener("click", function (e) {
                e.stopPropagation();
                setOpen(!dropdown.classList.contains("is-open"));
            });

            dropdown.addEventListener("keydown", function (e) {
                if (e.key === "Escape" && dropdown.classList.contains("is-open")) {
                    setOpen(false);
                    trigger.focus();
                }
            });

            dropdown.querySelectorAll(".util-dropdown-item").forEach(function (item) {
                item.addEventListener("click", function () {
                    setOpen(false);
                    trigger.focus();
                });
            });

            dropdown.addEventListener("focusout", function (e) {
                if (!dropdown.contains(e.relatedTarget)) setOpen(false);
            });

            document.addEventListener("click", function (e) {
                if (!dropdown.contains(e.target)) setOpen(false);
            });
        });
        const default_lang = "en-us"

        $(".util-dropdown-item[data-lang-prefix]").on("click", function () {

            const lang_text = $(this).attr("data-lang")

            const lang_prefix = $(this).attr("data-lang-prefix")

            doGoogleLanguageTranslator(default_lang, lang_prefix, lang_text);

            if (typeof cr_track_clicks !== 'undefined' && cr_track_clicks) {
                // tract language change
                ga_reg_event('click', {
                    "event_category": "Header Navigation",
                    "event_label": "Change Language",
                    "value": lang_text,
                })
            }
        })

        /*** Tracking ***/
        if (typeof cr_track_clicks !== 'undefined' && cr_track_clicks) {
            $('a').not('[data-lang]').on('click', function () {
                ga_reg_event_from_el(this)
            });
        }

        /*** Social share buttons with no native "share link" support
         * (e.g. TikTok): copy the link to the clipboard, then open the
         * platform so the user can paste it in. ***/
        $(document).on('click', '[data-copy-link]', function (e) {
            e.preventDefault();

            const $btn = $(this);
            const link = $btn.attr('data-copy-link');
            const target = $btn.attr('href');
            const platform = $btn.attr('data-ga-event-label') || 'the app';

            const openTarget = function () {
                window.open(target, '_blank', 'noopener');
            };

            if (navigator.clipboard && navigator.clipboard.writeText && link) {
                navigator.clipboard.writeText(link).then(function () {
                    if (typeof bulmaToast !== 'undefined') {
                        bulmaToast.toast({
                            message: 'Link copied to clipboard — paste it in ' + platform,
                            type: 'is-info',
                        });
                    }
                    openTarget();
                }, openTarget);
            } else {
                openTarget();
            }
        });
    }
);
/**
 * MapLibre labels every map just "Map". To tell screen reader users what a map shows,
 * add data-map-label="..." to its container; the label is copied onto the map's
 * focusable element once the map exists, whichever script created it.
 * Works for MapLibre (the canvas) and Leaflet (the container itself).
 */
(function () {
    if (!document.querySelector("[data-map-label]")) return;

    function labelMaps() {
        document.querySelectorAll("[data-map-label]").forEach(function (container) {
            const target = container.querySelector(".maplibregl-canvas") ||
                (container.classList.contains("leaflet-container") ? container : null);
            const label = container.dataset.mapLabel;
            if (target && label && target.getAttribute("aria-label") !== label) {
                target.setAttribute("aria-label", label);
                // MapLibre's canvas already has role="region"; Leaflet's container has no role
                if (!target.hasAttribute("role")) target.setAttribute("role", "region");
            }
        });
    }

    labelMaps();
    // maps are created after page load (and some after data fetches), so watch for them
    new MutationObserver(labelMaps).observe(document.body, { childList: true, subtree: true });
})();

/**
 * Collapsible blocks (.ac-wrap): each page's own script opens/closes items by toggling
 * .ac-item--open. This keeps the header buttons' aria-expanded/aria-controls in step.
 * Runs on document, so it fires after the page's handler on the header.
 */
(function () {
    function syncCollapsibles(root) {
        root.querySelectorAll(".ac-header").forEach(function (header) {
            const item = header.closest(".ac-item");
            const body = item && item.querySelector(".ac-body");
            if (!item) return;
            if (body) {
                if (!body.id) body.id = "ac-body-" + Math.random().toString(36).slice(2, 9);
                header.setAttribute("aria-controls", body.id);
            }
            header.setAttribute("aria-expanded", item.classList.contains("ac-item--open") ? "true" : "false");
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        syncCollapsibles(document);
    });

    document.addEventListener("click", function (e) {
        const header = e.target.closest && e.target.closest(".ac-header");
        if (header) syncCollapsibles(header.closest(".ac-wrap") || document);
    });
})();

/**
 * Bulma modals (.modal): pages open and close them by toggling .is-active, each with
 * its own script. This adds the keyboard/screen reader behaviour to all of them:
 * dialog semantics, focus moved into the modal and kept there, Esc to close, and
 * focus returned to whatever opened it.
 */
(function () {
    const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), ' +
        'select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';
    let lastActivated = null;

    function focusableIn(modal) {
        return Array.prototype.filter.call(modal.querySelectorAll(FOCUSABLE), function (el) {
            return !el.closest(".modal-background") && el.offsetParent !== null;
        });
    }

    function activeModal() {
        return document.querySelector(".modal.is-active");
    }

    function onOpen(modal) {
        modal.setAttribute("role", "dialog");
        modal.setAttribute("aria-modal", "true");
        const title = modal.querySelector(".modal-card-title, h1, h2, h3, h4, h5, h6");
        if (title && !modal.hasAttribute("aria-labelledby") && !modal.hasAttribute("aria-label")) {
            if (!title.id) title.id = "modal-title-" + Math.random().toString(36).slice(2, 9);
            modal.setAttribute("aria-labelledby", title.id);
        }
        modal._a11yOpener = lastActivated;

        const targets = focusableIn(modal);
        if (targets.length) {
            targets[0].focus();
        } else {
            const content = modal.querySelector(".modal-card, .modal-content") || modal;
            content.setAttribute("tabindex", "-1");
            content.focus();
        }
    }

    function onClose(modal) {
        const opener = modal._a11yOpener;
        modal._a11yOpener = null;
        if (opener && document.contains(opener) && !activeModal()) opener.focus();
    }

    // Remember the control that was activated, so focus can go back to it on close
    document.addEventListener("click", function (e) {
        const el = e.target.closest && e.target.closest(FOCUSABLE);
        if (el && !el.closest(".modal")) lastActivated = el;
    }, true);

    document.addEventListener("keydown", function (e) {
        const modal = activeModal();
        if (!modal) return;
        if (e.key === "Escape") {
            modal.classList.remove("is-active");
        } else if (e.key === "Tab") {
            const targets = focusableIn(modal);
            if (!targets.length) { e.preventDefault(); return; }
            const first = targets[0], last = targets[targets.length - 1];
            if (e.shiftKey && (document.activeElement === first || !modal.contains(document.activeElement))) {
                e.preventDefault(); last.focus();
            } else if (!e.shiftKey && (document.activeElement === last || !modal.contains(document.activeElement))) {
                e.preventDefault(); first.focus();
            }
        }
    });

    document.addEventListener("DOMContentLoaded", function () {
        const observer = new MutationObserver(function (mutations) {
            mutations.forEach(function (m) {
                const modal = m.target;
                const wasActive = (m.oldValue || "").split(/\s+/).indexOf("is-active") !== -1;
                const isActive = modal.classList.contains("is-active");
                if (isActive && !wasActive) onOpen(modal);
                if (!isActive && wasActive) onClose(modal);
            });
        });
        document.querySelectorAll(".modal").forEach(function (modal) {
            observer.observe(modal, { attributes: true, attributeFilter: ["class"], attributeOldValue: true });
        });
    });
})();

/**
 * Bulma tabs used as in-page tabs (<div class="tabs"><ul><li><a> with no href):
 * each page switches panels with its own click handler on the <li>. This makes the tabs
 * reachable and operable by keyboard and announces which one is selected.
 * Tab bars made of real links (<a href>) are navigation and are left alone.
 */
(function () {
    function panelFor(li) {
        const key = li.dataset.content || li.dataset.target || li.dataset.id;
        return key ? document.getElementById(key) : null;
    }

    function sync(list) {
        list.querySelectorAll(":scope > li > a").forEach(function (a) {
            a.setAttribute("aria-selected", a.parentElement.classList.contains("is-active") ? "true" : "false");
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll(".tabs > ul").forEach(function (list) {
            const links = list.querySelectorAll(":scope > li > a");
            if (!links.length || list.querySelector(":scope > li > a[href]")) return;

            list.setAttribute("role", "tablist");
            list.querySelectorAll(":scope > li").forEach(function (li) {
                li.setAttribute("role", "presentation");
            });
            links.forEach(function (a) {
                a.setAttribute("role", "tab");
                a.setAttribute("tabindex", "0");
                const panel = panelFor(a.parentElement);
                if (panel) {
                    if (!a.id) a.id = "tab-" + Math.random().toString(36).slice(2, 9);
                    a.setAttribute("aria-controls", panel.id);
                    panel.setAttribute("role", "tabpanel");
                    panel.setAttribute("aria-labelledby", a.id);
                }
                a.addEventListener("keydown", function (e) {
                    if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        a.click();
                    }
                });
            });

            sync(list);
            // page handlers toggle .is-active on click; update after they run
            list.addEventListener("click", function () { setTimeout(function () { sync(list); }, 0); });
        });
    });
})();

/**
 * Toggle buttons that pages mark with .active (list/grid view switches, the stations
 * "Colour by" switch): expose that state to screen readers as aria-pressed, whether it
 * changes on click or is restored from the URL on load.
 */
(function () {
    const TOGGLES = "#list-view-button, #grid-view-button, .stn-toggle-btn";

    function sync(btn) {
        btn.setAttribute("aria-pressed", btn.classList.contains("active") ? "true" : "false");
    }

    document.addEventListener("DOMContentLoaded", function () {
        const buttons = document.querySelectorAll(TOGGLES);
        if (!buttons.length) return;
        const observer = new MutationObserver(function (mutations) {
            mutations.forEach(function (m) { sync(m.target); });
        });
        buttons.forEach(function (btn) {
            sync(btn);
            observer.observe(btn, { attributes: true, attributeFilter: ["class"] });
        });
    });
})();
