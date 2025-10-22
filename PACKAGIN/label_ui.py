import tkinter as tk
from tkinter import ttk, messagebox
from zpl_preview import render_preview
from label_ui_external.label_ui_external import show_external_preview
from login_ui import build_login_ui
from database_handler import record_packaging_data

# Global variable to store printer connection
printer_connection = None

def build_main_ui(root, username, serial_num, po_num, printer_conn=None):
    """Enhanced main interface after login"""
    global sku_entry, barcode_entry, qty_entry, lot_entry, preview_label, status_var, printer_connection

    # Store the printer connection passed from serial validation
    printer_connection = printer_conn
    
    if not printer_connection or not printer_connection.is_open:
        messagebox.showwarning("Connection Warning", "⚠️ Printer not connected! Please reconnect if you want to print labels.")

    # Database configuration
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'my_database'
    }

    # --- Clear the root window before building UI ---
    for widget in root.winfo_children():
        widget.destroy()

    # --- Colors and Theme ---
    bg_color = "#1e1e2f"
    card_bg = "#f9f9fb"
    accent = "#0078d7"
    text_color = "#1e1e2f"
    root.configure(bg=bg_color)

    style = ttk.Style()
    style.theme_use("clam")

    # --- Widget Styling ---
    style.configure("Card.TLabelframe", background=card_bg, relief="flat")
    style.configure("Card.TLabelframe.Label", background=card_bg, font=("Segoe UI", 12, "bold"), foreground=accent)
    style.configure("TLabel", background=card_bg, font=("Segoe UI", 11), foreground=text_color)
    style.configure("TEntry", padding=6, font=("Segoe UI", 11))
    style.configure("Accent.TButton",
        font=("Segoe UI", 11, "bold"),
        background=accent,
        foreground="white",
        padding=8
    )
    style.map("Accent.TButton",
        background=[("active", "#005a9e")],
        relief=[("pressed", "sunken")]
    )

    # --- Left Panel: Form Card ---
    form_card = ttk.LabelFrame(
        root,
        text=f"  🏷️  Label Information (User: {username} | Serial: {serial_num})  ",
        padding=25,
        style="Card.TLabelframe"
    )
    form_card.pack(side="left", fill="y", padx=35, pady=30, ipadx=10, ipady=10)

    fields = [
        ("SKU LABEL:", "43000166102"),
        ("BARCODE:", "4341C4300016611002"),
        ("Quantity (pcs):", "2"),
        ("LOT CODE:", po_num)
    ]

    entries = {}
    for i, (label_text, default) in enumerate(fields):
        ttk.Label(form_card, text=label_text).grid(row=i, column=0, sticky="w", pady=12)
        entry = ttk.Entry(form_card, width=35)
        entry.insert(0, default)

        if label_text in ("SKU LABEL:", "LOT CODE:"):
            entry.config(state="readonly")

        entry.grid(row=i, column=1, pady=12, padx=(5, 10))
        entries[label_text] = entry

    sku_entry = entries["SKU LABEL:"]
    barcode_entry = entries["BARCODE:"]
    qty_entry = entries["Quantity (pcs):"]
    lot_entry = entries["LOT CODE:"]

    # --- Live preview updates ---
    for entry in [sku_entry, barcode_entry, qty_entry, lot_entry]:
        entry.bind("<KeyRelease>", lambda e: render_preview(
            sku_entry, barcode_entry, qty_entry, lot_entry, preview_label, status_var
        ))

    # --- Print Label Function ---
    def print_internal_label():
        """Print internal label via existing serial connection"""
        global printer_connection
        
        # Check connection first
        if not printer_connection or not printer_connection.is_open:
            messagebox.showerror("Connection Error", "❌ Printer not connected!\n\nPlease use 'Scan Next' to reconnect.")
            return

        # Import ZPL template first
        from zpl_code import zpl_code

        # Collect input field values
        sku = sku_entry.get().strip()
        barcode = barcode_entry.get().strip()
        qty = qty_entry.get().strip()
        lot = lot_entry.get().strip()

        # Validate fields
        if not all([sku, barcode, qty, lot]):
            messagebox.showwarning("Missing Information", "Please fill in all fields!")
            return

        # ✅ Generate ZPL with current data BEFORE sending
        zpl_filled = zpl_code.replace("43000166102", sku)
        zpl_filled = zpl_filled.replace("4341C4300016611002", barcode)
        zpl_filled = zpl_filled.replace("^FO750,1050^FD10^FS", f"^FO750,1050^FD{qty}^FS")
        zpl_filled = zpl_filled.replace("^FO920,980^FD10^FS", f"^FO920,980^FD{qty}^FS")
        # Add more replacements as needed

        try:
            status_var.set("⏳ Sending to printer...")
            root.update()

            # ✅ Now send it after defining zpl_filled
            printer_connection.write(zpl_filled.encode('utf-8'))
            printer_connection.flush()

            status_var.set(f"✅ Internal label printed | SKU: {sku}")
            messagebox.showinfo("Success", f"✅ Internal label sent to printer!\n\nSKU: {sku}\nQTY: {qty}")

        except Exception as e:
            status_var.set("❌ Print failed")
            messagebox.showerror("Print Error", f"Failed to print:\n\n{str(e)}\n\nConnection may be lost. Please 'Scan Next' to reconnect.")

    # --- Enhanced Submit Function ---
    def handle_submit():
        """Handle submit button with confirmation and database recording"""
        sku = sku_entry.get()
        qty = qty_entry.get()
        lot = lot_entry.get()
        
        if not all([sku, qty, lot]):
            messagebox.showwarning("Missing Information", "Please fill in all fields!")
            return
        
        confirm_msg = f"Confirm Submission:\n\n" \
                     f"Serial Number: {serial_num}\n" \
                     f"SKU: {sku}\n" \
                     f"Quantity: {qty} pcs\n" \
                     f"PO Number (LOT): {lot}\n\n" \
                     f"Proceed to record and generate external label?"
        
        if messagebox.askyesno("Confirm Submission", confirm_msg):
            result = record_packaging_data(lot, serial_num, sku, qty, po_num, db_config)
            
            if result["success"]:
                messagebox.showinfo("Success", 
                    f"{result['message']}\n\n"
                    f"Serial: {serial_num}\n"
                    f"SKU: {sku}\n"
                    f"QTY: {qty}\n"
                    f"PO Number: {lot}\n\n"
                    f"Status updated in both faceware_main and faceware_packaging1"
                )
                # Pass printer connection to external preview
                show_external_preview(root, sku, lot, qty, serial_num, printer_connection)
            elif result.get("already_submitted"):
                existing_sku = result.get("existing_sku", sku)
                existing_qty = result.get("existing_qty", qty)
                
                reprint = messagebox.askyesno(
                    "Already Submitted",
                    f"⚠️ Packaging 1 Already Submitted!\n\n"
                    f"Serial Number: {serial_num}\n"
                    f"PO Number: {lot}\n"
                    f"Existing SKU: {existing_sku}\n"
                    f"Existing QTY: {existing_qty}\n\n"
                    f"Do you want to print the external label?"
                )
                
                if reprint:
                    show_external_preview(root, existing_sku, lot, existing_qty, serial_num, printer_connection)
            else:
                messagebox.showwarning("Warning", 
                    f"{result['message']}\n\n"
                    f"Proceeding to label preview anyway..."
                )
                show_external_preview(root, sku, lot, qty, serial_num, printer_connection)

    # --- Buttons Frame ---
    btn_frame = ttk.Frame(form_card, style="Card.TFrame")
    btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=(25, 10))

    ttk.Button(
        btn_frame,
        text="🖨️ Print Label",
        command=print_internal_label,
        style="Accent.TButton"
    ).grid(row=0, column=0, padx=6)

    ttk.Button(
        btn_frame,
        text="📤 Submit",
        command=handle_submit,
        style="Accent.TButton"
    ).grid(row=0, column=1, padx=6)

    ttk.Button(
        btn_frame,
        text="🔄 Scan Next",
        command=lambda: scan_next(root, username, printer_connection),
        style="Accent.TButton"
    ).grid(row=0, column=2, padx=6)

    ttk.Button(
        btn_frame,
        text="🚪 Logout",
        command=lambda: logout_user(root, printer_connection),
        style="Accent.TButton"
    ).grid(row=0, column=3, padx=6)

    # --- Separator line ---
    ttk.Separator(form_card, orient="horizontal").grid(row=len(fields)+1, column=0, columnspan=2, sticky="ew", pady=15)

    # --- Right Panel: Preview Section ---
    preview_card = ttk.Frame(root, padding=20)
    preview_card.pack(side="right", expand=True, fill="both", padx=35, pady=30)

    ttk.Label(
        preview_card,
        text="🖼️ Internal Label Preview",
        font=("Segoe UI", 14, "bold"),
        foreground=accent,
        background=bg_color
    ).pack(anchor="w", pady=(0, 10))

    preview_label = ttk.Label(
        preview_card,
        text="Preview will appear here...",
        anchor="center",
        background="white",
        relief="ridge",
        borderwidth=3,
        font=("Segoe UI", 12),
        padding=20
    )
    preview_label.pack(expand=True, fill="both", padx=10, pady=10)

    # Connection status indicator
    conn_status = "🟢 Connected" if (printer_connection and printer_connection.is_open) else "🔴 Disconnected"
    status_var = tk.StringVar(value=f"{conn_status} | Serial: {serial_num} | PO: {po_num}")
    status_bar = tk.Label(
        root,
        textvariable=status_var,
        anchor="w",
        bg=accent,
        fg="white",
        font=("Segoe UI", 10, "italic"),
        padx=10,
        pady=6
    )
    status_bar.pack(side="bottom", fill="x")

    # --- Initial Preview Render ---
    render_preview(sku_entry, barcode_entry, qty_entry, lot_entry, preview_label, status_var)

def scan_next(root, username, printer_conn):
    confirm = messagebox.askyesno("Scan Next", "Do you want to scan another serial number?")
    if confirm:
        for widget in root.winfo_children():
            widget.destroy()
        from serial_validation.main import SerialValidation
        
        # Create validation normally
        validation = SerialValidation(root, username, build_main_ui)
        
        # Restore the existing connection
        if printer_conn and printer_conn.is_open:
            validation.ui.connection = printer_conn
            validation.ui.set_status(f"✅ Connection maintained", "green")
            validation.ui.connect_btn.config(text="🔌 Connected", bg="#28a745")

def logout_user(root, printer_conn):
    """Clear UI and return to login screen"""
    confirm = messagebox.askyesno("Logout", "Are you sure you want to logout?")
    if confirm:
        # Close printer connection on logout
        if printer_conn and printer_conn.is_open:
            printer_conn.close()
        
        for widget in root.winfo_children():
            widget.destroy()
        from login_ui import build_login_ui
        from serial_validation.main import SerialValidation
        build_login_ui(root, lambda r, u: SerialValidation(r, u, build_main_ui))