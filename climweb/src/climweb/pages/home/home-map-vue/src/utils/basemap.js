export const defaultMapStyle = {
    version: 8,
    glyphs: "https://tiles.basemaps.cartocdn.com/fonts/{fontstack}/{range}.pbf",
    sources: {
       
        // --- existing ---
        'voyager': {
            type: 'raster',
            tiles: [
                "https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png",
                "https://b.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png",
                "https://c.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png",
                "https://d.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png"
            ],
            tileSize: 256,
            attribution: '© OpenStreetMap © CARTO'
        },
        'carto-dark': {
            type: 'raster',
            tiles: [
                "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
                "https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
                "https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
                "https://d.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"
            ],
            tileSize: 256,
            attribution: '© OpenStreetMap © CARTO'
        },
        'carto-light': {
            type: 'raster',
            tiles: [
                "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
                "https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
                "https://c.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
                "https://d.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png"
            ],
            tileSize: 256,
            attribution: '© OpenStreetMap © CARTO'
        },
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
        { id: 'voyager',                source: 'voyager',                type: 'raster', minzoom: 0, maxzoom: 22, layout: { visibility: 'none' }, metadata: { 'mapbox:groups': 'background' } },
        { id: 'carto-light',            source: 'carto-light',            type: 'raster', minzoom: 0, maxzoom: 22, layout: { visibility: 'none'    }, metadata: { 'mapbox:groups': 'background' } },
        { id: 'carto-dark',             source: 'carto-dark',             type: 'raster', minzoom: 0, maxzoom: 22, layout: { visibility: 'none'    }, metadata: { 'mapbox:groups': 'background' } },
        { id: 'osm-standard',           source: 'osm-standard',           type: 'raster', minzoom: 0, maxzoom: 19, layout: { visibility: 'none'    }, metadata: { 'mapbox:groups': 'background' } },
        { id: 'open-topo',              source: 'open-topo',              type: 'raster', minzoom: 0, maxzoom: 17, layout: { visibility: 'none'    }, metadata: { 'mapbox:groups': 'background' } },
        { id: 'esri-light-gray',        source: 'esri-light-gray',        type: 'raster', minzoom: 0, maxzoom: 16, layout: { visibility: 'visible'    }, metadata: { 'mapbox:groups': 'background' } },

     ]
};