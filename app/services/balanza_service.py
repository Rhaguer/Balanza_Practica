import logging
import platform
import re
import threading
import time
from decimal import Decimal, InvalidOperation

from django.conf import settings


logger = logging.getLogger(__name__)


DEFAULT_SERIAL_BAUDRATES = (9600, 4800, 2400, 1200, 19200, 38400, 57600, 115200)
DEFAULT_SERIAL_MODES = ("8N1", "7E1", "8E1", "7N1", "8N2")
DEFAULT_LINE_CONTROLS = ("default", "rts", "dtr_rts", "none")
DEFAULT_POLL_COMMANDS = ("", "S\r\n", "W\r\n", "P\r\n", "SI\r\n", "Q\r\n", "PRINT\r\n")
BALANZA_KEYWORDS = (
    "scale", "balance", "weight", "peso", "balanza", "usb serial", "serial",
    "rs232", "ch340", "ch341", "cp210", "prolific", "pl2303", "ftdi",
)

_read_lock = threading.Lock()


def _setting_list(name, default=()):
    value = getattr(settings, name, default)
    if value in (None, ""):
        return tuple(default)
    if isinstance(value, str):
        return tuple(item.strip() for item in value.split(",") if item.strip())
    return tuple(str(item).strip() for item in value if str(item).strip())


def _setting_int(name, default, minimum=0):
    try:
        value = int(getattr(settings, name, default))
    except (TypeError, ValueError):
        value = default
    return max(value, minimum)


def _setting_decimal(name, default):
    try:
        return Decimal(str(getattr(settings, name, default)))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(str(default))


def _serial_baudrates():
    values = []
    for raw in _setting_list("BALANZA_SERIAL_BAUDRATES", DEFAULT_SERIAL_BAUDRATES):
        try:
            value = int(raw)
        except (TypeError, ValueError):
            continue
        if value > 0 and value not in values:
            values.append(value)
    return tuple(values or DEFAULT_SERIAL_BAUDRATES)


def _serial_modes():
    values = []
    for raw in _setting_list("BALANZA_SERIAL_MODES", DEFAULT_SERIAL_MODES):
        mode = raw.upper()
        if re.fullmatch(r"[78][NOE][12]", mode) and mode not in values:
            values.append(mode)
    return tuple(values or DEFAULT_SERIAL_MODES)


def _line_controls():
    aliases = {
        "default": "default",
        "rts": "rts",
        "dtrrts": "dtr_rts",
        "dtr_rts": "dtr_rts",
        "dtr-rts": "dtr_rts",
        "none": "none",
        "off": "none",
    }
    values = []
    for raw in _setting_list("BALANZA_LINE_CONTROLS", DEFAULT_LINE_CONTROLS):
        value = aliases.get(raw.lower())
        if value and value not in values:
            values.append(value)
    return tuple(values or DEFAULT_LINE_CONTROLS)


def _poll_commands():
    commands = []
    for raw in _setting_list("BALANZA_POLL_COMMANDS", DEFAULT_POLL_COMMANDS):
        commands.append(raw.replace("\\r", "\r").replace("\\n", "\n").replace("\\t", "\t"))
    return tuple(commands or DEFAULT_POLL_COMMANDS)


def _configured_serial_ports():
    return tuple(port.upper() for port in _setting_list("BALANZA_SERIAL_PORTS") if port)


def _max_weight_kg():
    return _setting_decimal("MAX_WEIGHT_KG", "1000")


def _is_probable_scale(*values):
    text = " ".join(str(value or "") for value in values).lower()
    return any(keyword in text for keyword in BALANZA_KEYWORDS)


def _serial_modules():
    try:
        import serial
        from serial.tools import list_ports

        return serial, list_ports, None
    except Exception as exc:
        return None, None, f"pyserial no disponible: {exc}"


def _hid_module():
    try:
        import hid

        return hid, None
    except Exception as exc:
        return None, f"hidapi no disponible: {exc}"


def _usb_modules():
    try:
        import usb.core
        import usb.util

        backend = None
        try:
            import libusb_package

            backend = libusb_package.get_libusb1_backend()
        except Exception as exc:
            logger.debug("No se pudo cargar el backend libusb empaquetado: %s", exc)
        return usb.core, usb.util, backend, None
    except Exception as exc:
        return None, None, None, f"pyusb no disponible: {exc}"


def _visible_text(raw):
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw
    return bytes(raw).decode("ascii", errors="ignore")


