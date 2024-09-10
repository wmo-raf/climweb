function ZoomToLocationsControl(zoomLocations) {
    this.zoomLocations = zoomLocations;
}

ZoomToLocationsControl.prototype.onAdd = function (map) {
    this._map = map;
    this._container = document.createElement('div');
    this._container.className = 'maplibregl-ctrl';


    if (!this.zoomLocations || this.zoomLocations.length === 0) {
        this._container.removeAttribute("class");
        return this._container;
    }

    this._wrapper = null;
    this._container.appendChild(this._createButton());
    this._select = this._createSelect();

    return this._container;
};

ZoomToLocationsControl.prototype.onRemove = function () {
    this._container.parentNode.removeChild(this._container);
    this._map = undefined;
}


ZoomToLocationsControl.prototype._createButton = function () {
    const wrapper = document.createElement('div');
    wrapper.className = 'maplibregl-ctrl-group';
    this._wrapper = wrapper;

    const buttonEl = document.createElement('button')
    buttonEl.className = 'maplibregl-ctrl-zoom-to-locations';
    buttonEl.title = 'Zoom to a location';
    this._wrapper.appendChild(buttonEl);


    const iconEl = document.createElement('span');
    iconEl.className = 'maplibregl-ctrl-icon mapboxgl-ctrl-icon';
    buttonEl.appendChild(iconEl);

    buttonEl.addEventListener('click', (e) => {
        this._wrapper.appendChild(this._select);
        buttonEl.style.display = 'none';
        e.stopPropagation()
    }, false)


    return wrapper;
}


ZoomToLocationsControl.prototype._createSelect = function () {
    const select = document.createElement('select');
    select.className = 'select is-small';

    const defaultZoomLocation = this.zoomLocations.find(loc => loc.default)
    const options = this.zoomLocations.map((location, i) => {
        return `<option value="${location.bounds}"  ${defaultZoomLocation.name === location.name ? "selected" : ""} >${location.name}</option>`
    });


    // add empty option
    options.unshift('<option value="">Select a location</option>');

    select.innerHTML = options.join('');

    select.addEventListener('change', (e) => {
        const bounds = e.target.value.split(',').map(parseFloat);

        if (!bounds || bounds.length !== 4) {
            return;
        }


        this._map.fitBounds(bounds, {
            padding: 20
        });
        this._wrapper.removeChild(select);
        this._wrapper.firstChild.style.display = 'block';
    })

    //on click outside
    document.addEventListener('click', (e) => {
        if (e.target !== select) {
            // check if select is still in the dom
            if (this._wrapper.contains(select)) {
                this._wrapper.removeChild(select);
                this._wrapper.firstChild.style.display = 'block';
            }
        }
    })

    return select;
}
