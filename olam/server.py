"""Run Olam on each address in config.HOSTS (OLAM_HOSTS), all on one port."""
import logging
import socket

import uvicorn

from . import config, db, zims
from .app import app


def _bind(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    return s


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    db.connect()
    zims.all()
    sockets = [_bind(h, config.PORT) for h in config.HOSTS]
    uvicorn.Server(uvicorn.Config(app, log_level="info", proxy_headers=False, access_log=False)).run(sockets=sockets)


if __name__ == "__main__":
    main()
