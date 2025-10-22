import tkinter as tk
from tkinter import messagebox, ttk
import requests
from zpl_code_external import zpl_external
from PIL import Image, ImageTk
from io import BytesIO
from database_handler2 import record_packaging_data

# --- Database Config ---
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'my_database'
}

def show_external_preview(root, sku, lot, qty, serial_num, printer_connection):
    """Open new GUI to show ZPL External Preview with updated values"""
    try:
        # Update ZPL template with dynamic data
        zpl_filled = zpl_external.replace("43000166102", sku)
        zpl_filled = zpl_filled.replace("4341C", lot)
        zpl_filled = zpl_filled.replace("^FO750,1050^FD10^FS", f"^FO750,1050^FD{qty}^FS")
        zpl_filled = zpl_filled.replace("^FO920,980^FD10^FS", f"^FO920,980^FD{qty}^FS")

        # Create preview window
        new_win = tk.Toplevel(root)
        new_win.title("External Label Preview")
        new_win.geometry("800x700")
        new_win.configure(bg="#16213e")

        # Loading message
        loading_label = tk.Label(
            new_win, text="⏳ Generating preview...",
            bg="#16213e", fg="white", font=("Segoe UI", 12)
        )
        loading_label.pack(expand=True)
        new_win.update()

        # Render image via Labelary API
        ZEBRA_API = "https://api.labelary.com/v1/printers/24dpmm/labels/5.512x3.465/0/"
        headers = {"Accept": "image/png"}
        response = requests.post(ZEBRA_API, headers=headers, data=zpl_filled.encode("utf-8"), timeout=10)

        loading_label.destroy()

        if response.status_code == 200:
            info_frame = tk.Frame(new_win, bg="#0078d7", height=60)
            info_frame.pack(fill="x", pady=(0, 10))
            info_label = tk.Label(
                info_frame,
                text=f"External Label | SKU: {sku} | LOT: {lot} | QTY: {qty}",
                bg="#0078d7", fg="white", font=("Segoe UI", 13, "bold")
            )
            info_label.pack(expand=True)

            # Display image
            image = Image.open(BytesIO(response.content))
            display_width = 700
            aspect_ratio = image.height / image.width
            display_height = int(display_width * aspect_ratio)
            image = image.resize((display_width, display_height), Image.LANCZOS)
            img_tk = ImageTk.PhotoImage(image)

            preview_label = tk.Label(new_win, image=img_tk, bg="white")
            preview_label.image = img_tk
            preview_label.pack(expand=True, fill="both", padx=20, pady=(10, 20))

            # Buttons
            btn_frame = tk.Frame(new_win, bg="#16213e")
            btn_frame.pack(pady=(0, 20))

            # Print using existing connection
            tk.Button(
                btn_frame, text="🖨️ Print External Label",
                command=lambda: print_external_label(zpl_filled, new_win, sku, lot, qty, printer_connection),
                font=("Segoe UI", 11, "bold"), bg="#0078d7", fg="white",
                padx=25, pady=10, relief="flat", cursor="hand2"
            ).pack(side="left", padx=10)

            # Submit (update database)
            tk.Button(
                btn_frame, text="✅ Submit",
                command=lambda: handle_submit_packaging2(new_win, serial_num, sku, qty, lot),
                font=("Segoe UI", 11, "bold"), bg="#28a745", fg="white",
                padx=25, pady=10, relief="flat", cursor="hand2"
            ).pack(side="left", padx=10)

            # Close
            tk.Button(
                btn_frame, text="❌ Close", command=new_win.destroy,
                font=("Segoe UI", 11), bg="#555", fg="white",
                padx=25, pady=10, relief="flat", cursor="hand2"
            ).pack(side="left", padx=10)

        else:
            tk.Label(
                new_win,
                text=f"❌ Error rendering ZPL\nStatus Code: {response.status_code}",
                bg="#16213e", fg="white", font=("Segoe UI", 12), justify="center"
            ).pack(expand=True, pady=20)

    except Exception as e:
        messagebox.showerror("Error", f"⚠️ {str(e)}")
        if 'new_win' in locals():
            new_win.destroy()

def print_external_label(zpl_code, parent_window, sku, lot, qty, printer_connection):
    """Print external label using existing serial connection"""
    if not printer_connection or not printer_connection.is_open:
        messagebox.showerror("Connection Error", "❌ Printer not connected!\n\nPlease use 'Scan Next' to reconnect.")
        return
    
    confirm = messagebox.askyesno(
        "Confirm Print",
        f"Print External Label?\n\n"
        f"SKU: {sku}\n"
        f"LOT: {lot}\n"
        f"QTY: {qty}\n\n"
        f"Send to printer?"
    )
    
    if confirm:
        try:
            # Send ZPL code using existing connection
            printer_connection.write(zpl_code.encode('utf-8'))
            printer_connection.flush()
            
            messagebox.showinfo(
                "Success",
                f"✅ External label sent to printer!\n\n"
                f"SKU: {sku}\n"
                f"LOT: {lot}\n"
                f"QTY: {qty}"
            )
            
        except Exception as e:
            messagebox.showerror("Print Error", f"Failed to print:\n\n{str(e)}\n\nConnection may be lost. Please use 'Scan Next' to reconnect.")

def handle_submit_packaging2(new_win, serial_num, sku, qty, lot):
    """Handle submit button with confirmation and database recording"""
    confirm_msg = f"Confirm External Label Submission:\n\n" \
                 f"Serial Number: {serial_num}\n" \
                 f"LOT/PO Number: {lot}\n" \
                 f"SKU: {sku}\n" \
                 f"Quantity: {qty} pcs\n\n" \
                 f"Proceed to update Packaging 2 status?"
    
    if messagebox.askyesno("Confirm Submission", confirm_msg):
        result = record_packaging_data(serial_num, sku, qty, db_config)
        
        if result["success"]:
            messagebox.showinfo("Success ✅", 
                f"{result['message']}\n\n"
                f"Serial: {serial_num}\n"
                f"LOT/PO: {lot}\n"
                f"SKU: {sku}\n"
                f"QTY: {qty}\n\n"
                f"Status updated in both faceware_main and faceware_packaging2"
            )
            new_win.destroy()
        elif result.get("already_submitted"):
            existing_sku = result.get("existing_sku", sku)
            existing_qty = result.get("existing_qty", qty)
            
            messagebox.showinfo(
                "Already Submitted",
                f"⚠️ Packaging 2 Already Submitted!\n\n"
                f"Serial Number: {serial_num}\n"
                f"LOT/PO Number: {lot}\n"
                f"Existing SKU: {existing_sku}\n"
                f"Existing QTY: {existing_qty}\n\n"
                f"No changes made to the database."
            )
        else:
            messagebox.showerror("Failed ❌", result["message"])