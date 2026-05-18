## Setup

1. Boot your Raspberry Pi Zero and install git:
   ```
   sudo apt install -y git
   ```
2. Checkout this repo on the Pi: 
   ```

   ```
3. Connect to your Brother printer via bluetooth: run `bluetoothctl` and enter the following commands in its prompt.
   ```
   power on                                                                                
   scan on                                                                                 
   agent on                                                                                
   ```
   Wait a little for the scan to complete. Then enter `devices` bluetoothctl command. You should see the Brother printer devices mac. Run `pair` & `trust` with its mac:
   ```
   pair <mac>
   trust <mac>
   ```