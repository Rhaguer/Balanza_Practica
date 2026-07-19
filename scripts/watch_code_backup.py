#!/usr/bin/env python
"""Sincroniza el respaldo único cuando cambia un archivo del código."""

import argparse
import socket
import time
from pathlib import Path

from sync_code_backup import default_destination, is_excluded, project_root, sync


def snapshot(root):
    state = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if is_excluded(relative):
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        state[relative.as_posix()] = (stat.st_mtime_ns, stat.st_size)
    return state


def acquire_lock(port):
    lock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        lock.bind(("127.0.0.1", port))
        lock.listen(1)
        return lock
    except OSError:
        lock.close()
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--lock-port", type=int, default=47633)
    args = parser.parse_args()

    lock = acquire_lock(args.lock_port)
    if lock is None:
        print("El respaldo automático de código ya está activo.")
        return

    root = project_root()
    destination = args.destination or default_destination(root)
    sync(root, destination)
    previous = snapshot(root)
    print(f"Respaldo automático de código activo: {destination}", flush=True)

    try:
        while True:
            time.sleep(max(args.interval, 0.5))
            current = snapshot(root)
            if current != previous:
                sync(root, destination)
                previous = current
                print("Respaldo de código actualizado.", flush=True)
    finally:
        lock.close()


if __name__ == "__main__":
    main()
