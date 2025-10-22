# PACKAGIN/label_ui_external/print_label_external.py
import tkinter as tk
from tkinter import messagebox
import socket
def send_zpl_to_printer(zpl_code, printer_ip="192.168.1.100", printer_port=9100):
    """
    Send ZPL code directly to Zebra printer
    
    Args:
        zpl_code: The ZPL string to print
        printer_ip: IP address of the Zebra printer
        printer_port: Port number (default: 9100 for Zebra printers)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Create socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # 5 second timeout
        
        # Connect to printer
        sock.connect((printer_ip, printer_port))
        
        # Send ZPL code
        sock.sendall(zpl_code.encode('utf-8'))
        
        # Close connection
        sock.close()
        
        return True, "Print job sent successfully!"
        
    except socket.timeout:
        return False, "Connection timeout. Check if printer is online."
    except socket.error as e:
        return False, f"Connection error: {str(e)}\nCheck printer IP address and network."
    except Exception as e:
        return False, f"Error: {str(e)}"

def print_external_label(zpl_code, parent_window, sku, lot, qty, printer_connection):
    """Handle print button click for external label"""
    if not printer_connection or not printer_connection.is_open:
        messagebox.showerror("Connection Error", "Please reconnect!")
        return
    
    # Just confirm and print - no COM port selection needed!
    if messagebox.askyesno("Confirm Print", f"Print label?\nSKU: {sku}"):
        printer_connection.write(zpl_code.encode('utf-8'))
        printer_connection.flush()
        printer_connection.close()
    # Show printer IP dialog
    ip_dialog = tk.Toplevel(parent_window)
    ip_dialog.title("Printer Settings")
    ip_dialog.geometry("450x180")
    ip_dialog.configure(bg="#16213e")
    ip_dialog.transient(parent_window)
    ip_dialog.grab_set()
    
    # Center the dialog
    ip_dialog.update_idletasks()
    x = parent_window.winfo_x() + (parent_window.winfo_width() // 2) - (ip_dialog.winfo_width() // 2)
    y = parent_window.winfo_y() + (parent_window.winfo_height() // 2) - (ip_dialog.winfo_height() // 2)
    ip_dialog.geometry(f"+{x}+{y}")
    
    tk.Label(
        ip_dialog, 
        text="Zebra ZT410 Printer IP Address:", 
        font=("Segoe UI", 11),
        bg="#16213e",
        fg="white"
    ).pack(pady=(20, 5))
    
    ip_var = tk.StringVar(value="192.168.1.100")
    ip_entry = tk.Entry(
        ip_dialog, 
        textvariable=ip_var, 
        width=30, 
        font=("Segoe UI", 11),
        bg="white",
        fg="black"
    )
    ip_entry.pack(pady=10, padx=20)
    
    status_label = tk.Label(
        ip_dialog,
        text="",
        font=("Segoe UI", 9),
        bg="#16213e",
        fg="yellow"
    )
    status_label.pack(pady=5)
    
    def confirm_print():
        printer_ip = ip_var.get()
        
        if not printer_ip:
            messagebox.showwarning("Invalid IP", "Please enter a printer IP address!")
            return
        
        status_label.config(text="⏳ Sending to printer...", fg="yellow")
        ip_dialog.update()
        
        # Send to printer
        success, message = send_zpl_to_printer(zpl_code, printer_ip)
        
        if success:
            status_label.config(text=f"✅ {message}", fg="lightgreen")
            messagebox.showinfo(
                "Success", 
                f"External label sent to printer at {printer_ip}\n\nSKU: {sku}\nLOT: {lot}\nQTY: {qty}"
            )
            ip_dialog.destroy()
        else:
            status_label.config(text="❌ Print failed", fg="red")
            messagebox.showerror("Print Error", message)
    
    # Button frame
    btn_frame = tk.Frame(ip_dialog, bg="#16213e")
    btn_frame.pack(pady=15)
    
    print_btn = tk.Button(
        btn_frame,
        text="🖨️ Print",
        command=confirm_print,
        font=("Segoe UI", 10, "bold"),
        bg="#0078d7",
        fg="white",
        padx=20,
        pady=8,
        relief="flat",
        cursor="hand2"
    )
    print_btn.pack(side="left", padx=5)
    
    cancel_btn = tk.Button(
        btn_frame,
        text="Cancel",
        command=ip_dialog.destroy,
        font=("Segoe UI", 10),
        bg="#444",
        fg="white",
        padx=20,
        pady=8,
        relief="flat",
        cursor="hand2"
    )
    cancel_btn.pack(side="left", padx=5)