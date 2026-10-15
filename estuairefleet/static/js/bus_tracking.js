document.addEventListener("DOMContentLoaded", () => {
  const mapElement = document.querySelector("[data-bus-map]");
  const shareButton = document.querySelector("[data-share-bus-position]");
  const shareStatus = document.querySelector("[data-bus-share-status]");
  const degraded = document.querySelector("[data-bus-degraded]");
  const csrf = document.cookie.split(";").map((item) => item.trim()).find((item) => item.startsWith("csrftoken="))?.split("=")[1];
  let watchId;

  if (mapElement && window.L) {
    const map = L.map(mapElement).setView([3.8667, 11.5167], 12);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "© OpenStreetMap contributors", maxZoom: 19 }).addTo(map);
    const markers = new Map();
    const poll = async () => {
      try {
        const response = await fetch("/api/buses/positions/", { credentials: "same-origin" });
        if (!response.ok) throw new Error("polling");
        const payload = await response.json();
        for (const bus of payload) {
          if (bus.position_lat === null || bus.position_lng === null) continue;
          const point = [bus.position_lat, bus.position_lng];
          const marker = markers.get(bus.id) || L.marker(point).addTo(map);
          marker.setLatLng(point).bindTooltip(`${bus.plate_number} · ${bus.status}`);
          markers.set(bus.id, marker);
        }
        if (degraded) degraded.hidden = true;
        window.setTimeout(poll, 5000);
      } catch (error) {
        if (degraded) degraded.hidden = false;
        window.setTimeout(poll, 2000);
      }
    };
    poll();
  }

  if (shareButton) {
    shareButton.addEventListener("click", () => {
      if (!navigator.geolocation) { if (shareStatus) shareStatus.textContent = "La géolocalisation est indisponible."; return; }
      shareButton.disabled = true;
      const send = (position) => fetch("/api/buses/my-bus/position/", { method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json", "X-CSRFToken": csrf || "" }, body: JSON.stringify({ lat: position.coords.latitude, lng: position.coords.longitude }) }).then((response) => { if (!response.ok) throw new Error("position"); });
      navigator.geolocation.getCurrentPosition((position) => { send(position).then(() => { if (shareStatus) shareStatus.textContent = "Position partagée. Mise à jour en cours…"; watchId = navigator.geolocation.watchPosition((next) => send(next).catch(() => {}), () => {}, { enableHighAccuracy: true, maximumAge: 5000 }); }).catch(() => { if (shareStatus) shareStatus.textContent = "La position n’a pas pu être partagée."; shareButton.disabled = false; }); }, () => { if (shareStatus) shareStatus.textContent = "Autorisez la localisation pour continuer."; shareButton.disabled = false; }, { enableHighAccuracy: true, timeout: 8000, maximumAge: 5000 });
    });
  }
});