def _error_resultado(mensaje, codigo="error", accion="", errores=None, **extra):
    payload = {
        "ok": False,
        "peso": None,
        "unidad": None,
        "puerto": None,
        "baudrate": None,
        "serial_mode": None,
        "line_control": None,
        "codigo": codigo,
        "mensaje": mensaje,
        "accion": accion,
        "errores": errores or [],
    }
    payload.update(extra)
    return payload


def _usb_string(usb_util, device, index):
    if not index:
        return ""
    try:
        return usb_util.get_string(device, index) or ""
    except Exception:
        return ""


def listar_dispositivos_balanza():
    dispositivos = {"serial": [], "hid": [], "usb": [], "errores": []}
    configured = _configured_serial_ports()
    seen = set()

    _, list_ports, serial_error = _serial_modules()
    if serial_error:
        dispositivos["errores"].append(serial_error)
    else:
        for port in list_ports.comports():
            name = str(port.device or "").upper()
            seen.add(name)
            dispositivos["serial"].append({
                "puerto": port.device,
                "descripcion": port.description or "",
                "fabricante": port.manufacturer or "",
                "hwid": port.hwid or "",
                "configurado": name in configured,
                "probable_balanza": _is_probable_scale(
                    port.device, port.description, port.manufacturer, port.hwid
                ),
            })

    for name in configured:
        if name not in seen:
            dispositivos["serial"].append({
                "puerto": name,
                "descripcion": "Puerto configurado manualmente",
                "fabricante": "",
                "hwid": "",
                "configurado": True,
                "probable_balanza": True,
            })

    hid, hid_error = _hid_module()
    if hid_error:
        dispositivos["errores"].append(hid_error)
    else:
        try:
            for device in hid.enumerate():
                manufacturer = device.get("manufacturer_string") or ""
                product = device.get("product_string") or ""
                dispositivos["hid"].append({
                    "path": device.get("path"),
                    "fabricante": manufacturer,
                    "producto": product,
                    "vendor_id": device.get("vendor_id"),
                    "product_id": device.get("product_id"),
                    "probable_balanza": _is_probable_scale(manufacturer, product),
                })
        except Exception as exc:
            dispositivos["errores"].append(f"No se pudo enumerar HID: {exc}")

    usb_core, usb_util, usb_backend, usb_error = _usb_modules()
    if usb_error:
        dispositivos["errores"].append(usb_error)
    else:
        try:
            for device in usb_core.find(find_all=True, backend=usb_backend) or []:
                manufacturer = _usb_string(usb_util, device, getattr(device, "iManufacturer", 0))
                product = _usb_string(usb_util, device, getattr(device, "iProduct", 0))
                dispositivos["usb"].append({
                    "vendor_id": getattr(device, "idVendor", None),
                    "product_id": getattr(device, "idProduct", None),
                    "fabricante": manufacturer,
                    "producto": product,
                    "probable_balanza": _is_probable_scale(manufacturer, product),
                })
        except Exception as exc:
            dispositivos["errores"].append(f"No se pudo enumerar USB: {exc}")

    return dispositivos


def diagnostico_balanza():
    return {
        "ok": True,
        "plataforma": platform.platform(),
        "configuracion": {
            "serial_ports": list(_configured_serial_ports()),
            "baudrates": list(_serial_baudrates()),
            "serial_modes": list(_serial_modes()),
            "line_controls": list(_line_controls()),
            "probe_seconds": _setting_int("BALANZA_PROBE_SECONDS", 2, 1),
            "scan_timeout_seconds": _setting_int("BALANZA_SCAN_TIMEOUT_SECONDS", 20, 1),
            "stable_samples": _setting_int("BALANZA_STABLE_SAMPLES", 3, 1),
            "stable_tolerance_kg": str(_setting_decimal("BALANZA_STABLE_TOLERANCE_KG", "0.020")),
        },
        "dispositivos": listar_dispositivos_balanza(),
    }


def normalizar_peso(raw):
    samples = _extraer_muestras_texto(raw)
    return samples[-1] if samples else None


def _extraer_muestras_texto(raw):
    text = _visible_text(raw)
    matches = re.finditer(
        # Exigir unidad evita confundir bytes corruptos o códigos de estado
        # con un peso (por ejemplo, ``HRo7)`` no equivale a 7 kg).
        r"(?P<value>[-+]?\d+(?:[\.,]\d+)?)\s*(?P<unit>kilogramos?|kgs?|gramos?|gr|g)",
        text,
        flags=re.IGNORECASE,
    )
    samples = []
    for match in matches:
        try:
            weight = Decimal(match.group("value").replace(",", "."))
        except (InvalidOperation, ValueError):
            continue
        unit = match.group("unit").lower()
        if unit in {"g", "gr", "gramo", "gramos"}:
            weight /= Decimal("1000")
        if Decimal("0") < weight <= _max_weight_kg():
            samples.append(weight.quantize(Decimal("0.001")))
    return samples


