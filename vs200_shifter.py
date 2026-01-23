import asyncio
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
import pyautogui
import platform
import sys

# --- Configuration (Check and Adjust as needed) ---
DEVICE_NAME = "Think VS01-"
NOTIFY_UUID = "0000fea1-0000-1000-8000-00805f9b34fb"
SHIFT_UP_PATTERN = "f3050301fc"
SHIFT_DOWN_PATTERN = "f3050300fb"
BATTERY_LEVEL_CHARACTERISTIC_UUID = "00002a19-0000-1000-8000-00805f9b34fb"

SHIFT_KEYS = {
 "Up": 'k',
 "Down": 'i'
}

debug = 0

if len(sys.argv) > 1:
    for arg in sys.argv:
        if arg.lower() == "rouvy":
            SHIFT_KEYS = {
              "Up": '+',
              "Down": '-'
            }
        if arg.lower() == "debug":
            debug = 1

# --- Core Logic: Notification Handler Function ---
def handle_notify(sender: BleakGATTCharacteristic, data: bytearray):
    # Log the incoming data
    if (debug):
        print(f"📨 Data from {sender.uuid}: {data.hex()}")
    if data.hex() == SHIFT_UP_PATTERN:
        if (debug):
            print(f"Pressed: {SHIFT_KEYS["Up"]}")
        pyautogui.press(SHIFT_KEYS["Up"])
    elif data.hex() == SHIFT_DOWN_PATTERN:
        if (debug):
            print(f"Pressed: {SHIFT_KEYS["Down"]}")
        pyautogui.press(SHIFT_KEYS["Down"])
    
# --- Main Connection Logic (Unchanged) ---
async def main():
    if platform.system() == "Linux":
        import os
        os.environ["BLESSED_NO_DANGER_RISK"] = "1"
        
    print(f"🔍 Scanning for {DEVICE_NAME}... (waiting for connection)")

    def filter_device(d, ad):
        return d.name and DEVICE_NAME.lower() in d.name.lower()

    device = await BleakScanner.find_device_by_filter(filter_device, timeout=20.0)
    if not device:
        print(f"❌ Device '{DEVICE_NAME}' not found. Make sure it's powered on and near your PC.")
        return

    print(f"✅ Found device: {device.name or 'Unnamed'} ({device.address})")

    try:
        async with BleakClient(device.address) as client:
            print(f"🔗 Connected to {device.name or 'Unnamed'}")
            battery_level = int.from_bytes(await client.read_gatt_char(BATTERY_LEVEL_CHARACTERISTIC_UUID))
            if battery_level > 20:
                print(f"✅ Battery level {battery_level}%")
            else:
                print(f"❌ Battery level {battery_level}%")
            
            print("✅ Subscribing to notifications...")
            
            try:
                await client.start_notify(NOTIFY_UUID, handle_notify)
                print(f"📡 Subscribed to {NOTIFY_UUID}")
            except Exception as e:
                print(f"❌ FAILED to subscribe to notification UUID: {e}. Check device pairing status.")
                return

            print(f"🎧 Listening for shift signals... ")
            print("👋 Press Ctrl+C to stop.")
            
            while client.is_connected:
                await asyncio.sleep(0.1)

    except Exception as e:
        print(f"🛑 An error occurred: {e}")
    finally:
        print("🛑 Disconnected. Stopping listener.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Stopped by user.")
    except RuntimeError as e:
        if "Event loop is closed" not in str(e):
             print(f"🛑 Runtime Error: {e}")
