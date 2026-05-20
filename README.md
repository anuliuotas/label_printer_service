# Label Printer Service

Web service and CLI for generating PNG labels and printing them on a **Brother PT-P300BT** via Bluetooth.

---

## Setup on Raspberry Pi Zero

### 1. Install system dependencies

```bash
sudo apt update
sudo apt install -y git bluetooth bluez python3-pip \
    zlib1g-dev libjpeg-dev libfreetype6-dev python3-dev
```

> The last four packages are C build dependencies for Pillow. The Pi Zero is ARMv6
> and has no pre-built Pillow wheel, so it compiles from source.

### 2. Install uv (Python package manager)

```bash
curl -Ls https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

### 3. Clone the repository

```bash
git clone https://github.com/anuliuotas/label_printer_service.git
cd label_printer_service
```

### 4. Install Python dependencies

```bash
uv sync
```

### 5. Pair the printer via Bluetooth

Power on the Brother PT-P300BT, then run `bluetoothctl`:

```bash
bluetoothctl
```

Inside the prompt:

```
power on
agent on
scan on
```

Wait for the printer to appear in the device list, then note its MAC address. Run:

```
pair <MAC>
trust <MAC>
exit
```

### 6. Configure the environment

```bash
cp .env.example .env
```

Edit `.env` and set your printer's MAC address:

```
BROTHER_BT_MAC=XX:XX:XX:XX:XX:XX
BROTHER_PORT=/dev/rfcomm0
```

### 7. Allow passwordless rfcomm (required for auto-connect)

The app manages the Bluetooth RFCOMM connection automatically. Grant the required permission:

```bash
sudo visudo
```

Add this line (replace `pi` with your username):

```
pi ALL=(ALL) NOPASSWD: /usr/bin/rfcomm
```

---

## Running

### Web app

```bash
uv run python web/app.py
```

Open `http://<pi-ip>:5000` in your browser.

### CLI

```bash
uv run python generator.py "Your Text" --width 600 --cut-marks
```

---

## Run on boot (optional)

Create a systemd service so the web app starts automatically:

```bash
sudo nano /etc/systemd/system/label-printer.service
```

Paste the following (replace `pi` and the path if needed):

```ini
[Unit]
Description=Label Printer Service
After=network.target bluetooth.target

[Service]
User=pi
WorkingDirectory=/home/pi/label_printer_service
ExecStart=/home/pi/.local/bin/uv run python web/app.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start it:

```bash
sudo systemctl enable label-printer
sudo systemctl start label-printer
```

---

## Updating the service

```bash
cd ~/label_printer_service
git pull
sudo systemctl restart label-printer
sudo systemctl status label-printer
```
