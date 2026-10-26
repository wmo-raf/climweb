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
        this.$accordion_header.on("click", (event) => {
            this.toggle($(event.currentTarget));
        });

        if (this.settings.firstOpen) {
            this.$accordion.find(".js-accordion-item:first").addClass("active");
            this.$accordion.find(".js-accordion-item.active:not(:first)").removeClass("active");
        }

        // Reveal the active accordion bodies
        this.$accordion.find(".js-accordion-item.active").find("> .js-accordion-body").show();
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
