document.addEventListener("DOMContentLoaded", () => {
  const element = document.querySelector("[data-signal-map]");
  if (!element || !window.L) return;

  const map = L.map(element).setView([3.8667, 11.5167], 12);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors",
    maxZoom: 19,
  }).addTo(map);
  const markers = new Map();
  let retryDelay = 1000;
  const pollDelay = navigator.connection?.saveData ? 10000 : 5000;
  const degraded = document.querySelector("[data-signal-degraded]");
  const status = document.querySelector("[data-signal-count]");
  let pollTimer;
  let controller;
  let stopped = false;
  let hasFittedBounds = false;
  const markerIcon = L.divIcon({
    className: "ef-signal-marker",
    html: '<span class="ef-signal-marker-dot" aria-hidden="true"></span>',
    iconSize: [26, 26],
    iconAnchor: [13, 13],
  });

  const schedulePoll = (delay) => {
    window.clearTimeout(pollTimer);
    if (!stopped && !document.hidden) pollTimer = window.setTimeout(poll, delay);
  };

  const poll = async () => {
    if (stopped || document.hidden) return;
    controller?.abort();
    controller = new AbortController();
    try {
      const response = await fetch("/api/signals/visible/", { credentials: "same-origin", signal: controller.signal });
      if (!response.ok) throw new Error("polling");
      const payload = await response.json();
      const activeIds = new Set();
      for (const signal of payload.signals || []) {
        activeIds.add(String(signal.id));
        const point = [signal.lat, signal.lng];
        const marker = markers.get(signal.id) || L.marker(point, { icon: markerIcon }).addTo(map);
        marker.setLatLng(point).bindTooltip(signal.student_label || "Signal actif");
        markers.set(signal.id, marker);
      }
      for (const [id, marker] of markers) {
        if (!activeIds.has(String(id))) {
          marker.remove?.();
          markers.delete(id);
        }
      }
      if (!hasFittedBounds && markers.size) {
        map.fitBounds([...markers.values()].map((marker) => marker.getLatLng()), { padding: [30, 30] });
        hasFittedBounds = true;
      }
      retryDelay = 1000;
      if (degraded) degraded.hidden = true;
      if (status) status.textContent = `${markers.size} signal${markers.size === 1 ? "" : "aux"} actif${markers.size === 1 ? "" : "s"}`;
      schedulePoll(pollDelay);
    } catch (error) {
      if (error.name === "AbortError") return;
      if (degraded) degraded.hidden = false;
      schedulePoll(retryDelay);
      retryDelay = Math.min(retryDelay * 2, 15000);
    } finally {
      controller = undefined;
    }
  };
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      window.clearTimeout(pollTimer);
      controller?.abort();
    } else {
      map.invalidateSize?.();
      poll();
    }
  });
  window.addEventListener("pagehide", () => {
    stopped = true;
    window.clearTimeout(pollTimer);
    controller?.abort();
  }, { once: true });
  poll();
});
