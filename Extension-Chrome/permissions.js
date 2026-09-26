document.addEventListener('DOMContentLoaded', () => {
  const btnAllow = document.getElementById('btnAllow');
  const statusEl = document.getElementById('status');

  async function askPermission() {
    statusEl.textContent = 'Por favor, presiona "Permitir" en el aviso de Chrome arriba a la izquierda...';
    statusEl.style.color = '#e0af68';
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop());
      statusEl.textContent = '✓ ¡Permiso concedido exitosamente! Cerrando pestaña...';
      statusEl.style.color = '#9ece6a';
      btnAllow.style.display = 'none';
      setTimeout(() => {
        window.close();
      }, 1000);
    } catch (err) {
      statusEl.textContent = 'Debes presionar "Permitir" para que Chrome muestre los nombres de tus dispositivos.';
      statusEl.style.color = '#f7768e';
    }
  }

  btnAllow.addEventListener('click', askPermission);
  // Also try immediately
  askPermission();
});
