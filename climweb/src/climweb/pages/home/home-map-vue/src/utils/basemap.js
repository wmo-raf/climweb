export const defaultMapStyle = {
    version: 8,
    glyphs: "https://tiles.basemaps.cartocdn.com/fonts/{fontstack}/{range}.pbf",
    sources: {
        'voyager': {
            type: 'raster',
            tiles: [
                "https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png",
                "https://b.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png",
                "https://c.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png",
                "https://d.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png"
            ]
        },
        'carto-dark': {
            type: 'raster',
            tiles: [
                "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
                "https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
                "https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
                "https://d.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"
            ]
        },
        'carto-light': {
            type: 'raster',
            tiles: [
                "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
                "https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
                "https://c.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
                "https://d.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png"
            ]
        },

        'wikimedia': {
            type: 'raster',
            tiles: [
                "https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png"
            ]
        }
    },
    layers: [
        {
            id: 'voyager',
            source: 'voyager',
            type: 'raster',
            minzoom: 0,
            maxzoom: 22,
            layout: {
                visibility: 'visible'
            },
            metadata: {
                'mapbox:groups': 'background'
            }
        },
        {
            id: 'carto-light',
            source: 'carto-light',
            type: 'raster',
            minzoom: 0,
            maxzoom: 22,
            layout: {
                visibility: 'none'
            },
            metadata: {
                'mapbox:groups': 'background'
            }
        },
        {
            id: 'carto-dark',
            source: 'carto-dark',
            type: 'raster',
            minzoom: 0,
            maxzoom: 22,
            layout: {
                visibility: 'none'
            },
            metadata: {
                'mapbox:groups': 'background'
            }
        },
    ]
};
