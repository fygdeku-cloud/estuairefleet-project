let deferredInstallPrompt;

const setOfflineState = () => {
  const status = document.querySelector("[data-offline-status]");
  if (status) status.classList.toggle("hidden", navigator.onLine);
};

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  deferredInstallPrompt = event;
  const panel = document.querySelector("[data-pwa-install]");
  if (panel) panel.hidden = false;
});

window.addEventListener("appinstalled", () => {
  deferredInstallPrompt = undefined;
  const panel = document.querySelector("[data-pwa-install]");
  if (panel) panel.hidden = true;
});

window.addEventListener("online", setOfflineState);
window.addEventListener("offline", setOfflineState);

window.addEventListener("load", () => {
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
});

document.addEventListener("DOMContentLoaded", () => {
  setOfflineState();

  document.querySelector("[data-pwa-install-action]")?.addEventListener("click", async () => {
    if (!deferredInstallPrompt) return;
    deferredInstallPrompt.prompt();
    await deferredInstallPrompt.userChoice;
    deferredInstallPrompt = undefined;
    const panel = document.querySelector("[data-pwa-install]");
    if (panel) panel.hidden = true;
  });
  document.querySelector("[data-pwa-dismiss]")?.addEventListener("click", () => {
    const panel = document.querySelector("[data-pwa-install]");
    if (panel) panel.hidden = true;
  });

  if (!window.initFlowbite) {
    document.querySelectorAll("[data-collapse-toggle]").forEach((toggle) => {
      toggle.addEventListener("click", () => {
        const target = document.getElementById(toggle.dataset.collapseToggle);
        if (!target) return;
        target.classList.toggle("hidden");
        toggle.setAttribute("aria-expanded", String(!target.classList.contains("hidden")));
      });
    });
    document.querySelectorAll("[data-dismiss-target]").forEach((dismiss) => {
      dismiss.addEventListener("click", () => document.querySelector(dismiss.dataset.dismissTarget)?.remove());
    });
  }

  document.querySelectorAll("[data-toggle='password']").forEach((toggle) => {
    toggle.addEventListener("click", () => {
      const target = document.getElementById(toggle.dataset.target);
      if (!target) return;

      const isHidden = target.type === "password";
      target.type = isHidden ? "text" : "password";
      toggle.textContent = isHidden ? "Masquer" : "Afficher";
      toggle.setAttribute("aria-pressed", String(isHidden));
    });
  });

  const locateButton = document.querySelector("[data-locate]");
  if (locateButton) {
    const status = document.querySelector("[data-location-status]");
    locateButton.addEventListener("click", () => {
    if (!navigator.geolocation) {
      if (status) status.textContent = "La géolocalisation n’est pas disponible sur cet appareil.";
      return;
    }

    locateButton.disabled = true;
    if (status) status.textContent = "Localisation en cours…";
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const latitude = document.querySelector("[name='position_lat']");
        const longitude = document.querySelector("[name='position_lng']");
        if (latitude) latitude.value = position.coords.latitude;
        if (longitude) longitude.value = position.coords.longitude;
        if (status) status.textContent = "Position prête. Vous pouvez confirmer le signal.";
        locateButton.disabled = false;
      },
      () => {
        if (status) status.textContent = "Autorisez la localisation pour émettre votre signal.";
        locateButton.disabled = false;
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 },
    );
    });
  }
});
