#!/usr/bin/env python3
"""Walk Olam in a headless Chrome container, signed in, and save screenshots (a developer's check).

    tools/walk.py OUTDIR [--width 1440 --height 1000] [--mobile] [--base URL]

The container (OLAM_CHROME, default docker-chrome-1) runs Chrome with DevTools on port 9222 and must reach Olam at
OLAM_URL. Opens its own tab, runs the walk below, reports any JavaScript errors, and closes the tab. Stdlib only.
"""
import argparse
import base64
import json
import os
import socket
import struct
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from olam import auth, config  # noqa: E402

CONTAINER = os.environ.get("OLAM_CHROME", "docker-chrome-1")
BASE = config.URL


def container_ip():
    return subprocess.run(["docker", "inspect", "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}", CONTAINER],
                          capture_output=True, text=True, check=True).stdout.strip()


def ensure_chrome(ip):
    try:
        urllib.request.urlopen(f"http://{ip}:9222/json/version", timeout=2)
        return
    except OSError:
        pass
    subprocess.run(["docker", "exec", "-d", CONTAINER, "chromium-browser", "--headless=new", "--no-sandbox", "--disable-gpu",
                    "--disable-dev-shm-usage", "--hide-scrollbars", "--remote-debugging-port=9222",
                    "--remote-debugging-address=0.0.0.0", "about:blank"], check=True)
    for _ in range(40):
        try:
            urllib.request.urlopen(f"http://{ip}:9222/json/version", timeout=2)
            return
        except OSError:
            time.sleep(0.25)
    raise SystemExit("chromium did not start")


class WS:
    def __init__(self, url):
        host_port, path = url[len("ws://"):].split("/", 1)
        host, port = host_port.split(":")
        self.s = socket.create_connection((host, int(port)), timeout=60)
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f"GET /{path} HTTP/1.1\r\nHost: {host_port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                        f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += self.s.recv(4096)
        self.rest = buf.split(b"\r\n\r\n", 1)[1]
        self.n = 0

    def _recv(self, n):
        while len(self.rest) < n:
            self.rest += self.s.recv(65536)
        out, self.rest = self.rest[:n], self.rest[n:]
        return out

    def send(self, method, **params):
        self.n += 1
        data = json.dumps({"id": self.n, "method": method, "params": params}).encode()
        hdr = bytes([0x81])
        ln = len(data)
        hdr += bytes([0x80 | ln]) if ln < 126 else (bytes([0x80 | 126]) + struct.pack(">H", ln) if ln < 65536 else bytes([0x80 | 127]) + struct.pack(">Q", ln))
        mask = os.urandom(4)
        self.s.sendall(hdr + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))
        while True:
            msg = self.read()
            if msg.get("id") == self.n:
                return msg.get("result", msg)

    def read(self):
        payload = b""
        while True:
            b1, b2 = self._recv(2)
            ln = b2 & 0x7F
            if ln == 126:
                ln = struct.unpack(">H", self._recv(2))[0]
            elif ln == 127:
                ln = struct.unpack(">Q", self._recv(8))[0]
            payload += self._recv(ln)
            if b1 & 0x80:
                return json.loads(payload.decode("utf-8", "replace"))


