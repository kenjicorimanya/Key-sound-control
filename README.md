# Key-sound-control 🎧🔊

**Key-sound-control** es la solución definitiva para Windows para **enrutar y regular el audio de programas y pestañas web individuales** con total independencia.

Permite, por ejemplo, que una pestaña de **YouTube suene por los altavoces**, otra pestaña de **Twitch suene por los auriculares**, y las demás pestañas y programas continúen en la **salida predeterminada**.

---

## 📦 Componentes del Proyecto

### 1. 🪟 Aplicación de Escritorio (`Release/Key-sound-control.exe`)
* **Ejecutable sin instalación:** [`Release/Key-sound-control.exe`](./Release/Key-sound-control.exe)
* **Selector de salida para programas:** (`Alt + A` o botón de ratón). Enruta programas completos (Juegos, Spotify, Discord, reproductores, etc.) al dispositivo deseado.
* **Mezclador de volumen flotante:** (`Alt + V` o botón de ratón). Controla volúmenes maestros y de apps con la rueda del ratón y silencia con un clic.
* **Soporte para botones extra de ratón (Mouse 4/5) y macros.**

---

### 2. 🌐 Mini Extensión para el Navegador (`Extension-Chrome/`)
* **Ubicación:** Carpeta [`Extension-Chrome/`](./Extension-Chrome)
* **Compatibilidad:** Google Chrome, Microsoft Edge, Brave, Opera.
* **Propósito:** Control **pestaña por pestaña**. Permite redirigir el audio de cualquier pestaña individual (YouTube, Spotify Web, Twitch, Meet) a una salida de audio diferente mediante la API nativa de Chromium (`setSinkId`).
* **Atajo en el navegador:** `Alt + Shift + A`

#### Cómo instalar la extensión en 1 minuto:
1. Abre `chrome://extensions/` (o `edge://extensions/`).
2. Activa el **"Modo de desarrollador"** (arriba a la derecha).
3. Haz clic en **"Cargar descomprimida"**.
4. Selecciona la carpeta **`Extension-Chrome`**.
5. ¡Listo! Al abrir cualquier video de YouTube o música, pulsa `Alt + Shift + A` o haz clic en el icono para asignarle su propio altavoz o auricular.

---

## 📄 Licencia
Desarrollado bajo licencia MIT.
