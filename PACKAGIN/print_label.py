# PACKAGING/print_label.py
import serial
import serial.tools.list_ports
from tkinter import messagebox

def send_zpl_to_serial(zpl_code, com_port, baudrate=19200, timeout=1):
    """
    Send ZPL code directly to Zebra printer via COM port.
    
    Args:
        zpl_code (str): The ZPL command string.
        com_port (str): The COM port to send the data (e.g., 'COM3').
        baudrate (int): The baud rate (default: 19200).
        timeout (int): The read timeout (default: 1 second).

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        with serial.Serial(com_port, baudrate=baudrate, timeout=timeout) as printer:
            printer.write(zpl_code.encode('utf-8'))
            printer.flush()
        return True, f"Label successfully sent to {com_port}"
    except serial.SerialException as e:
        return False, f"Serial communication error: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"

def generate_zpl_code(sku, barcode, quantity, lot):
    """
    Generate ZPL code for the label (adjusted for ZT410 600dpi printer)
    """
    zpl = f"""^XA
^MMT
^PW812
^LL1218
^LS0
^FT50,100^A0N,50,50^FH^FD{sku}^FS
^BY3,3,100^FT50,250^BCN,,Y,N
^FD{barcode}^FS
^FT50,400^A0N,40,40^FH^FDQTY: {quantity} pcs^FS
^FT50,500^A0N,40,40^FH^FDLOT: {lot}^FS
^XZ"""
    return zpl

def print_label(sku_entry, barcode_entry, qty_entry, lot_entry, status_var, connected_port=None):
    """
    Automatically print label through connected COM port (no IP dialog).
    If no COM port is specified, tries to auto-detect the first available port.
    """
    sku = sku_entry.get()
    barcode = barcode_entry.get()
    qty = qty_entry.get()
    lot = lot_entry.get()

    # Validate inputs
    if not all([sku, barcode, qty, lot]):
        messagebox.showwarning("Missing Information", "Please fill in all fields!")
        return

    # Determine which COM port to use
    if not connected_port:
        ports = [p.device for p in serial.tools.list_ports.comports()]
        if not ports:
            messagebox.showerror("No Printer Found", "⚠️ No COM ports available.")
            return
        connected_port = ports[0]  # use first detected COM automatically

    # Generate ZPL
    zpl_code = generate_zpl_code(sku, barcode, qty, lot)

    # Update status
    status_var.set(f"⏳ Sending label to {connected_port}...")

    # Send to serial printer
    success, message = send_zpl_to_serial(zpl_code, connected_port)

    if success:
        status_var.set(f"✅ {message}")
        messagebox.showinfo("Success", message)
    else:
        status_var.set("❌ Print failed")
        messagebox.showerror("Print Error", message)
