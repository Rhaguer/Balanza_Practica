#!/usr/bin/env python
"""Servidor WSGI local y portable para Windows, Linux y macOS."""

import argparse
import os
import sys
from pathlib import Path

from waitress import serve

sys.dont_write_bytecode = True


def main():
    parser = argparse.ArgumentParser(description="Servidor local de Balanza de Mermas.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--threads", type=int, default=8)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "codigo_qr.settings")
    from codigo_qr.wsgi import application

    serve(
        application,
        host=args.host,
        port=args.port,
        threads=max(args.threads, 4),
        channel_timeout=120,
        clear_untrusted_proxy_headers=True,
    )


if __name__ == "__main__":
    main()
