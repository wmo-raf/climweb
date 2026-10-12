function triggerHtmlEvent(element, eventName) {
    let event;
    if (document.createEvent) {
        event = document.createEvent("HTMLEvents");
        event.initEvent(eventName, true, true);
        element.dispatchEvent(event);
    } else {
        event = document.createEventObject();
        event.eventType = eventName;
        element.fireEvent("on" + event.eventType, event);
    }
}

function setDirectionBasedOnLang(lang) {
    // Keep in sync with RTL_LANGUAGES in base/templatetags/nmhs_cms_tags.py
    const rtlLangs = ["ar", "fa", "he", "ur"];  // Add more RTL languages if needed

    // Tell screen readers which language the page is now in, so they use the right voice
    document.documentElement.setAttribute("lang", lang);

    if (rtlLangs.includes(lang.slice(0, 2))) {
        document.documentElement.setAttribute("dir", "rtl");
        document.body.classList.add("rtl");
        document.body.classList.remove("ltr");
    } else {
        document.documentElement.setAttribute("dir", "ltr");
        document.body.classList.add("ltr");
        document.body.classList.remove("rtl");
    }
}


function doGoogleLanguageTranslator(default_lang, lang_prefix) {
    // console.log(default_lang, )
    // console.log(lang_prefix, )
    console.log("Default:", default_lang);
    console.log("Selected:", lang_prefix);

    let event;

    const classic = $(".goog-te-combo");

    for (let i = 0; i < classic.length; i++) {
        event = classic[i];
    }

    if (document.getElementById("google_language_translator") != null) {
        if (classic.length !== 0) {
            if (lang_prefix !== default_lang) {
                event.value = lang_prefix;
                triggerHtmlEvent(event, "change");
                // ✅ Apply direction change
                setDirectionBasedOnLang(lang_prefix);
            } else {

                $(".goog-te-banner-frame:first")
                    .contents()
                    .find(".goog-close-link")
                    .get(0)
                    .click();

                 // ✅ Reset to default language direction
                setDirectionBasedOnLang(document.documentElement.dataset.defaultLang || default_lang);
            }
        }
    }
}

