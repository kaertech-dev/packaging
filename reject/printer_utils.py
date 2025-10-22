#PACKAGIN/printer_utils.py
import serial
import time
import re
from tkinter import messagebox

# Import configuration
from config import SERIAL_PORT, BAUDRATE, TIMEOUT

def send_zpl_to_printer(zpl: str):
    """Send ZPL to Zebra printer via serial."""
    try:
        with serial.Serial(SERIAL_PORT, BAUDRATE, timeout=TIMEOUT) as printer:
            printer.write(zpl.encode('utf-8'))
            printer.flush()
        time.sleep(1)
        messagebox.showinfo("Success", "ZPL command sent successfully.")
    except Exception as e:
        messagebox.showerror("Serial Error", f"Error sending ZPL:\n{e}")

def detect_printer_dpi() -> int:
    """Detect printer DPI via ~HS command over serial."""
    try:
        with serial.Serial(SERIAL_PORT, BAUDRATE, timeout=2) as printer:
            printer.write(b'~HS\n')
            time.sleep(0.5)
            response = printer.read_all().decode(errors='ignore')

        match = re.search(r"[DE]:\s*(\d{3})", response)
        if match:
            dpi = int(match.group(1))
            print(f"Detected printer DPI: {dpi}")
            return dpi
        else:
            print("Could not detect DPI from ~HS response. Defaulting to 600.")
            return 600
    except Exception as e:
        print(f"DPI detection failed: {e}")
        return 600
