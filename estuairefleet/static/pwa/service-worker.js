const CACHE_NAME = "estuairefleet-shell-v1";
const APP_SHELL = [
  "/",
  "/static/pwa/manifest.json",
  "/static/pwa/offline.html",
  "/static/pwa/icons/icon-192.svg",
  "/static/pwa/icons/icon-512.svg",
  "/static/css/tailwind.css",
  "/static/css/design-system.css",
  "/static/css/domains/alerts.css",
  "/static/css/domains/intercampus.css",
  "/static/css/domains/notifications.css",
  "/static/js/project.js",
  "/static/js/signal_map.js",
  "/static/js/signals.js",
  "/static/js/bus_tracking.js",
  "/static/images/favicons/favicon.ico",
  "/static/vendor/leaflet/leaflet.css",
  "/static/vendor/leaflet/leaflet.js"
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin) return;

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(() => caches.match(request).then((cached) => cached || caches.match("/static/pwa/offline.html"))),
    );
    return;
  }

  if (url.pathname.startsWith("/static/")) {
    event.respondWith(caches.match(request).then((cached) => cached || fetch(request)));
  }
});
