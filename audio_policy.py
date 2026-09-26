import ctypes
from ctypes import wintypes, c_void_p, POINTER, byref, Structure, c_ulong, c_ushort, c_ubyte, c_uint, WINFUNCTYPE, cast
import uuid
import logging

logger = logging.getLogger("AudioPolicy")

# Windows COM / WinRT base definitions
combase = ctypes.windll.combase

class GUID(Structure):
    _fields_ = [
        ('Data1', c_ulong),
        ('Data2', c_ushort),
        ('Data3', c_ushort),
        ('Data4', c_ubyte * 8)
    ]

def string_to_guid(guid_str: str) -> GUID:
    u = uuid.UUID(guid_str)
    g = GUID()
    g.Data1 = u.time_low
    g.Data2 = u.time_mid
    g.Data3 = u.time_hi_version
    for i, b in enumerate(u.bytes[8:]):
        g.Data4[i] = b
    return g

# WinRT APIs
RoInitialize = combase.RoInitialize
RoInitialize.argtypes = [wintypes.UINT]
RoInitialize.restype = wintypes.HRESULT

WindowsCreateString = combase.WindowsCreateString
WindowsCreateString.argtypes = [wintypes.LPCWSTR, wintypes.UINT, POINTER(c_void_p)]
WindowsCreateString.restype = wintypes.HRESULT

WindowsDeleteString = combase.WindowsDeleteString
WindowsDeleteString.argtypes = [c_void_p]
WindowsDeleteString.restype = wintypes.HRESULT

WindowsGetStringRawBuffer = combase.WindowsGetStringRawBuffer
WindowsGetStringRawBuffer.argtypes = [c_void_p, POINTER(wintypes.UINT)]
WindowsGetStringRawBuffer.restype = wintypes.LPCWSTR

RoGetActivationFactory = combase.RoGetActivationFactory
RoGetActivationFactory.argtypes = [c_void_p, POINTER(GUID), POINTER(c_void_p)]
RoGetActivationFactory.restype = wintypes.HRESULT

# Constants for MMDevice endpoints
DEVINTERFACE_AUDIO_RENDER = "#{e6327cad-dcec-4949-ae8a-991e976a79d2}"
DEVINTERFACE_AUDIO_CAPTURE = "#{2eef81be-33fa-4800-9670-1cd474972c3f}"
MMDEVAPI_TOKEN = r"\\?\SWD#MMDEVAPI#"

IID_21H2 = "ab3d4648-e242-459f-b02f-541c70306324"
IID_DOWNLEVEL = "2a59116d-6c4f-45e0-a74f-707e3fef9258"

