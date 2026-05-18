"""
Manages the Bluetooth RFCOMM connection to the Brother printer.

Requires the calling user to be able to run rfcomm via sudo without a password.
Add this line to /etc/sudoers (via visudo):
    <user> ALL=(ALL) NOPASSWD: /usr/bin/rfcomm
"""

import re
import subprocess
import threading
import time

from config import BT_MAC, PRINTER_PORT

RETRY_DELAY = 10  # seconds between reconnect attempts

_thread: threading.Thread | None = None
_stop = threading.Event()


def _port_num(port_path: str) -> int:
    m = re.search(r'\d+$', port_path)
    return int(m.group()) if m else 0


def _loop(mac: str, port_num: int) -> None:
    while not _stop.is_set():
        print(f'[rfcomm] Connecting to {mac} on rfcomm{port_num}…', flush=True)
        try:
            proc = subprocess.Popen(
                ['sudo', '/usr/bin/rfcomm', 'connect', str(port_num), mac],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            _, stderr = proc.communicate()
            if stderr:
                print(f'[rfcomm] {stderr.decode().strip()}', flush=True)
        except FileNotFoundError:
            print('[rfcomm] /usr/bin/rfcomm not found — install bluez-utils', flush=True)
        except Exception as e:
            print(f'[rfcomm] Error: {e}', flush=True)

        if not _stop.is_set():
            print(f'[rfcomm] Connection lost, retrying in {RETRY_DELAY}s…', flush=True)
            _stop.wait(RETRY_DELAY)


def start() -> None:
    """Start the background rfcomm manager. No-op if already running or MAC not configured."""
    global _thread
    if not BT_MAC:
        print('[rfcomm] BROTHER_BT_MAC not set — skipping auto-connect', flush=True)
        return
    if _thread and _thread.is_alive():
        return
    _stop.clear()
    _thread = threading.Thread(
        target=_loop,
        args=(BT_MAC, _port_num(PRINTER_PORT)),
        daemon=True,
        name='rfcomm-manager',
    )
    _thread.start()


def stop() -> None:
    _stop.set()
