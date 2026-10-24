"""One password for the owner and a signed cookie for the browser.

auth.json lives in the data folder, outside git: {"salt": hex, "hash": hex, "secret": hex}.
Changing the password replaces the secret, which signs out every browser at once.
"""
import hashlib
import hmac
import json
import secrets
import time

from . import config

COOKIE = "olam"
DAYS = 365


def _scrypt(password, salt):
    return hashlib.scrypt(password.encode(), salt=salt, n=2 ** 14, r=8, p=1, dklen=32)


def _load():
    try:
        return json.loads(config.AUTH_FILE.read_text())
    except (FileNotFoundError, ValueError):
        return None


def set_password(password):
    config.DATA.mkdir(parents=True, exist_ok=True)
    salt = secrets.token_bytes(16)
    tmp = config.AUTH_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps({"salt": salt.hex(), "hash": _scrypt(password, salt).hex(), "secret": secrets.token_hex(32)}))
    tmp.chmod(0o600)
    tmp.replace(config.AUTH_FILE)


def new_secret():
    """Sign out every browser, keeping the password."""
    a = _load()
    a["secret"] = secrets.token_hex(32)
    tmp = config.AUTH_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(a))
    tmp.chmod(0o600)
    tmp.replace(config.AUTH_FILE)


def check_password(password):
    a = _load()
    if not a:
        return False
    return hmac.compare_digest(_scrypt(password, bytes.fromhex(a["salt"])).hex(), a["hash"])


def make_cookie():
    a = _load()
    exp = str(int(time.time()) + DAYS * 86400)
    sig = hmac.new(bytes.fromhex(a["secret"]), exp.encode(), hashlib.sha256).hexdigest()
    return f"{exp}.{sig}"


def valid(cookie):
    a = _load()
    if not a or not cookie or "." not in cookie:
        return False
    exp, sig = cookie.split(".", 1)
    good = hmac.new(bytes.fromhex(a["secret"]), exp.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig, good) and exp.isdigit() and int(exp) > time.time()


def configured():
    return _load() is not None
