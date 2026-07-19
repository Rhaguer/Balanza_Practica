#!/usr/bin/env python
import argparse
import json
import os
import re
import signal
import sys
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


DEFAULT_BAUDRATES = (9600, 4800, 2400, 1200, 19200, 38400, 57600, 115200)
DEFAULT_MODES = ("8N1", "7E1", "8E1", "7N1", "8N2")
DEFAULT_LINE_CONTROLS = ("default", "rts", "dtr_rts", "none")
DEFAULT_COMMANDS = ("", "P\r\n", "W\r\n", "SI\r\n", "S\r\n", "Q\r\n", "PRINT\r\n")
SERIAL_KEYWORDS = ("usb", "serial", "ch340", "ch341", "cp210", "prolific", "pl2303", "ftdi", "rs232")


def project_root():
    return Path(__file__).resolve().parents[1]


def read_env(path):
    values = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def env_value(values, name, default=""):
    return os.environ.get(name) or values.get(name) or default


def csv_values(text, default=()):
    if not text:
        return tuple(default)
    return tuple(item.strip() for item in text.split(",") if item.strip())


def csv_ints(text, default=()):
    values = []
    for item in csv_values(text):
        try:
            parsed = int(item)
        except ValueError:
            continue
        if parsed > 0:
            values.append(parsed)
    return tuple(values or default)


def visible_text(raw):
    if not raw:
        return ""
    if isinstance(raw, str):
        return raw
    return bytes(raw).decode("ascii", errors="ignore")


def extract_weight_kg(text, max_weight_kg):
    matches = list(re.finditer(
        # A serial frame is only a weight when the number includes a unit.
        # This prevents corrupted baud/parity data such as ``HRo7)`` from
        # being accepted as 7 kg.
        r"(?P<value>-?\d+(?:[\.,]\d+)?)\s*(?P<unit>kilogramos?|kgs?|gramos?|gr|g)",
        text,
        flags=re.IGNORECASE,
    ))
    if not matches:
        return None

    for match in reversed(matches):
        try:
            weight = Decimal(match.group("value").replace(",", "."))
        except (InvalidOperation, ValueError):
            continue
        unit = match.group("unit").lower()
        if unit in {"g", "gr", "gramo", "gramos"}:
            weight = weight / Decimal("1000")
        if Decimal("0") < weight <= max_weight_kg:
            return weight.quantize(Decimal("0.001"))
    return None


def is_stable(samples, required, tolerance):
    if len(samples) < required:
        return False
    window = samples[-required:]
    return max(window) - min(window) <= tolerance


def parse_mode(serial, mode):
    match = re.match(r"^([78])([NOE])([12])$", mode.upper())
    if not match:
        raise ValueError(f"Modo serial invalido: {mode}")
    bytesize = serial.SEVENBITS if match.group(1) == "7" else serial.EIGHTBITS
    parity = {
        "N": serial.PARITY_NONE,
        "E": serial.PARITY_EVEN,
        "O": serial.PARITY_ODD,
    }[match.group(2)]
    stopbits = serial.STOPBITS_TWO if match.group(3) == "2" else serial.STOPBITS_ONE
    return bytesize, parity, stopbits


def apply_line_control(ser, line_control):
    if line_control == "rts":
        ser.rts = True
    elif line_control == "dtr_rts":
        ser.dtr = True
        ser.rts = True
    elif line_control == "none":
        ser.dtr = False
        ser.rts = False


def post_weight(endpoint, token, weight, device_name, raw_data):
    payload = json.dumps({
        "weight_kg": str(weight),
        "device_name": device_name,
        "raw_data": raw_data[-1000:],
        "is_stable": True,
    }).encode("utf-8")
    request = Request(
        endpoint,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Weight-Token": token,
        },
        method="POST",
    )
    with urlopen(request, timeout=3) as response:
        response.read()


