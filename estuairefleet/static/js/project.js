document.addEventListener("DOMContentLoaded", () => {
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
  if (!locateButton) return;

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
});
