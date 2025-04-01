export const getRasterLayerConfig = (layer) => {
    const {layerConfig, id} = layer
    const tileUrl = layerConfig.source.tiles[0].replace("{geostore_id}", "")

    return {
        source: {
            "id": id,
            "type": "raster",
            "tiles": [tileUrl]
        },
        layer: {
            "id": id,
            "type": "raster",
        }
    }
}


export const updateTileUrl = (tileUrl, params) => {
    // construct new url with new query params
    const url = new URL(tileUrl)
    const qs = new URLSearchParams(url.search);
    Object.keys(params).forEach(key => {
        qs.set(key, params[key])
    })
    url.search = decodeURIComponent(qs);
    return decodeURIComponent(url.href)
}

export const updateSourceTileUrl = (map, sourceId, params) => {
    // Get the source object from the map using the specified source ID.
    const source = map.getSource(sourceId);
    if (source && source.tiles) {
        const sourceTileUrl = source.tiles[0]
        const newTileUrl = updateTileUrl(sourceTileUrl, params)

        // Replace the source's tile URL with the updated URL.
        map.getSource(sourceId).tiles = [newTileUrl];

        // Remove the tiles for the updated source from the map cache.
        map.style.sourceCaches[sourceId].clearTiles();

        // Load the new tiles for the updated source within the current viewport.
        map.style.sourceCaches[sourceId].update(map.transform);

        // Trigger a repaint of the map to display the updated tiles.
        map.triggerRepaint();
    }
}