def _muestra_estable(samples):
    required = _setting_int("BALANZA_STABLE_SAMPLES", 3, 1)
    if len(samples) < required:
        return None
    window = samples[-required:]
    tolerance = _setting_decimal("BALANZA_STABLE_TOLERANCE_KG", "0.020")
    if max(window) - min(window) <= tolerance:
        return window[-1].quantize(Decimal("0.001"))
    return None


def _puertos_serial_a_probar(seriales):
    configured = _configured_serial_ports()

    def sort_key(item):
        port = str(item.get("puerto") or "")
        match = re.search(r"(\d+)$", port)
        number = int(match.group(1)) if match else 9999
        configured_index = configured.index(port.upper()) if port.upper() in configured else 9999
        return (
            configured_index,
            not item.get("configurado", False),
            not item.get("probable_balanza", False),
            number,
            port,
        )

    return sorted(seriales, key=sort_key)


def _parse_serial_mode(serial, mode):
    match = re.fullmatch(r"([78])([NOE])([12])", mode.upper())
    if not match:
        raise ValueError(f"Modo serial inválido: {mode}")
    bytesize = serial.SEVENBITS if match.group(1) == "7" else serial.EIGHTBITS
    parity = {
        "N": serial.PARITY_NONE,
        "E": serial.PARITY_EVEN,
        "O": serial.PARITY_ODD,
    }[match.group(2)]
    stopbits = serial.STOPBITS_TWO if match.group(3) == "2" else serial.STOPBITS_ONE
    return bytesize, parity, stopbits


def _apply_line_control(port, control):
    if control == "rts":
        port.rts = True
    elif control == "dtr_rts":
        port.dtr = True
        port.rts = True
    elif control == "none":
        port.dtr = False
        port.rts = False


def _leer_serial_estable(puerto, baudrate, mode, line_control, port_info=None):
    serial, _, error = _serial_modules()
    if error:
        return _error_resultado(error, codigo="pyserial_no_disponible")

    handle = None
    raw_parts = []
    samples = []
    try:
        bytesize, parity, stopbits = _parse_serial_mode(serial, mode)
        handle = serial.Serial()
        handle.port = puerto
        handle.baudrate = baudrate
        handle.bytesize = bytesize
        handle.parity = parity
        handle.stopbits = stopbits
        handle.timeout = 0.20
        handle.write_timeout = 0.20
        handle.xonxoff = False
        handle.rtscts = False
        handle.dsrdtr = False
        _apply_line_control(handle, line_control)
        handle.open()
        time.sleep(0.10)
        try:
            handle.reset_input_buffer()
        except Exception as exc:
            logger.debug("No se pudo limpiar el buffer serial: %s", exc)

        deadline = time.monotonic() + _setting_int("BALANZA_PROBE_SECONDS", 2, 1)
        command_index = 0
        last_poll = 0.0
        while time.monotonic() < deadline:
            now = time.monotonic()
            if now - last_poll >= 0.5:
                commands = _poll_commands()
                command = commands[command_index % len(commands)]
                command_index += 1
                last_poll = now
                if command:
                    try:
                        handle.write(command.encode("ascii"))
                        handle.flush()
                    except Exception as exc:
                        logger.debug("No se pudo enviar el comando de sondeo serial: %s", exc)

            chunk = handle.read(max(getattr(handle, "in_waiting", 0), 1))
            if not chunk:
                continue
            raw_parts.append(_visible_text(chunk))
            samples.extend(_extraer_muestras_texto(chunk))
            stable = _muestra_estable(samples)
            if stable is not None:
                description = (port_info or {}).get("descripcion") or puerto
                return {
                    "ok": True,
                    "peso": stable,
                    "unidad": "kg",
                    "puerto": puerto,
                    "baudrate": baudrate,
                    "serial_mode": mode,
                    "line_control": line_control,
                    "mensaje": "Lectura correcta",
                    "raw": "".join(raw_parts)[-1000:],
                    "dispositivo": f"{description} ({puerto}@{baudrate}/{mode}/{line_control})",
                    "fuente": "serial",
                }
        return _error_resultado("sin lectura estable", codigo="sin_lectura")
    except Exception as exc:
        text = str(exc)
        lowered = text.lower()
        if isinstance(exc, PermissionError) or "access" in lowered and "denied" in lowered or "acceso denegado" in lowered:
            return _error_resultado(
                f"No se pudo abrir {puerto}: acceso denegado",
                codigo="puerto_ocupado",
                accion="Cierre cualquier programa o puente duplicado que esté usando ese puerto.",
                errores=[text],
            )
        return _error_resultado(
            f"No se pudo leer {puerto}",
            codigo="error_serial",
            accion="Revise el controlador USB-serial, el cable y la alimentación de la balanza.",
            errores=[text],
        )
    finally:
        if handle is not None:
            try:
                handle.close()
            except Exception as exc:
                logger.debug("No se pudo cerrar el puerto serial: %s", exc)


