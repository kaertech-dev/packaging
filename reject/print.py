import serial
import time
import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import requests
from PIL import Image, ImageTk
from io import BytesIO
import re

# Serial port settings
SERIAL_PORT = 'COM5'
BAUDRATE = 9600
TIMEOUT = 2

# Default PRN file path
DEFAULT_PRN_PATH = r"C:\Users\cadetautomation\Documents\packagin\Code 128 Inner carton label for face shield (Rose Gold, US version).nlbl"
preview_image = None

def read_prn_as_zpl(file_path):
    """Read PRN file and try to extract or convert ZPL text."""
    if not os.path.exists(file_path):
        messagebox.showerror("File Error", f"File not found:\n{file_path}")
        return None

    try:
        with open(file_path, 'rb') as f:
            content = f.read()

        # Try decode (ignore binary noise)
        text = content.decode('utf-8', errors='ignore')

        # Check if already ZPL
        if '^XA' in text and '^XZ' in text:
            print("✅ Detected ZPL format in PRN file.")
            return text

        # If not, attempt minimal conversion:
        # Extract ZPL-like sequences from printable ASCII
        possible_zpl = ''.join(
            ch if 32 <= ord(ch) <= 126 or ch in '\n\r\t' else ''
            for ch in text
        )

        if '^XA' in possible_zpl:
            print("⚙️ Cleaned ZPL extracted from PRN file.")
            return possible_zpl

        # If not ZPL-like at all:
        messagebox.showwarning(
            "Unsupported PRN",
            "The selected .PRN file doesn't appear to be in ZPL format.\n"
            "It may be a non-Zebra print language (EPL, CPCL, or PCL)."
        )
        return None

    except Exception as e:
        messagebox.showerror("Read Error", f"Error reading PRN file:\n{e}")
        return None

def send_zpl_to_printer(zpl):
    """Send ZPL to Zebra printer via serial."""
    try:
        with serial.Serial(SERIAL_PORT, BAUDRATE, timeout=TIMEOUT) as printer:
            printer.write(zpl.encode('utf-8'))
            printer.flush()
        time.sleep(1)
        messagebox.showinfo("Success", "✅ ZPL command sent successfully.")
    except Exception as e:
        messagebox.showerror("Serial Error", f"Error sending ZPL:\n{e}")

def detect_printer_dpi():
    """Detect printer DPI via ~HS command over serial."""
    try:
        with serial.Serial(SERIAL_PORT, BAUDRATE, timeout=2) as printer:
            printer.write(b'~HS\n')
            time.sleep(0.5)
            response = printer.read_all().decode(errors='ignore')

        match = re.search(r"[DE]:\s*(\d{3})", response)
        if match:
            dpi = int(match.group(1))
            print(f"🖨️ Detected printer DPI: {dpi}")
            return dpi
        else:
            print("⚠️ Could not detect DPI from ~HS response. Defaulting to 600.")
            print(response)
            return 600
    except Exception as e:
        print(f"⚠️ DPI detection failed: {e}")
        return 600

def extract_label_size(zpl_text):
    """
    Attempt to detect label dimensions (^PW or ^LL) in ZPL.
    If not found, return a safe fallback (4x6 inches).
    Caps output to Labelary maximum 15x15 inches.
    """
    width = 4
    height = 6  # Default fallback 4x6 inches

    pw_match = re.search(r"\^PW(\d+)", zpl_text)
    ll_match = re.search(r"\^LL(\d+)", zpl_text)
    
    DPI = detect_printer_dpi()  # Get printer DPI
    # Convert dots to inches (8dpmm = 203 dpi)
    if pw_match:
        width = round(int(pw_match.group(1)) / DPI, 2)
    if ll_match:
        height = round(int(ll_match.group(1)) / DPI, 2)

    # Sanity check and clamp to Labelary limits
    width = max(0.5, min(width, 15.0))
    height = max(0.5, min(height, 15.0))

    return width, height


