/* Local Leaflet-compatible facade used when the full vendor bundle is unavailable. */
(() => {
  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
  const project = (map, point) => {
    const [lat, lng] = point;
    const x = 50 + ((Number(lng) - map._center[1]) / map._spanLng) * 100;
    const y = 50 - ((Number(lat) - map._center[0]) / map._spanLat) * 100;
    return { left: `${clamp(x, 4, 96)}%`, top: `${clamp(y, 7, 93)}%` };
  };
  const redraw = (map) => map._markers.forEach((marker) => marker._render());
  const createMap = (element) => {
    element.classList.add("leaflet-container");
    const surface = document.createElement("div");
    surface.className = "ef-local-map-surface";
    const grid = document.createElement("div");
    grid.className = "ef-local-map-grid";
    const markerPane = document.createElement("div");
    markerPane.className = "ef-local-map-markers";
    element.replaceChildren(surface, grid, markerPane);
    return {
      _element: element,
      _markerPane: markerPane,
      _markers: new Set(),
      _center: [3.8667, 11.5167],
      _spanLat: 0.08,
      _spanLng: 0.10,
      setView(center) { this._center = center.map(Number); redraw(this); return this; },
      invalidateSize() { redraw(this); return this; },
      fitBounds(bounds) {
        if (!bounds?.length) return this;
        const lats = bounds.map((point) => Number(point.lat ?? point[0]));
        const lngs = bounds.map((point) => Number(point.lng ?? point[1]));
        this._center = [(Math.min(...lats) + Math.max(...lats)) / 2, (Math.min(...lngs) + Math.max(...lngs)) / 2];
        this._spanLat = Math.max(0.015, (Math.max(...lats) - Math.min(...lats)) * 1.8);
        this._spanLng = Math.max(0.02, (Math.max(...lngs) - Math.min(...lngs)) * 1.8);
        redraw(this);
        return this;
      },
      _addAttribution(text) {
        if (!text || this._element.querySelector(".leaflet-control-attribution")) return;
        const attribution = document.createElement("small");
        attribution.className = "leaflet-control-attribution";
        attribution.textContent = text;
        this._element.append(attribution);
      },
    };
  };
  const createMarker = (point, options = {}) => {
    const icon = options.icon || {};
    return {
      _point: point.map(Number),
      _map: null,
      _element: null,
      addTo(map) {
        this._map = map;
        this._element = document.createElement("div");
        this._element.className = icon.className || "ef-map-bus-marker";
        this._element.innerHTML = icon.html || "<span aria-hidden=\"true\">●</span>";
        this._element.setAttribute("role", "img");
        map._markerPane.append(this._element);
        map._markers.add(this);
        this._render();
        return this;
      },
      _render() {
        if (!this._map || !this._element) return;
        Object.assign(this._element.style, project(this._map, this._point));
      },
      setLatLng(next) { this._point = next.map(Number); this._render(); return this; },
      getLatLng() { return { lat: this._point[0], lng: this._point[1] }; },
      bindTooltip(text) { if (this._element) this._element.title = text || ""; return this; },
      bindPopup(text) { return this.bindTooltip(text); },
      remove() { this._map?._markers.delete(this); this._element?.remove(); return this; },
    };
  };
  window.L = window.L || {
    divIcon: (options) => options,
    map: createMap,
    marker: createMarker,
    tileLayer: (_url, options = {}) => ({ addTo(map) { map._addAttribution(options.attribution || "Carte locale"); return this; } }),
  };
})();
