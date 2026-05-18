import os
from pathlib import Path


def _load_env():
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, _, val = line.partition('=')
                os.environ.setdefault(key.strip(), val.strip())


_load_env()

BT_MAC = os.environ.get('BROTHER_BT_MAC', '')
PRINTER_PORT = os.environ.get('BROTHER_PORT', '/dev/rfcomm0')