def port_sort_key(port):
    text = " ".join([
        str(getattr(port, "device", "") or ""),
        str(getattr(port, "description", "") or ""),
        str(getattr(port, "manufacturer", "") or ""),
        str(getattr(port, "hwid", "") or ""),
    ]).lower()
    probable = any(keyword in text for keyword in SERIAL_KEYWORDS)
    match = re.search(r"(\d+)$", getattr(port, "device", "") or "")
    number = int(match.group(1)) if match else 9999
    return (not probable, number, getattr(port, "device", ""))


def list_ports(configured_ports):
    from serial.tools import list_ports as serial_list_ports

    detected = list(serial_list_ports.comports())
    detected_names = {str(port.device).upper() for port in detected}
    ports = [str(port.device) for port in sorted(detected, key=port_sort_key)]
    for configured in configured_ports:
        if configured.upper() not in detected_names:
            ports.insert(0, configured)
    return ports


def probe_or_watch_port(serial, port, baudrate, mode, line_control, config, once=False):
    bytesize, parity, stopbits = parse_mode(serial, mode)
    label = f"{port}@{baudrate}/{mode}/{line_control}"
    samples = []
    buffer = ""
    last_sent = None
    last_sent_at = 0.0
    last_poll = 0.0
    command_index = 0
    deadline = time.monotonic() + config["read_seconds"]
    detected = False

    with serial.Serial(
        port=port,
        baudrate=baudrate,
        bytesize=bytesize,
        parity=parity,
        stopbits=stopbits,
        timeout=0.25,
        write_timeout=0.25,
        xonxoff=False,
        rtscts=False,
        dsrdtr=False,
    ) as ser:
        apply_line_control(ser, line_control)
        time.sleep(0.2)
        try:
            ser.reset_input_buffer()
        except Exception:
            pass

        print(f"Conectado a {label}.", flush=True)
        while True:
            now = time.monotonic()
            if now - last_poll >= 0.8:
                command = config["commands"][command_index % len(config["commands"])]
                command_index += 1
                last_poll = now
                if command:
                    try:
                        ser.write(command.encode("ascii"))
                        ser.flush()
                    except Exception:
                        pass

            chunk = ser.read(max(getattr(ser, "in_waiting", 0), 1))
            if chunk:
                buffer = (buffer + " " + visible_text(chunk))[-1000:]
                weight = extract_weight_kg(buffer, config["max_weight_kg"])
                if weight is not None:
                    samples.append(weight)
                    samples = samples[-config["stable_samples"]:]
                    if is_stable(samples, config["stable_samples"], config["stable_tolerance_kg"]):
                        if once:
                            print(f"Balanza detectada en {label}: {weight} kg", flush=True)
                            return True
                        detected = True
                        cooldown_ok = (now - last_sent_at) >= config["post_cooldown_seconds"]
                        if weight != last_sent or cooldown_ok:
                            try:
                                post_weight(config["endpoint"], config["token"], weight, label, buffer.strip())
                                print(f"Peso enviado desde {label}: {weight} kg", flush=True)
                                last_sent = weight
                                last_sent_at = now
                            except (URLError, OSError) as exc:
                                print(f"No se pudo enviar a Django: {exc}", flush=True)

            # En modo servicio también hay que abandonar una configuración que
            # no entrega peso estable; de otro modo el primer COM/baudrate válido
            # queda abierto para siempre y nunca se prueban los demás candidatos.
            if not detected and time.monotonic() >= deadline:
                return False
            time.sleep(config["read_pause_seconds"])


