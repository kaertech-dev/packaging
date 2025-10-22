# PACKAGING/serial_validation.py
import tkinter as tk
from tkinter import messagebox, Frame, Label, Entry, Button
import mysql.connector
from mysql.connector import Error

class SerialValidationGUI:
    def __init__(self, parent, username, on_success_callback):
        """
        Serial Number Validation Window
        
        Args:
            parent: Parent window (root)
            username: Logged-in username
            on_success_callback: Function to call on successful validation with (root, username, serial_num, lot_code)
        """
        self.parent = parent
        self.username = username
        self.on_success_callback = on_success_callback
        
        # Database configuration
        self.db_config = {
            'host': '192.168.1.38',
            'user': 'readonly_user',
            'password': 'kts@tsd2025',
            'database': 'ledtech'
        }
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the validation window UI"""
        # Main container frame (replaces login container)
        self.container = Frame(self.parent, bg="#16213e")
        self.container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Card frame (white box with padding)
        self.card = Frame(self.container, bg="#f4f5f7", bd=0, relief="flat")
        self.card.grid(row=0, column=0, padx=20, pady=20, ipadx=30, ipady=20)
        
        # Title
        title_label = Label(
            self.card,
            text="🔍 Serial Number Validation",
            font=("Segoe UI", 18, "bold"),
            bg="#f4f5f7",
            fg="#16213e"
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(10, 10))
        
        # Subtitle with username
        subtitle_label = Label(
            self.card,
            text=f"Logged in as: {self.username}",
            font=("Segoe UI", 10),
            bg="#f4f5f7",
            fg="#666"
        )
        subtitle_label.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        # Serial Number Label
        Label(
            self.card,
            text="Serial Number:",
            font=("Segoe UI", 11, "bold"),
            bg="#f4f5f7"
        ).grid(row=2, column=0, sticky="e", padx=(10, 5), pady=10)
        
        # Serial Number Entry
        self.serial_var = tk.StringVar()
        self.serial_entry = Entry(
            self.card,
            textvariable=self.serial_var,
            font=("Segoe UI", 11),
            width=28,
            relief="solid",
            bd=1
        )
        self.serial_entry.grid(row=2, column=1, pady=10, padx=(0, 10))
        self.serial_entry.focus()
        
        # Bind Enter key to validate
        self.parent.bind('<Return>', lambda e: self.validate_serial())
        
        # Status label
        self.status_label = Label(
            self.card,
            text="",
            font=("Segoe UI", 9),
            bg="#f4f5f7",
            fg="#d9534f"
        )
        self.status_label.grid(row=3, column=0, columnspan=2, pady=(5, 10))
        
        # Button frame
        btn_frame = Frame(self.card, bg="#f4f5f7")
        btn_frame.grid(row=4, column=0, columnspan=2, pady=(10, 10))
        
        validate_btn = Button(
            btn_frame,
            text="✓ Validate & Continue",
            command=self.validate_serial,
            font=("Segoe UI", 11, "bold"),
            bg="#0f3460",
            fg="white",
            padx=20,
            pady=8,
            relief="flat",
            cursor="hand2",
            activebackground="#1a508b"
        )
        validate_btn.pack(side="left", padx=5)
        
        cancel_btn = Button(
            btn_frame,
            text="Logout",
            command=self.cancel,
            font=("Segoe UI", 11),
            bg="#666",
            fg="white",
            padx=20,
            pady=8,
            relief="flat",
            cursor="hand2",
            activebackground="#888"
        )
        cancel_btn.pack(side="left", padx=5)
    
    def validate_serial(self):
        """Validate serial number against database"""
        serial_num = self.serial_var.get().strip()
        
        if not serial_num:
            self.status_label.config(text="❌ Please enter a serial number!", fg="#d9534f")
            return
        
        self.status_label.config(text="⏳ Validating serial number...", fg="#f0ad4e")
        self.parent.update()
        
        try:
            # Connect to database
            connection = mysql.connector.connect(**self.db_config)
            
            if connection.is_connected():
                cursor = connection.cursor(dictionary=True)
                
                # Query to fetch batch_code for the given serial_num
                query = """
                    SELECT serial_num, batch_code 
                    FROM faceware_assembly1 
                    WHERE serial_num = %s
                """
                cursor.execute(query, (serial_num,))
                result = cursor.fetchone()
                
                cursor.close()
                connection.close()
                
                if result:
                    lot_code = result['batch_code']
                    
                    self.status_label.config(
                        text=f"✅ Valid! LOT: {lot_code}", 
                        fg="#5cb85c"
                    )
                    
                    # Success - call the callback after a brief delay
                    self.parent.after(800, lambda: self.success(serial_num, lot_code))
                else:
                    self.status_label.config(
                        text="❌ Serial number not found in database", 
                        fg="#d9534f"
                    )
                    messagebox.showerror(
                        "Invalid Serial Number",
                        f"Serial number '{serial_num}' not found in database.\n\nPlease verify and try again."
                    )
        
        except Error as e:
            self.status_label.config(text="❌ Database connection error", fg="#d9534f")
            messagebox.showerror(
                "Database Error",
                f"Failed to connect to database:\n\n{str(e)}\n\nPlease check your network connection."
            )
        except Exception as e:
            self.status_label.config(text="❌ Error occurred", fg="#d9534f")
            messagebox.showerror("Error", f"An unexpected error occurred:\n\n{str(e)}")
    
    def success(self, serial_num, lot_code):
        """Handle successful validation"""
        # Remove the container
        self.container.destroy()
        
        # Unbind Enter key
        self.parent.unbind('<Return>')
        
        # Call the success callback with all needed data
        self.on_success_callback(self.parent, self.username, serial_num, lot_code)
    
    def cancel(self):
        """Handle logout - return to login screen"""
        if messagebox.askokcancel("Logout", "Are you sure you want to logout?"):
            self.container.destroy()
            self.parent.unbind('<Return>')
            # Import and rebuild login UI
            from login_ui import build_login_ui
            build_login_ui(self.parent, lambda root, username: show_serial_validation(root, username, self.on_success_callback))


def show_serial_validation(root, username, on_label_ui_callback):
    """
    Show serial validation screen after successful login
    
    Args:
        root: The main window
        username: Logged-in username
        on_label_ui_callback: Function to call with (root, username, serial_num, lot_code)
    """
    SerialValidationGUI(root, username, on_label_ui_callback)


# ===== UPDATED LOGIN UI =====
# PACKAGING/login_ui.py (REPLACE YOUR ENTIRE FILE WITH THIS)

"""
import re
from tkinter import ttk, messagebox, Frame
from serial_validation import show_serial_validation