def _extraer_peso_hid(raw):
    if not raw:
        return None
    for offset in range(max(0, len(raw) - 4)):
        unit = raw[offset + 1]
        exponent_byte = raw[offset + 2]
        raw_weight = raw[offset + 3] | (raw[offset + 4] << 8)
        if unit not in {2, 3, 11, 12} or raw_weight <= 0:
            continue
        exponent = exponent_byte - 256 if exponent_byte > 127 else exponent_byte
        weight = Decimal(raw_weight) * (Decimal(10) ** exponent)
        if unit == 2:
            weight /= Decimal("1000")
        elif unit == 11:
            weight *= Decimal("0.0283495")
        elif unit == 12:
            weight *= Decimal("0.45359237")
        if Decimal("0") < weight <= _max_weight_kg():
            return weight.quantize(Decimal("0.001"))
    return None


def _leer_hid_estable(devices):
    hid, error = _hid_module()
    if error:
        return _error_resultado(error, codigo="hid_no_disponible")

    errors = []
    candidates = sorted(devices, key=lambda item: not item.get("probable_balanza"))
    for item in candidates:
        handle = None
        samples = []
        try:
            if not item.get("path"):
                continue
            handle = hid.device()
            handle.open_path(item["path"])
            try:
                handle.set_nonblocking(1)
            except Exception as exc:
                logger.debug("El dispositivo HID no admite modo no bloqueante: %s", exc)
            deadline = time.monotonic() + _setting_int("BALANZA_PROBE_SECONDS", 2, 1)
            while time.monotonic() < deadline:
                try:
                    data = handle.read(64, timeout_ms=200)
                except TypeError:
                    data = handle.read(64)
                if not data:
                    time.sleep(0.05)
                    continue
                raw = bytes(data)
                sample = _extraer_peso_hid(raw)
                samples.extend([sample] if sample is not None else _extraer_muestras_texto(raw))
                stable = _muestra_estable(samples)
                if stable is not None:
                    return {
                        "ok": True,
                        "peso": stable,
                        "unidad": "kg",
                        "puerto": item.get("producto") or "HID",
                        "baudrate": None,
                        "serial_mode": None,
                        "line_control": None,
                        "mensaje": "Lectura correcta",
                        "raw": _visible_text(raw),
                        "dispositivo": item.get("producto") or "balanza-hid",
                        "fuente": "hid",
                    }
        except Exception as exc:
            errors.append(str(exc))
        finally:
            if handle is not None:
                try:
                    handle.close()
                except Exception as exc:
                    logger.debug("No se pudo cerrar el dispositivo HID: %s", exc)
    return _error_resultado(
        "No se recibieron datos válidos por HID",
        codigo="sin_lectura_hid",
        errores=errors[-5:],
    )


