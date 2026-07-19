#!/usr/bin/env python
import argparse
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

sys.dont_write_bytecode = True


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


def health_ok(url):
    try:
        with urlopen(url, timeout=2) as response:
            return response.status in {200, 403}
    except (OSError, URLError):
        return False


def hidden_creation_flags():
    if os.name != "nt":
        return 0
    return getattr(subprocess, "CREATE_NO_WINDOW", 0)


def run_checked(command, cwd):
    print(f"> {' '.join(str(part) for part in command)}", flush=True)
    subprocess.run(
        command,
        cwd=cwd,
        check=True,
        creationflags=hidden_creation_flags(),
    )


def start_process(command, cwd, log_path):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = log_path.open("a", encoding="utf-8")
    print(f"Iniciando: {' '.join(str(part) for part in command)}", flush=True)
    return subprocess.Popen(
        command,
        cwd=cwd,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=hidden_creation_flags(),
    )


def terminate(process):
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()


def acquire_instance_lock(port=47632):
    lock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        lock.bind(("127.0.0.1", port))
        lock.listen(1)
        return lock
    except OSError:
        lock.close()
        return None


def main():
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    parser = argparse.ArgumentParser(description="Arranque automatico de Django y balanza.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default="8000")
    parser.add_argument("--skip-install", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--bridge-once", action="store_true")
    parser.add_argument("--no-code-backup", action="store_true")
    args = parser.parse_args()

    root = project_root()
    env = read_env(root / ".env")
    log_dir = root / env.get("DJANGO_LOG_DIR", "logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    windowless_python = Path(sys.executable).stem.lower() == "pythonw"
    if sys.stdout is None or windowless_python:
        sys.stdout = (log_dir / "auto-start.log").open("a", encoding="utf-8")
    if sys.stderr is None or windowless_python:
        sys.stderr = sys.stdout
    python = sys.executable
    if windowless_python:
        console_python = Path(sys.executable).with_name("python.exe")
        if console_python.exists():
            python = str(console_python)
    server_url = f"http://{args.host}:{args.port}"
    instance_lock = acquire_instance_lock()
    if instance_lock is None:
        print("La aplicación ya está iniciada.", flush=True)
        if not args.no_browser:
            import webbrowser

            webbrowser.open(server_url)
        return

    if not args.skip_install:
        run_checked([python, "-m", "pip", "install", "--upgrade", "pip"], root)
        run_checked([python, "-m", "pip", "install", "-r", "requirements.txt"], root)

    run_checked([python, "manage.py", "migrate", "--noinput"], root)
    run_checked([python, "manage.py", "check"], root)
    run_checked([python, "manage.py", "collectstatic", "--noinput"], root)

    server = None
    bridge = None
    code_backup = None
    workshop_worker = None

    try:
        backup_script = root / "scripts" / "watch_code_backup.py"
        if backup_script.exists() and not args.no_code_backup:
            code_backup = start_process(
                [python, str(backup_script)],
                root,
                log_dir / "auto-code-backup.log",
            )

        if not health_ok(f"{server_url}/health/"):
            server = start_process(
                [
                    python,
                    str(root / "scripts" / "serve_app.py"),
                    "--host",
                    args.host,
                    "--port",
                    args.port,
                ],
                root,
                log_dir / "auto-django.log",
            )
            for _ in range(30):
                if health_ok(f"{server_url}/health/"):
                    break
                time.sleep(1)
            if not health_ok(f"{server_url}/health/"):
                raise RuntimeError(
                    "El servidor web no respondió. Revise auto-django.log."
                )

        workshop_worker = start_process(
            [python, "manage.py", "workshop_worker"],
            root,
            log_dir / "auto-workshop-worker.log",
        )

        bridge_command = [
            python,
            str(root / "scripts" / "weight_bridge.py"),
            "--server-url",
            server_url,
        ]
        if args.bridge_once:
            bridge_command.append("--once")
        bridge = start_process(bridge_command, root, log_dir / "auto-weight-bridge.log")

        print("")
        print(f"Aplicacion lista: {server_url}/", flush=True)
        print(f"Diagnostico balanza: {server_url}/balanza/diagnostico/", flush=True)
        print("El puente queda vigilando puertos USB/serial automaticamente.", flush=True)

        if not args.no_browser:
            try:
                import webbrowser

                webbrowser.open(server_url)
            except Exception:
                pass

        while True:
            if server and server.poll() is not None:
                print("Servidor web se detuvo; reiniciando.", flush=True)
                server = start_process(
                    [
                        python,
                        str(root / "scripts" / "serve_app.py"),
                        "--host",
                        args.host,
                        "--port",
                        args.port,
                    ],
                    root,
                    log_dir / "auto-django.log",
                )

            if bridge and bridge.poll() is not None and not args.bridge_once:
                print("Puente de balanza se detuvo; reiniciando.", flush=True)
                bridge = start_process(bridge_command, root, log_dir / "auto-weight-bridge.log")
            if bridge and bridge.poll() is not None and args.bridge_once:
                return
            if workshop_worker and workshop_worker.poll() is not None:
                print("Vigilancia de talleres se detuvo; reiniciando.", flush=True)
                workshop_worker = start_process(
                    [python, "manage.py", "workshop_worker"],
                    root,
                    log_dir / "auto-workshop-worker.log",
                )
            if code_backup and code_backup.poll() is not None:
                if code_backup.returncode == 0:
                    code_backup = None
                else:
                    print("Respaldo de código se detuvo; reiniciando.", flush=True)
                    code_backup = start_process(
                        [python, str(backup_script)],
                        root,
                        log_dir / "auto-code-backup.log",
                    )

            time.sleep(3)
    except KeyboardInterrupt:
        print("Deteniendo servicios.", flush=True)
    finally:
        terminate(workshop_worker)
        terminate(code_backup)
        terminate(bridge)
        terminate(server)
        instance_lock.close()


if __name__ == "__main__":
    main()
