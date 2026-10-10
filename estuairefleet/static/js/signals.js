document.addEventListener("DOMContentLoaded", () => {
  const button = document.querySelector("[data-locate]");
  const form = button?.closest("form");
  const status = document.querySelector("[data-location-status]");
  if (!button || !form || !status) return;

  button.addEventListener("click", (event) => {
    event.preventDefault();
    if (!navigator.geolocation) {
      status.textContent = "La géolocalisation n'est pas disponible sur cet appareil.";
      return;
    }
    button.disabled = true;
    status.textContent = "Localisation en cours…";
    navigator.geolocation.getCurrentPosition(
      (position) => {
        document.querySelector("#id_position_lat").value = position.coords.latitude.toFixed(6);
        document.querySelector("#id_position_lng").value = position.coords.longitude.toFixed(6);
        status.textContent = "Signal envoyé.";
        form.submit();
      },
      () => {
        button.disabled = false;
        status.textContent = "Autorisez la localisation pour envoyer votre signal.";
      },
      { enableHighAccuracy: true, timeout: 8000, maximumAge: 10000 },
    );
  });
});