class Page:
    def __init__(self, width, height, mobile, out, base=None):
        global BASE
        BASE = base or BASE
        self.ip = container_ip()
        ensure_chrome(self.ip)
        t = json.load(urllib.request.urlopen(urllib.request.Request(f"http://{self.ip}:9222/json/new?about:blank", method="PUT")))
        self.id = t["id"]
        self.ws = WS(t["webSocketDebuggerUrl"].replace("localhost", self.ip).replace("127.0.0.1", self.ip))
        self.out, self.width, self.height, self.mobile = out, width, height, mobile
        self.ws.send("Network.enable")
        self.ws.send("Network.setCookie", name=auth.COOKIE, value=auth.make_cookie(), url=BASE.split("/", 3)[0] + "//" + BASE.split("/", 3)[2] + "/")
        self.ws.send("Emulation.setDeviceMetricsOverride", width=width, height=height, deviceScaleFactor=1, mobile=mobile)
        self.ws.send("Page.enable")
        self.ws.send("Page.addScriptToEvaluateOnNewDocument", source=(
            "window.__errs=[];addEventListener('error',e=>__errs.push(String(e.message||e)));"
            "addEventListener('unhandledrejection',e=>__errs.push('promise: '+String(e.reason&&e.reason.message||e.reason)));"))

    def go(self, path, wait=2.5):
        self.ws.send("Page.navigate", url=BASE + path)
        time.sleep(wait)

    def ev(self, expr, wait=0.0):
        r = self.ws.send("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
        if wait:
            time.sleep(wait)
        return r.get("result", {}).get("value")

    def until(self, expr, timeout=60):
        t = time.time()
        while time.time() - t < timeout:
            if self.ev(expr):
                return True
            time.sleep(0.5)
        return False

    def shot(self, name, full=False):
        if full:
            h = int(self.ev("Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)") or self.height)
            self.ws.send("Emulation.setDeviceMetricsOverride", width=self.width, height=min(h, 9000), deviceScaleFactor=1, mobile=self.mobile)
            time.sleep(0.8)
        png = self.ws.send("Page.captureScreenshot", format="png")
        path = os.path.join(self.out, name + ".png")
        with open(path, "wb") as f:
            f.write(base64.b64decode(png["data"]))
        if full:
            self.ws.send("Emulation.setDeviceMetricsOverride", width=self.width, height=self.height, deviceScaleFactor=1, mobile=self.mobile)
        errs = json.loads(self.ev("JSON.stringify(window.__errs||[])") or "[]")
        print(name, "errors:" if errs else "ok", errs or "")
        return path

    def close(self):
        try:
            urllib.request.urlopen(f"http://{self.ip}:9222/json/close/{self.id}", timeout=5)
        except OSError:
            pass


def walk(p, ask=True):
    p.go("/#/learn", 3)
    p.shot("01-learn", full=True)
    p.ev("document.querySelector('[data-step=see]')?.click()", 1.2)
    p.shot("02-see")
    p.ev("document.querySelector('[data-step=do]')?.click()", 1.2)
    p.shot("03-do")
    p.ev("document.querySelector('[data-step=check]')?.click()", 1.2)
    p.shot("04-check")
    p.go("/#/codex?q=owlbear&ed=2024", 3)
    p.shot("05-codex")
    p.go("/#/wiki/srd-2024%2Fmonster%2Fowlbear", 3)
    p.shot("06-owlbear", full=True)
    p.go("/#/wiki/srd-2024%2Fglossary%2Fgrappled", 3)
    p.shot("07-grappled")
    if ask:
        p.go("/#/ask?q=" + urllib.request.quote("Can I take a reaction on my own turn?"), 1)
        p.until("!!document.querySelector('.answer')", 90)
        p.shot("08-ask", full=True)
    p.go("/#/learn/advantage", 3)
    p.shot("09-advantage-lesson")
    p.go("/#/read/rpg.stackexchange.com/questions%2F34825%2Fwhat-s-the-inspiration-for-the-owlbear", 3)
    p.shot("10-reader")
    p.go("/#/credits", 2.5)
    p.shot("11-credits", full=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--width", type=int, default=1440)
    ap.add_argument("--height", type=int, default=1000)
    ap.add_argument("--mobile", action="store_true")
    ap.add_argument("--no-ask", action="store_true")
    ap.add_argument("--base", help="another address, e.g. https://example.com/olam")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    p = Page(a.width, a.height, a.mobile, a.out, a.base)
    try:
        walk(p, ask=not a.no_ask)
    finally:
        p.close()


if __name__ == "__main__":
    main()