def _leer_usb_estable(devices):
    usb_core, usb_util, usb_backend, error = _usb_modules()
    if error:
        return _error_resultado(error, codigo="pyusb_no_disponible")

    candidates = [item for item in devices if item.get("probable_balanza")]
    if not candidates:
        return _error_resultado(
            "No se identificó una balanza USB directa",
            codigo="sin_balanza_usb",
            accion="Si usa un adaptador USB-RS232, debe aparecer como puerto COM.",
        )

    try:
        raw_devices = list(usb_core.find(find_all=True, backend=usb_backend) or [])
    except Exception as exc:
        return _error_resultado(
            f"No se pudo enumerar USB: {exc}",
            codigo="usb_backend_faltante",
            accion="Instale el controlador oficial del dispositivo y el backend USB requerido.",
        )

    errors = []
    for item in candidates:
        device = next((
            candidate for candidate in raw_devices
            if getattr(candidate, "idVendor", None) == item.get("vendor_id")
            and getattr(candidate, "idProduct", None) == item.get("product_id")
        ), None)
        if device is None:
            continue
        try:
            try:
                configuration = device.get_active_configuration()
            except Exception:
                device.set_configuration()
                configuration = device.get_active_configuration()
            endpoint = next((
                endpoint
                for interface in configuration
                for endpoint in interface
                if usb_util.endpoint_direction(endpoint.bEndpointAddress) == usb_util.ENDPOINT_IN
            ), None)
            if endpoint is None:
                continue
            samples = []
            deadline = time.monotonic() + _setting_int("BALANZA_PROBE_SECONDS", 2, 1)
            while time.monotonic() < deadline:
                try:
                    raw = bytes(device.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize, timeout=200))
                except Exception as exc:
                    logger.debug("Lectura USB omitida durante sondeo: %s", exc)
                    continue
                sample = _extraer_peso_hid(raw)
                samples.extend([sample] if sample is not None else _extraer_muestras_texto(raw))
                stable = _muestra_estable(samples)
                if stable is not None:
                    return {
                        "ok": True,
                        "peso": stable,
                        "unidad": "kg",
                        "puerto": item.get("producto") or "USB",
                        "baudrate": None,
                        "serial_mode": None,
                        "line_control": None,
                        "mensaje": "Lectura correcta",
                        "raw": _visible_text(raw),
                        "dispositivo": item.get("producto") or "balanza-usb",
                        "fuente": "usb",
                    }
        except Exception as exc:
            errors.append(str(exc))
        finally:
            try:
                usb_util.dispose_resources(device)
            except Exception as exc:
                logger.debug("No se pudieron liberar recursos USB: %s", exc)
    return _error_resultado(
        "No se recibieron datos válidos por USB",
        codigo="sin_lectura_usb",
        errores=errors[-5:],
    )


def obtener_peso_estable():
    if not _read_lock.acquire(blocking=False):
        return _error_resultado(
            "Ya hay una búsqueda de balanza en curso",
            codigo="lectura_en_curso",
            accion="Espere unos segundos y vuelva a intentar.",
        )
    try:
        return _obtener_peso_estable_sin_bloqueo()
    finally:
        _read_lock.release()


def _obtener_peso_estable_sin_bloqueo():
    devices = listar_dispositivos_balanza()
    errors = list(devices["errores"])
    ports = _puertos_serial_a_probar(devices["serial"])
    deadline = time.monotonic() + _setting_int("BALANZA_SCAN_TIMEOUT_SECONDS", 20, 1)
    attempted_ports = []
    timed_out = False
    baudrates = _serial_baudrates()
    modes = _serial_modes()
    controls = _line_controls()

    # Primera pasada obligatoria: cada puerto visible se prueba con la
    # configuración más común, incluso si un puerto lento consume el presupuesto.
    first_config = (baudrates[0], modes[0], controls[0])
    for port in ports:
        name = port["puerto"]
        attempted_ports.append(name)
        result = _leer_serial_estable(name, *first_config, port)
        if result["ok"]:
            result["puertos_probados"] = attempted_ports
            return result
        errors.extend(result.get("errores") or [])

    # Después de haber cubierto todos los puertos, se profundiza en el resto
    # de baudios, modos y controles hasta agotar el tiempo configurado.
    for baudrate in baudrates:
        for mode in modes:
            for line_control in controls:
                if (baudrate, mode, line_control) == first_config:
                    continue
                for port in ports:
                    if time.monotonic() >= deadline:
                        timed_out = True
                        break
                    name = port["puerto"]
                    result = _leer_serial_estable(name, baudrate, mode, line_control, port)
                    if result["ok"]:
                        result["puertos_probados"] = attempted_ports
                        return result
                    errors.extend(result.get("errores") or [])
                if timed_out:
                    break
            if timed_out:
                break
        if timed_out:
            break

    # Aunque existan puertos COM, también se prueban HID y USB. La versión
    # anterior terminaba antes y podía omitir una balanza válida de esos tipos.
    hid_result = _leer_hid_estable(devices["hid"])
    if hid_result["ok"]:
        hid_result["puertos_probados"] = attempted_ports
        return hid_result
    errors.extend(hid_result.get("errores") or [])

    usb_result = _leer_usb_estable(devices["usb"])
    if usb_result["ok"]:
        usb_result["puertos_probados"] = attempted_ports
        return usb_result
    errors.extend(usb_result.get("errores") or [])

    return _error_resultado(
        "No se detectó una lectura estable en Serial, HID ni USB",
        codigo="sin_lectura",
        accion=(
            "Conecte y encienda la balanza, instale su controlador USB-serial, "
            "cierre programas que ocupen el COM y verifique el protocolo de transmisión."
        ),
        errores=errors[-12:],
        puertos_probados=attempted_ports,
        busqueda_agotada=timed_out,
    )
