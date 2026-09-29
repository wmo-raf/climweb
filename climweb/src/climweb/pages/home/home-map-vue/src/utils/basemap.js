const rasterMapStyle = {
    version: 8,
    sources: {
       
        // --- OSM variants ---
        'osm-standard': {
            type: 'raster',
            tiles: [
                "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
                "https://b.tile.openstreetmap.org/{z}/{x}/{y}.png",
                "https://c.tile.openstreetmap.org/{z}/{x}/{y}.png"
            ],
            tileSize: 256,
            attribution: '© OpenStreetMap contributors'
        },

        // --- Terrain/Topo ---
        'open-topo': {
            type: 'raster',
            tiles: [
                "https://a.tile.opentopomap.org/{z}/{x}/{y}.png",
                "https://b.tile.opentopomap.org/{z}/{x}/{y}.png",
                "https://c.tile.opentopomap.org/{z}/{x}/{y}.png"
            ],
            tileSize: 256,
            attribution: '© OpenTopoMap contributors'
        },

        // --- ESRI (free, no key required) ---
         'esri-light-gray': {
            type: 'raster',
            tiles: [
                "https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"
            ],
            tileSize: 256,
            attribution: '© Esri © OpenStreetMap contributors'
        },
    },

    layers: [
        { id: 'osm-standard',           source: 'osm-standard',           type: 'raster', minzoom: 0, maxzoom: 19, layout: { visibility: 'none'    }, metadata: { 'mapbox:groups': 'background', basemap: 'osm-standard' } },
        { id: 'open-topo',              source: 'open-topo',              type: 'raster', minzoom: 0, maxzoom: 17, layout: { visibility: 'none'    }, metadata: { 'mapbox:groups': 'background', basemap: 'open-topo' } },
        { id: 'esri-light-gray',        source: 'esri-light-gray',        type: 'raster', minzoom: 0, maxzoom: 16, layout: { visibility: 'none'    }, metadata: { 'mapbox:groups': 'background', basemap: 'esri-light-gray' } },

     ]
};

// OpenFreeMap vector styles. They all share the same sources, sprite and glyphs,
// so they can be merged into one style and toggled via layer visibility.
export const OPENFREEMAP_STYLES = {
    'ofm-light': 'https://tiles.openfreemap.org/styles/positron',
    'ofm-bright': 'https://tiles.openfreemap.org/styles/bright',
    'ofm-dark': 'https://tiles.openfreemap.org/styles/dark',
};

export const getDefaultMapStyle = async (visibleBasemap) => {
    const style = {
        ...rasterMapStyle,
        sources: {...rasterMapStyle.sources},
        layers: rasterMapStyle.layers.map(layer => ({
            ...layer,
            layout: {...layer.layout, visibility: layer.id === visibleBasemap ? 'visible' : 'none'},
        })),
    };

    const ofmStyles = await Promise.all(
        Object.entries(OPENFREEMAP_STYLES).map(([id, url]) =>
            fetch(url)
                .then(res => res.json())
                .then(json => [id, json])
                .catch(e => {
                    console.error(`Error loading basemap style ${url}`, e);
                    return null;
                })
        )
    );

    ofmStyles.filter(Boolean).forEach(([basemapId, ofmStyle]) => {
        style.glyphs = ofmStyle.glyphs;
        style.sprite = ofmStyle.sprite;
        Object.assign(style.sources, ofmStyle.sources);

        ofmStyle.layers.forEach(layer => {
            style.layers.push({
                ...layer,
                id: `${basemapId}-${layer.id}`,
                layout: {...layer.layout, visibility: basemapId === visibleBasemap ? 'visible' : 'none'},
                metadata: {...layer.metadata, 'mapbox:groups': 'background', basemap: basemapId},
            });
        });
    });

    return style;
};
