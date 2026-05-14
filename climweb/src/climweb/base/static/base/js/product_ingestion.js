(function () {
    'use strict';

    // ── Pre-hide conditional fields immediately to prevent flicker ────────────
    // Runs synchronously when the <script> tag is parsed, before any paint.
    // init() removes this style and replaces it with explicit JS visibility control.
    var PRELOAD_ID = 'product-ingestion-preload';
    (function injectPreloadStyles() {
        if (document.getElementById(PRELOAD_ID)) return;
        var s = document.createElement('style');
        s.id = PRELOAD_ID;
        // Direct Product fields use <section aria-labelledby="panel-FIELD-heading">
        // Inline panel fields use <div class="w-panel__wrapper"> containing the label
        // and a <div data-field-wrapper id="...-FIELD-wrapper"> — target via :has().
        s.textContent = [
            'section[aria-labelledby="panel-variable_name-heading"]',
            'section[aria-labelledby="panel-temporal_resolution-heading"]',
            'section[aria-labelledby="panel-watch_root-heading"]',
            '.w-panel__wrapper:has([id$="-category_format-wrapper"])',
            '.w-panel__wrapper:has([id$="-file_name_convention-wrapper"])',
        ].join(',') + '{display:none !important}';
        (document.head || document.documentElement).appendChild(s);
    })();

    // Must mirror TEMPORAL_RESOLUTION_DEFAULT_CONVENTIONS in snippets.py
    var DEFAULT_CONVENTIONS = {
        yearly:   '{yyyy}_01_01_00_00_00',
        monthly:  '{yyyy}_{mm}_01_00_00_00',
        weekly:   '{yyyy}_{mm}_{dd}_00_00_00',
        daily:    '{yyyy}_{mm}_{dd}_00_00_00',
        hourly:   '{yyyy}_{mm}_{dd}_{hh}_00_00',
        dekadal:  '{yyyy}_{mm}_{dd}_00_00_00',
        pentadal: '{yyyy}_{mm}_{dd}_00_00_00'
    };

    var ALL_DEFAULTS = Object.values(DEFAULT_CONVENTIONS);

    // ── Panel section helpers ─────────────────────────────────────────────────

    /**
     * Find a direct Product field's panel section by field name.
     * Uses the exact aria-labelledby pattern from Wagtail 7:
     *   <section aria-labelledby="panel-variable_name-heading">
     */
    function getDirectFieldSection(fieldName) {
        return document.querySelector(
            'section[aria-labelledby="panel-' + fieldName + '-heading"]'
        );
    }

    // ── Visibility control ────────────────────────────────────────────────────

    function toggleIngestionFields(enabled) {
        ['variable_name', 'temporal_resolution', 'watch_root'].forEach(function (name) {
            var section = getDirectFieldSection(name);
            if (section) section.style.display = enabled ? '' : 'none';
        });
        updateInlineFieldVisibility(enabled);
    }

    function updateInlineFieldVisibility(enabled) {
        // Inline panel fields render as:
        //   <div class="w-panel__wrapper">          ← hide this
        //     <label>File Format</label>
        //     <div data-field-wrapper id="...-FIELD-wrapper">
        //       <input id="id_categories-0-FIELD">
        //     </div>
        //   </div>
        // parentElement of [data-field-wrapper] is the w-panel__wrapper to hide.
        ['category_format', 'file_name_convention'].forEach(function (fieldName) {
            document.querySelectorAll('[id$="-' + fieldName + '"]').forEach(function (input) {
                var fw = input.closest('[data-field-wrapper]');
                var container = fw ? fw.parentElement : null;
                if (container) container.style.display = enabled ? '' : 'none';
            });
        });
    }

    // ── Convention auto-fill ──────────────────────────────────────────────────

    function applyConventionToAll(resolution) {
        var convention = DEFAULT_CONVENTIONS[resolution] || '';
        if (!convention) return;
        document.querySelectorAll('[id$="-file_name_convention"]').forEach(function (input) {
            if (!input.value || ALL_DEFAULTS.indexOf(input.value) !== -1) {
                input.value = convention;
            }
        });
    }

    function applyConventionToEmpty(resolution) {
        var convention = DEFAULT_CONVENTIONS[resolution] || '';
        if (!convention) return;
        document.querySelectorAll('[id$="-file_name_convention"]').forEach(function (input) {
            if (!input.value) input.value = convention;
        });
    }

    // ── Bootstrap ─────────────────────────────────────────────────────────────

    function init() {
        var enabledCheckbox = document.getElementById('id_ingestion_enabled');
        var resolutionSelect = document.getElementById('id_temporal_resolution');

        if (!enabledCheckbox) return;

        // Hand off from CSS pre-hide to JS-controlled visibility
        var preload = document.getElementById(PRELOAD_ID);
        if (preload) preload.parentNode.removeChild(preload);

        toggleIngestionFields(enabledCheckbox.checked);

        if (resolutionSelect && resolutionSelect.value) {
            applyConventionToEmpty(resolutionSelect.value);
        }

        enabledCheckbox.addEventListener('change', function () {
            toggleIngestionFields(this.checked);
        });

        if (resolutionSelect) {
            resolutionSelect.addEventListener('change', function () {
                applyConventionToAll(this.value);
            });
        }

        // Watch for dynamically added inline panel rows
        new MutationObserver(function (mutations) {
            if (!mutations.some(function (m) { return m.addedNodes.length > 0; })) return;
            updateInlineFieldVisibility(enabledCheckbox.checked);
            if (resolutionSelect && resolutionSelect.value) {
                applyConventionToEmpty(resolutionSelect.value);
            }
        }).observe(document.body, { childList: true, subtree: true });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
