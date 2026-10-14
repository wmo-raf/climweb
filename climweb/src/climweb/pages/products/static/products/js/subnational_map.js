(function () {
    const configEl = document.getElementById("subnational-map-config");
    if (!configEl) {
        return;
    }

    const config = JSON.parse(configEl.textContent);
    const cards = Array.from(document.querySelectorAll(".subnational-card"));
    const panel = document.querySelector(".subnational-map-panel");

    const primaryColor = getComputedStyle(document.documentElement).getPropertyValue("--primary-color").trim() || "#3e8ed0";
    const colors = {
        available: primaryColor,
        selected: "#f5a524",
        outline: "#1f2d3d",
    };

    const map = new maplibregl.Map({
        container: "subnational-map",
        style: "https://tiles.openfreemap.org/styles/positron",
        doubleClickZoom: false,
        cooperativeGestures: true,
        attributionControl: false,
    });

    map.addControl(new maplibregl.AttributionControl({compact: true}));
    map.addControl(new maplibregl.NavigationControl({showCompass: false}));
    map.addControl(new maplibregl.FullscreenControl());

    const popup = new maplibregl.Popup({closeButton: false, closeOnClick: false, offset: 8});

    const fitToBounds = (animate) => {
        if (config.bounds) {
            const b = config.bounds;
            map.fitBounds([[b[0], b[1]], [b[2], b[3]]], {padding: 40, maxZoom: 9, animate});
        }
    };

    const levelFilter = (level, gidKey, gids) => [
        "all",
        ["==", ["get", "level"], level],
        ["in", ["get", gidKey], ["literal", gids]],
    ];

    const fillColor = (gidKey, selectedGids) => [
        "case",
        ["in", ["get", gidKey], ["literal", selectedGids]], colors.selected,
        colors.available,
    ];

    const navigate = (changes) => {
        const params = new URLSearchParams(window.location.search);
        ["district", "subdistrict", "region", "page"].forEach(key => params.delete(key));
        Object.entries(changes).forEach(([key, value]) => params.set(key, value));
        window.location.href = `${window.location.pathname}?${params.toString()}#results`;
    };

    // highlight the outline of an area, or clear it when gid is null
    const setHoverOutline = (level, gid) => {
        map.setFilter("district-hover", levelFilter(1, "gid_1", level === 1 && gid ? [gid] : []));
        map.setFilter("sub-district-hover", levelFilter(2, "gid_2", level === 2 && gid ? [gid] : []));
    };

    const highlightCards = (level, gid) => {
        cards.forEach(card => {
            const match = gid && (level === 1 ? card.dataset.district === gid : card.dataset.subdistrict === gid);
            card.classList.toggle("is-highlighted", Boolean(match));
        });
    };

    map.on("load", () => {
        fitToBounds(false);

        map.addSource("admin-boundary-source", {
            type: "vector",
            tiles: [config.boundaryTilesUrl],
        });

        map.addSource("labels-source", {
            type: "geojson",
            data: config.labels,
        });

        // country outline
        map.addLayer({
            id: "country-line",
            type: "line",
            source: "admin-boundary-source",
            "source-layer": "default",
            filter: ["==", ["get", "level"], 0],
            paint: {"line-color": colors.outline, "line-width": 1.5},
        });

        // districts with products
        map.addLayer({
            id: "district-fill",
            type: "fill",
            source: "admin-boundary-source",
            "source-layer": "default",
            filter: levelFilter(1, "gid_1", config.districts),
            paint: {
                "fill-color": fillColor("gid_1", config.selectedDistricts),
                "fill-opacity": 0.35,
            },
        });

        map.addLayer({
            id: "district-line",
            type: "line",
            source: "admin-boundary-source",
            "source-layer": "default",
            filter: levelFilter(1, "gid_1", config.districts),
            paint: {"line-color": colors.available, "line-width": 1.5},
        });

        // sub-districts with products, drawn on top of their district
        map.addLayer({
            id: "sub-district-fill",
            type: "fill",
            source: "admin-boundary-source",
            "source-layer": "default",
            filter: levelFilter(2, "gid_2", config.subDistricts),
            paint: {
                "fill-color": fillColor("gid_2", config.selectedSubDistricts),
                "fill-opacity": 0.6,
            },
        });

        map.addLayer({
            id: "sub-district-line",
            type: "line",
            source: "admin-boundary-source",
            "source-layer": "default",
            filter: levelFilter(2, "gid_2", config.subDistricts),
            paint: {"line-color": colors.available, "line-width": 1, "line-dasharray": [2, 1]},
        });

        // hover outlines, driven by the map and by the result cards
        map.addLayer({
            id: "district-hover",
            type: "line",
            source: "admin-boundary-source",
            "source-layer": "default",
            filter: levelFilter(1, "gid_1", []),
            paint: {"line-color": colors.outline, "line-width": 3},
        });

        map.addLayer({
            id: "sub-district-hover",
            type: "line",
            source: "admin-boundary-source",
            "source-layer": "default",
            filter: levelFilter(2, "gid_2", []),
            paint: {"line-color": colors.outline, "line-width": 3},
        });

        // area names, sub-district names only once zoomed in
        const labelLayer = (id, level, size, minzoom) => ({
            id,
            type: "symbol",
            source: "labels-source",
            minzoom,
            filter: ["==", ["get", "level"], level],
            layout: {
                "text-field": ["get", "name"],
                "text-font": ["Noto Sans Bold"],
                "text-size": size,
            },
            paint: {
                "text-color": colors.outline,
                "text-halo-color": "#fff",
                "text-halo-width": 1.5,
            },
        });

        map.addLayer(labelLayer("district-labels", 1, 13, 0));
        map.addLayer(labelLayer("sub-district-labels", 2, 11, 8));

        const clickableLayers = ["sub-district-fill", "district-fill"];

        // sub-districts are on top, so prefer them when both are under the pointer
        const featureAt = (point) => {
            const features = map.queryRenderedFeatures(point, {layers: clickableLayers});
            return features.find(f => f.layer.id === "sub-district-fill") || features[0];
        };

        let hovered = null;

        map.on("mousemove", (e) => {
            const feature = featureAt(e.point);
            map.getCanvas().style.cursor = feature ? "pointer" : "";

            if (!feature) {
                if (hovered) {
                    hovered = null;
                    popup.remove();
                    setHoverOutline(null, null);
                    highlightCards(null, null);
                }
                return;
            }

            const props = feature.properties;
            const isSubDistrict = feature.layer.id === "sub-district-fill";
            const level = isSubDistrict ? 2 : 1;
            const gid = isSubDistrict ? props.gid_2 : props.gid_1;

            popup.setLngLat(e.lngLat).setText(isSubDistrict ? props.name_2 : props.name_1).addTo(map);

            if (!hovered || hovered.gid !== gid) {
                hovered = {level, gid};
                setHoverOutline(level, gid);
                highlightCards(level, gid);
            }
        });

        map.getCanvas().addEventListener("mouseleave", () => {
            hovered = null;
            popup.remove();
            setHoverOutline(null, null);
            highlightCards(null, null);
        });

        map.on("click", (e) => {
            const feature = featureAt(e.point);
            if (!feature) {
                return;
            }

            const props = feature.properties;
            if (feature.layer.id === "sub-district-fill") {
                navigate({district: props.gid_1, subdistrict: props.gid_2});
            } else {
                navigate({district: props.gid_1});
            }
        });

        cards.forEach(card => {
            card.addEventListener("mouseenter", () => {
                if (card.dataset.subdistrict) {
                    setHoverOutline(2, card.dataset.subdistrict);
                } else if (card.dataset.district) {
                    setHoverOutline(1, card.dataset.district);
                }
            });
            card.addEventListener("mouseleave", () => setHoverOutline(null, null));
        });
    });

    // collapsible map on small screens
    const toggle = document.querySelector(".subnational-map-toggle");
    if (toggle && panel) {
        toggle.addEventListener("click", () => {
            const collapsed = panel.classList.toggle("is-collapsed");
            toggle.setAttribute("aria-expanded", String(!collapsed));
            if (!collapsed) {
                map.resize();
                fitToBounds(false);
            }
        });
    }
})();
