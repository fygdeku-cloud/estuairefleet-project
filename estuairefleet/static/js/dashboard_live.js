document.addEventListener("DOMContentLoaded", () => {
  const dashboard = document.querySelector("[data-supervision-dashboard]");
  if (!dashboard) return;

  const mapElement = dashboard.querySelector("[data-supervision-map]");
  const markers = new Map();
  const map = mapElement && window.L ? L.map(mapElement).setView([3.8667, 11.5167], 12) : null;
  if (map) L.tileLayer?.("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "© OpenStreetMap contributors", maxZoom: 19 })?.addTo(map);
  let timer;
  let controller;
  let stopped = false;

  const setMetric = (name, value) => {
    dashboard.querySelectorAll(`[data-live-stat='${name}']`).forEach((element) => { element.textContent = value; });
  };
  const renderList = (selector, items, empty, render) => {
    const list = dashboard.querySelector(selector);
    if (!list) return;
    list.replaceChildren();
    if (!items.length) {
      const item = document.createElement("li");
      item.className = "py-3 text-sm text-slate-500";
      item.textContent = empty;
      list.append(item);
      return;
    }
    items.forEach((data) => list.append(render(data)));
  };
  const row = (label, detail, tone = "") => {
    const item = document.createElement("li");
    item.className = "flex items-start justify-between gap-3 rounded-2xl border border-slate-100 bg-slate-50 p-3";
    const content = document.createElement("div");
    const title = document.createElement("strong");
    title.className = "block text-sm text-slate-900";
    title.textContent = label;
    const text = document.createElement("span");
    text.className = "mt-1 block text-xs text-slate-500";
    text.textContent = detail;
    content.append(title, text);
    if (tone) {
      const badge = document.createElement("span");
      badge.className = "shrink-0 rounded-full bg-insam-50 px-2 py-1 text-[10px] font-bold text-insam-700";
      badge.textContent = tone;
      item.append(content, badge);
    } else item.append(content);
    return item;
  };
  const render = (payload) => {
    Object.entries(payload.statistics || {}).forEach(([key, value]) => setMetric(key, value));
    renderList("[data-live-alerts]", payload.alerts || [], "Aucune alerte ouverte.", (alert) => row(alert.route, `${alert.signal_count} signal(s) · ${alert.status}`, alert.priority ? "Prioritaire" : "Suivi"));
    renderList("[data-live-incidents]", payload.incidents || [], "Aucun incident ouvert.", (incident) => row(incident.type, `${incident.bus} · ${incident.status}`, incident.description));
    renderList("[data-live-routes]", payload.routes || [], "Aucun trajet actif.", (route) => row(route.name, `${route.buses} bus · ${route.signals} signal(s) actif(s)`));
    const stamp = dashboard.querySelector("[data-live-updated]");
    if (stamp) stamp.textContent = `Mis à jour à ${new Date(payload.generated_at).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })}`;
    if (!map) return;
    const activeIds = new Set();
    (payload.buses || []).forEach((bus) => {
      activeIds.add(bus.id);
      const point = [bus.position_lat, bus.position_lng];
      const marker = markers.get(bus.id) || L.marker(point).addTo(map);
      marker.setLatLng(point).bindTooltip(`${bus.plate_number} · ${bus.status}`);
      markers.set(bus.id, marker);
    });
    markers.forEach((marker, id) => { if (!activeIds.has(id)) { marker.remove(); markers.delete(id); } });
  };
  const renderUnavailable = () => {
    renderList("[data-live-alerts]", [], "Données momentanément indisponibles.", () => null);
    renderList("[data-live-incidents]", [], "Données momentanément indisponibles.", () => null);
    renderList("[data-live-routes]", [], "Données momentanément indisponibles.", () => null);
    const stamp = dashboard.querySelector("[data-live-updated]");
    if (stamp) stamp.textContent = "Actualisation indisponible";
  };
  const poll = async () => {
    if (stopped || document.hidden) return;
    controller?.abort();
    controller = new AbortController();
    try {
      const response = await fetch("/dashboard/live/", { credentials: "same-origin", signal: controller.signal });
      if (!response.ok) throw new Error("snapshot");
      render(await response.json());
    } catch (error) {
      if (error.name === "AbortError") return;
      const status = dashboard.querySelector("[data-live-error]");
      if (status) status.hidden = false;
      renderUnavailable();
    } finally {
      controller = undefined;
      if (!stopped && !document.hidden) timer = window.setTimeout(poll, 10000);
    }
  };
  document.addEventListener("visibilitychange", () => { if (!document.hidden) { map?.invalidateSize(); poll(); } else { window.clearTimeout(timer); controller?.abort(); } });
  window.addEventListener("pagehide", () => { stopped = true; window.clearTimeout(timer); controller?.abort(); }, { once: true });
  poll();
});