def load_file():
    """Load a .PRN file and show its ZPL content."""
    file_path = filedialog.askopenfilename(filetypes=[("PRN files", "*.prn"), ("All files", "*.*")])
    if file_path:
        zpl = read_prn_as_zpl(file_path)
        if zpl:
            text_area.delete(1.0, tk.END)
            text_area.insert(tk.END, zpl)


def print_label():
    """Send current ZPL text to printer."""
    zpl_body = text_area.get(1.0, tk.END).strip()
    if not zpl_body:
        messagebox.showwarning("Empty Label", "ZPL content is empty.")
        return

    darkness = darkness_var.get()
    speed = speed_var.get()
    zpl = f"^XA\n^MD{darkness}\n^PR{speed}\n{zpl_body}\n^XZ"
    send_zpl_to_printer(zpl)

def preview_zpl():
    """Generate a full-size ZPL preview using Labelary."""
    global preview_image

    zpl_body = text_area.get(1.0, tk.END).strip()
    if not zpl_body:
        messagebox.showwarning("Empty Label", "ZPL content is empty.")
        return

    darkness = darkness_var.get()
    speed = speed_var.get()
    zpl = f"^XA\n^MD{darkness}\n^PR{speed}\n{zpl_body}\n^XZ"

    width_in, height_in = extract_label_size(zpl)

    try:
        # Labelary API URL with adjusted size
        dpmm = round(detect_printer_dpi() / 25.4)  # convert dpi → dots per mm
        url = f"http://api.labelary.com/v1/printers/{dpmm}dpmm/labels/{width_in}x{height_in}/0/"

        response = requests.post(
            url,
            headers={'Accept': 'image/png'},
            data=zpl.encode('utf-8')
        )

        if response.status_code == 200:
            img_data = BytesIO(response.content)
            img = Image.open(img_data)

            # Resize dynamically to fit canvas
            canvas_width = preview_canvas.winfo_width()
            canvas_height = preview_canvas.winfo_height()
            img.thumbnail((canvas_width, canvas_height), Image.Resampling.LANCZOS)

            preview_image = ImageTk.PhotoImage(img)
            preview_canvas.delete("all")
            preview_canvas.create_image(
                canvas_width // 2,
                canvas_height // 2,
                anchor=tk.CENTER,
                image=preview_image
            )
        else:
            messagebox.showerror(
                "Preview Error",
                f"Labelary returned status {response.status_code}\n\n"
                f"Width={width_in} in, Height={height_in} in\n"
                f"Details: {response.text}"
            )

    except Exception as e:
        messagebox.showerror("Preview Error", f"Error generating preview:\n{e}")


# GUI setup
root = tk.Tk()
root.title("Editable ZPL Label Printer")
root.geometry("950x950")

tk.Button(root, text="Load PRN File", command=load_file).pack(pady=10)

text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Courier", 10))
text_area.pack(expand=True, fill='both', padx=10, pady=10)

# Controls for print parameters
control_frame = tk.Frame(root)
control_frame.pack(pady=5)

tk.Label(control_frame, text="Darkness (0–30):").grid(row=0, column=0, padx=5)
darkness_var = tk.IntVar(value=10)
tk.Entry(control_frame, textvariable=darkness_var, width=5).grid(row=0, column=1)

tk.Label(control_frame, text="Speed (1–30):").grid(row=0, column=2, padx=5)
speed_var = tk.IntVar(value=2)
tk.Entry(control_frame, textvariable=speed_var, width=5).grid(row=0, column=3)

tk.Button(root, text="Send to Printer", command=print_label).pack(pady=10)
tk.Button(root, text="Preview ZPL", command=preview_zpl).pack(pady=5)

# Preview canvas (large)
preview_canvas = tk.Canvas(root, width=800, height=800, bg="white")
preview_canvas.pack(pady=5)

# Load default file on startup
default_zpl = read_prn_as_zpl(DEFAULT_PRN_PATH)
if default_zpl:
    text_area.insert(tk.END, default_zpl)

root.mainloop()