def build_login_ui(root, on_success):
    '''Enhanced login UI with modern design and validation'''
    # Root background
    root.configure(bg="#16213e")

    # --- Main container frame ---
    container = Frame(root, bg="#16213e")
    container.place(relx=0.5, rely=0.5, anchor="center")

    # --- Card frame (white box with padding) ---
    card = Frame(container, bg="#f4f5f7", bd=0, relief="flat")
    card.grid(row=0, column=0, padx=20, pady=20, ipadx=30, ipady=20)

    # --- Title ---
    ttk.Label(
        card,
        text="🔒 Login to ZPL Editor",
        font=("Segoe UI", 18, "bold"),
        background="#f4f5f7",
        foreground="#16213e"
    ).grid(row=0, column=0, columnspan=2, pady=(10, 25))

    # --- ID Label ---
    ttk.Label(
        card,
        text="User ID:",
        font=("Segoe UI", 11, "bold"),
        background="#f4f5f7"
    ).grid(row=1, column=0, sticky="e", padx=(10, 5), pady=10)

    # --- ID Entry ---
    username_entry = ttk.Entry(card, width=28, font=("Segoe UI", 11))
    username_entry.grid(row=1, column=1, pady=10, padx=(0, 10))
    username_entry.focus()

    # --- Login button ---
    login_btn = ttk.Button(
        card,
        text="Login",
        command=lambda: check_login(),
        style="Login.TButton"
    )
    login_btn.grid(row=3, column=0, columnspan=2, pady=(20, 10), ipadx=10)

    # --- Style customization ---
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Login.TButton",
        font=("Segoe UI", 11, "bold"),
        foreground="white",
        background="#0f3460",
        padding=8
    )
    style.map(
        "Login.TButton",
        background=[("active", "#1a508b")],
        relief=[("pressed", "sunken")]
    )

    style.configure("TEntry", padding=5)

    # --- Validation logic ---
    def check_login():
        username = username_entry.get().strip()

        if not username:
            messagebox.showerror("Login Failed", "❌ ID cannot be empty.")
        elif re.match(r"^KE\d{4}$", username) or re.match(r"^LL\d{4}$", username):
            messagebox.showinfo("Login Successful", f"Welcome, {username}!")
            container.destroy()
            root.unbind("<Return>")
            # Show serial validation instead of directly calling on_success
            show_serial_validation(root, username, on_success)
        else:
            messagebox.showerror(
                "Login Failed",
                "❌ Invalid ID format.\nUse KE0001, KE0412, or LL0001."
            )

    # Allow pressing Enter to trigger login
    root.bind("<Return>", lambda e: check_login())
"""


# ===== UPDATED LABEL UI =====
# PACKAGING/label_ui.py (UPDATE build_main_ui function signature)

"""
# Add these parameters to your function signature:
def build_main_ui(root, username, serial_num, lot_code):
    '''Enhanced main interface after login with serial validation'''
    global sku_entry, barcode_entry, qty_entry, lot_entry, preview_label, status_var

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
        ("LOT CODE:", lot_code)  # Use fetched lot_code from database
    ]

    entries = {}
    for i, (label_text, default) in enumerate(fields):
        ttk.Label(form_card, text=label_text).grid(row=i, column=0, sticky="w", pady=12)
        entry = ttk.Entry(form_card, width=35)
        entry.insert(0, default)
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

    # --- Buttons Frame ---
    btn_frame = ttk.Frame(form_card, style="Card.TFrame")
    btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=(25, 10))

    ttk.Button(
        btn_frame,
        text="🖨️ Print Label",
        command=lambda: print_label(
            sku_entry, barcode_entry, qty_entry, lot_entry, status_var
        ),
        style="Accent.TButton"
    ).grid(row=0, column=0, padx=6)

    ttk.Button(
        btn_frame,
        text="📤 Submit",
        command=lambda: show_external_preview(
            root,
            sku_entry.get(),
            lot_entry.get(),
            qty_entry.get()
        ),
        style="Accent.TButton"
    ).grid(row=0, column=1, padx=6)

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

    # --- Status Bar ---
    status_var = tk.StringVar(value=f"✅ Ready | Serial: {serial_num} | LOT: {lot_code}")
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
"""