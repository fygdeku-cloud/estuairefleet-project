document.addEventListener("DOMContentLoaded", () => {
  const element = document.querySelector("[data-signal-map]");
  if (!element || !window.L) return;

  const map = L.map(element).setView([3.8667, 11.5167], 12);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors",
    maxZoom: 19,
  }).addTo(map);
  const markers = new Map();
  let since = null;
  let retryDelay = 1000;
  const degraded = document.querySelector("[data-signal-degraded]");
  const status = document.querySelector("[data-signal-count]");
  const markerIcon = L.divIcon({
    className: "ef-signal-marker",
    html: '<span class="ef-signal-marker-dot" aria-hidden="true"></span>',
    iconSize: [26, 26],
    iconAnchor: [13, 13],
  });

  const poll = async () => {
    const query = since ? `?since=${encodeURIComponent(since)}` : "";
    try {
      const response = await fetch(`/api/signals/visible/${query}`, { credentials: "same-origin" });
      if (!response.ok) throw new Error("polling");
      const payload = await response.json();
      for (const signal of payload.signals || []) {
        const point = [signal.lat, signal.lng];
        const marker = markers.get(signal.id) || L.marker(point, { icon: markerIcon }).addTo(map);
        marker.setLatLng(point).bindTooltip(signal.student_label || "Signal actif");
        markers.set(signal.id, marker);
      }
      if (!since && markers.size) {
        map.fitBounds([...markers.values()].map((marker) => marker.getLatLng()), { padding: [30, 30] });
      }
      since = payload.server_time;
      retryDelay = 1000;
      if (degraded) degraded.hidden = true;
      if (status) status.textContent = `${markers.size} signal${markers.size === 1 ? "" : "aux"} actif${markers.size === 1 ? "" : "s"}`;
      window.setTimeout(poll, 5000);
    } catch (error) {
      if (degraded) degraded.hidden = false;
      window.setTimeout(poll, retryDelay);
      retryDelay = Math.min(retryDelay * 2, 15000);
    }
  };
  poll();
});