def build_config(args, env):
    api_path = env_value(env, "DJANGO_WEIGHT_UPDATE_URL", "/api/update_weight/")
    server_url = args.server_url.rstrip("/")
    endpoint = f"{server_url}/{api_path.strip('/')}"
    token = env_value(env, "WEIGHT_API_TOKEN")
    if not token:
        raise SystemExit("WEIGHT_API_TOKEN no esta configurado.")

    commands = csv_values(env_value(env, "BALANZA_POLL_COMMANDS"), DEFAULT_COMMANDS)
    commands = tuple(command.replace("\\r", "\r").replace("\\n", "\n") for command in commands)

    return {
        "endpoint": endpoint,
        "token": token,
        "ports": tuple(args.ports) or csv_values(env_value(env, "BALANZA_SERIAL_PORTS"), ()),
        "baudrates": tuple(args.baudrates) or csv_ints(env_value(env, "BALANZA_SERIAL_BAUDRATES"), DEFAULT_BAUDRATES),
        "modes": tuple(args.modes) or csv_values(env_value(env, "BALANZA_SERIAL_MODES"), DEFAULT_MODES),
        "line_controls": tuple(args.line_controls) or csv_values(env_value(env, "BALANZA_LINE_CONTROLS"), DEFAULT_LINE_CONTROLS),
        "commands": commands or DEFAULT_COMMANDS,
        "read_seconds": int(env_value(env, "BALANZA_READ_SECONDS", "4")),
        "rescan_seconds": args.rescan_seconds,
        "read_pause_seconds": args.read_pause_ms / 1000,
        "post_cooldown_seconds": args.post_cooldown_ms / 1000,
        "stable_samples": max(1, int(env_value(env, "BALANZA_STABLE_SAMPLES", "3"))),
        "stable_tolerance_kg": Decimal(env_value(env, "BALANZA_STABLE_TOLERANCE_KG", "0.020")),
        "max_weight_kg": Decimal(env_value(env, "MAX_WEIGHT_KG", "1000")),
    }


def main():
    parser = argparse.ArgumentParser(description="Puente automatico multiplataforma para balanza serial.")
    parser.add_argument("--server-url", default="http://127.0.0.1:8000")
    parser.add_argument("--env-file", default=str(project_root() / ".env"))
    parser.add_argument("--ports", nargs="*", default=())
    parser.add_argument("--baudrates", nargs="*", type=int, default=())
    parser.add_argument("--modes", nargs="*", default=())
    parser.add_argument("--line-controls", nargs="*", default=())
    parser.add_argument("--rescan-seconds", type=int, default=3)
    parser.add_argument("--read-pause-ms", type=int, default=120)
    parser.add_argument("--post-cooldown-ms", type=int, default=900)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--list-ports", action="store_true")
    args = parser.parse_args()

    try:
        import serial
    except Exception as exc:
        raise SystemExit(f"pyserial no esta disponible: {exc}")

    env = read_env(Path(args.env_file))
    config = build_config(args, env)

    if args.list_ports:
        ports = list_ports(config["ports"])
        if not ports:
            print("No hay puertos seriales disponibles.")
            return 0
        print("Puertos seriales disponibles:")
        for port in ports:
            print(f" - {port}")
        return 0

    stopped = False

    def handle_stop(_signum, _frame):
        nonlocal stopped
        stopped = True

    signal.signal(signal.SIGINT, handle_stop)
    signal.signal(signal.SIGTERM, handle_stop)

    print("Puente de balanza multiplataforma iniciado.", flush=True)
    print(f"Endpoint Django: {config['endpoint']}", flush=True)

    while not stopped:
        ports = list_ports(config["ports"])
        if not ports:
            print("No hay puertos seriales disponibles.", flush=True)
            if args.once:
                return 2
            time.sleep(config["rescan_seconds"])
            continue

        for port in ports:
            for baudrate in config["baudrates"]:
                for mode in config["modes"]:
                    for line_control in config["line_controls"]:
                        if stopped:
                            break
                        label = f"{port}@{baudrate}/{mode}/{line_control}"
                        print(f"Probando {label}...", flush=True)
                        try:
                            ok = probe_or_watch_port(serial, port, baudrate, mode, line_control, config, once=args.once)
                        except Exception as exc:
                            print(f"No se pudo usar {label}: {exc}", flush=True)
                            ok = False
                        if ok:
                            return 0

        if args.once:
            print("No se detecto lectura de balanza en los puertos disponibles.", flush=True)
            return 2

        print("No se detecto lectura. Reintentando...", flush=True)
        time.sleep(config["rescan_seconds"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
