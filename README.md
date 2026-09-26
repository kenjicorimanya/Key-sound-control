# Key-sound-control 🎧🔊

**Key-sound-control** es una aplicación moderna y ultraligera para Windows diseñada para ejecutarse en segundo plano en la bandeja del sistema (System Tray), permitiéndote **enrutar y regular el audio de programas y ventanas individuales** con la máxima comodidad.

---

## 🚀 Características Principales

### 1. 🔀 Selector Rápido de Salida (Router HUD)
* **Atajo por defecto:** `Alt + A` *(o el botón de tu ratón que elijas)*.
* Detecta al instante la ventana o programa en el que estés trabajando (ej. una ventana de Google Chrome con música o video).
* Despliega un menú flotante estilo Windows 11 junto a tu ratón:
  * Elige la salida de audio deseada (**Altavoces**, **Auriculares**, **Monitor HDMI**, etc.) con un solo clic o con teclas numéricas (`1`, `2`, `3`...).
  * El audio de esa app se redirige de inmediato a ese dispositivo sin reiniciar la aplicación ni afectar al resto del sistema.
  * Presiona `0` para volver a la salida de audio predeterminada de Windows.

### 2. 🎚️ Mezclador de Volumen Flotante (Mixer HUD)
* **Atajo por defecto:** `Alt + V` *(o el botón lateral de tu ratón que elijas)*.
* Abre un mezclador moderno y compacto en la posición de tu cursor:
  * **Dispositivos de Salida:** Controla el volumen maestro de todos tus altavoces y auriculares conectados.
  * **Aplicaciones Activas:** Controla el volumen individual de cada programa que esté emitiendo sonido (Chrome, Spotify, Discord, Juegos, etc.).
  * **Control con la Rueda del Ratón:** Posas el cursor sobre cualquier barra y con la rueda del ratón subes o bajas el volumen con precisión milimétrica.
  * **Botón de Silencio Instantáneo (Mute):** Clic en el icono para mutear o desmutear en 1 segundo.

### 3. 🖱️ Compatibilidad Total con Ratones Gaming y Macros
* Soporta **botones extra del ratón** (`XButton 1 / Mouse 4`, `XButton 2 / Mouse 5`, `Middle Click`).
* Soporta cualquier combinación de teclado (`Ctrl`, `Alt`, `Shift`, `Win`, teclas de función `F1-F24`).
* **Grabador interactivo en Configuración:** Simplemente haz clic en "Grabar" y presiona la tecla o botón del ratón que quieras asignar.

### 4. 🪶 Segundo Plano Ultraligero
* Icono elegante en la bandeja del sistema (al lado del reloj de Windows).
* Cierre automático de los menús al presionar `Esc` o hacer clic fuera.
* Opción de arranque automático con Windows.

---

## 🛠️ Instalación y Uso

### Requisitos
* Windows 10 (versión 1803 o superior) o Windows 11.
* Python 3.10 o superior.

### Dependencias
Instala los módulos necesarios con:
```bash
pip install -r requirements.txt
```

### Iniciar la aplicación
* **Con consola para ver registros:** Ejecuta `INICIAR.bat`
* **Silencioso en segundo plano:** Ejecuta `INICIAR_SILENCIOSO.vbs`

---

## 📂 Estructura del Proyecto

* **`audio_policy.py`**: Interfaz de bajo nivel con Windows Core Audio (`Windows.Media.Internal.AudioPolicyConfig` / WinRT COM) para enrutamiento por proceso (`PID`).
* **`audio_manager.py`**: Gestión de dispositivos de salida, sesiones de audio, volúmenes, mute y detección de ventana activa.
* **`input_listener.py`**: Escucha global de atajos de teclado y botones especiales del ratón.
* **`router_hud.py`**: Interfaz flotante de selección de salida de sonido para la ventana enfocada.
* **`mixer_hud.py`**: Interfaz flotante del mezclador de volúmenes con soporte de rueda del ratón.
* **`settings_gui.py`**: Panel de ajustes para personalizar atajos, botones del ratón y preferencias.
* **`main.py`**: Punto de entrada con icono de bandeja del sistema (System Tray).

---

## 📄 Licencia
Desarrollado bajo licencia MIT.