class AudioPolicyService:
    def __init__(self):
        self._initialized = False
        self._factory_ptr = None
        self._set_persisted_func = None
        self._get_persisted_func = None
        self._clear_all_func = None
        self._init_factory()

    def _init_factory(self):
        try:
            # RO_INIT_MULTITHREADED = 1
            RoInitialize(1)
        except Exception:
            pass

        h_class = c_void_p()
        class_name = "Windows.Media.Internal.AudioPolicyConfig"
        hr = WindowsCreateString(class_name, len(class_name), byref(h_class))
        if hr != 0:
            logger.error(f"Error WindowsCreateString: {hex(hr & 0xffffffff)}")
            return

        factory_ptr = c_void_p()
        guid_21h2 = string_to_guid(IID_21H2)
        hr = RoGetActivationFactory(h_class, byref(guid_21h2), byref(factory_ptr))

        if hr != 0 or not factory_ptr.value:
            guid_dl = string_to_guid(IID_DOWNLEVEL)
            hr = RoGetActivationFactory(h_class, byref(guid_dl), byref(factory_ptr))

        WindowsDeleteString(h_class)

        if hr == 0 and factory_ptr.value:
            self._factory_ptr = factory_ptr
            vtable = cast(factory_ptr, POINTER(POINTER(c_void_p))).contents

            # Method 25: SetPersistedDefaultAudioEndpoint(this, uint pid, uint flow, uint role, HSTRING dev_id)
            self._set_persisted_func = WINFUNCTYPE(
                wintypes.HRESULT, c_void_p, c_uint, c_uint, c_uint, c_void_p
            )(vtable[25])

            # Method 26: GetPersistedDefaultAudioEndpoint(this, uint pid, uint flow, uint role, POINTER(HSTRING))
            self._get_persisted_func = WINFUNCTYPE(
                wintypes.HRESULT, c_void_p, c_uint, c_uint, c_uint, POINTER(c_void_p)
            )(vtable[26])

            # Method 27: ClearAllPersistedApplicationDefaultEndpoints(this)
            self._clear_all_func = WINFUNCTYPE(
                wintypes.HRESULT, c_void_p
            )(vtable[27])

            self._initialized = True
            logger.info("AudioPolicyService factory successfully initialized.")
        else:
            logger.error(f"Failed to activate AudioPolicyConfig factory: {hex(hr & 0xffffffff)}")

    def _format_device_id(self, raw_id: str) -> str:
        """Adds Windows MMDEVAPI prefix and suffix if not present."""
        if not raw_id:
            return ""
        if raw_id.startswith(MMDEVAPI_TOKEN):
            return raw_id
        return f"{MMDEVAPI_TOKEN}{raw_id}{DEVINTERFACE_AUDIO_RENDER}"

    def _clean_device_id(self, full_id: str) -> str:
        """Removes prefix and suffix to return raw endpoint GUID string."""
        if not full_id:
            return ""
        res = full_id
        if res.startswith(MMDEVAPI_TOKEN):
            res = res[len(MMDEVAPI_TOKEN):]
        if res.endswith(DEVINTERFACE_AUDIO_RENDER):
            res = res[:-len(DEVINTERFACE_AUDIO_RENDER)]
        elif res.endswith(DEVINTERFACE_AUDIO_CAPTURE):
            res = res[:-len(DEVINTERFACE_AUDIO_CAPTURE)]
        return res

    def set_app_audio_device(self, process_id: int, device_id: str | None) -> bool:
        """
        Routes the specified process to a specific audio endpoint.
        If device_id is None or empty, resets the process to the Windows default device.
        """
        if not self._initialized or not self._set_persisted_func:
            self._init_factory()
            if not self._initialized:
                return False

        h_dev = c_void_p(0)
        if device_id:
            full_dev_id = self._format_device_id(device_id)
            hr = WindowsCreateString(full_dev_id, len(full_dev_id), byref(h_dev))
            if hr != 0:
                logger.error(f"Error creating device HSTRING: {hex(hr & 0xffffffff)}")
                return False

        try:
            # Roles: 0 = eConsole (games/apps), 1 = eMultimedia (music/video)
            hr1 = self._set_persisted_func(self._factory_ptr, process_id, 0, 1, h_dev)
            hr2 = self._set_persisted_func(self._factory_ptr, process_id, 0, 0, h_dev)
            success = (hr1 == 0 and hr2 == 0)
            if not success:
                logger.warning(f"set_app_audio_device returned HR1={hex(hr1 & 0xffffffff)}, HR2={hex(hr2 & 0xffffffff)}")
            return success
        except Exception as e:
            logger.error(f"Exception in set_app_audio_device: {e}")
            return False
        finally:
            if h_dev.value:
                WindowsDeleteString(h_dev)

    def get_app_audio_device(self, process_id: int) -> str | None:
        """
        Returns the raw device ID assigned to the given process, or None if using default.
        """
        if not self._initialized or not self._get_persisted_func:
            self._init_factory()
            if not self._initialized:
                return None

        out_str = c_void_p(0)
        try:
            # Check eMultimedia first
            hr = self._get_persisted_func(self._factory_ptr, process_id, 0, 1, byref(out_str))
            if hr == 0 and out_str.value:
                length = wintypes.UINT()
                buf = WindowsGetStringRawBuffer(out_str, byref(length))
                WindowsDeleteString(out_str)
                if buf:
                    return self._clean_device_id(buf)
        except Exception as e:
            logger.error(f"Exception in get_app_audio_device: {e}")
        return None

    def clear_all_custom_routes(self) -> bool:
        """Clears all custom per-app audio routing in Windows."""
        if not self._initialized or not self._clear_all_func:
            return False
        try:
            hr = self._clear_all_func(self._factory_ptr)
            return hr == 0
        except Exception as e:
            logger.error(f"Exception in clear_all_custom_routes: {e}")
            return False
