import tkinter as tk
from tkinter import Frame, Label, Entry, Button, ttk, messagebox
import serial
import serial.tools.list_ports

class SerialValidationUI:
    def __init__(self, parent, username, on_validate, on_cancel):
        self.parent = parent
        self.username = username
        self.on_validate = on_validate
        self.on_cancel = on_cancel

        self.serial_var = tk.StringVar()
        self.selected_port = tk.StringVar()
        self.connection = None  # ✅ initialize connection object

        self.build_ui()

    def build_ui(self):
        self.container = Frame(self.parent, bg="#16213e")
        self.container.place(relx=0.5, rely=0.5, anchor="center")

        card = Frame(self.container, bg="#f4f5f7", bd=0)
        card.grid(row=0, column=0, padx=20, pady=20, ipadx=30, ipady=20)

        Label(card, text="🔍 Serial Number Validation", font=("Segoe UI", 18, "bold"),
              bg="#f4f5f7", fg="#16213e").grid(row=0, column=0, columnspan=4, pady=(10, 10))

        Label(card, text=f"Logged in as: {self.username}", font=("Segoe UI", 10),
              bg="#f4f5f7", fg="#666").grid(row=1, column=0, columnspan=4, pady=(0, 20))

        # --- COM Port Selection ---
        Label(card, text="Select COM Port:", font=("Segoe UI", 11, "bold"),
              bg="#f4f5f7").grid(row=2, column=0, sticky="e", padx=(10, 5), pady=10)

        self.port_dropdown = ttk.Combobox(card, textvariable=self.selected_port, font=("Segoe UI", 11),
                                          width=25, state="readonly")
        self.port_dropdown.grid(row=2, column=1, padx=(0, 10), pady=10, sticky="w")

        refresh_btn = Button(card, text="🔄 Refresh", command=self.refresh_ports,
                             font=("Segoe UI", 9), bg="#0f3460", fg="white",
                             relief="flat", cursor="hand2")
        refresh_btn.grid(row=2, column=2, padx=(5, 5))

        self.connect_btn = Button(card, text="🔌 Connect", command=self.connect_port,
                             font=("Segoe UI", 9), bg="#1a508b", fg="white",
                             relief="flat", cursor="hand2")
        self.connect_btn.grid(row=2, column=3, padx=(5, 10))

        # --- Baud Rate Selection ---
        Label(card, text="Baud Rate:", font=("Segoe UI", 11, "bold"),
              bg="#f4f5f7").grid(row=3, column=0, sticky="e", padx=(10, 5), pady=10)

        self.baud_combo = ttk.Combobox(card, font=("Segoe UI", 11), width=25, state="readonly",
                                       values=["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.set("19200")  # Default baud rate for ZT410
        self.baud_combo.grid(row=3, column=1, padx=(0, 10), pady=10, sticky="w")

        # --- Serial Number Entry ---
        Label(card, text="Serial Number:", font=("Segoe UI", 11, "bold"),
              bg="#f4f5f7").grid(row=4, column=0, sticky="e", padx=(10, 5), pady=10)

        Entry(card, textvariable=self.serial_var, font=("Segoe UI", 11),
              width=28, relief="solid", bd=1).grid(row=4, column=1, pady=10, padx=(0, 10))

        # --- Status Label ---
        self.status_label = Label(card, text="⚠️ Please connect to printer first", font=("Segoe UI", 9),
                                  bg="#f4f5f7", fg="#d9534f")
        self.status_label.grid(row=5, column=0, columnspan=4, pady=(5, 10))

        # --- Buttons ---
        btn_frame = Frame(card, bg="#f4f5f7")
        btn_frame.grid(row=6, column=0, columnspan=4, pady=(10, 10))

        Button(btn_frame, text="✓ Validate & Continue", command=self.on_validate,
               font=("Segoe UI", 11, "bold"), bg="#0f3460", fg="white",
               padx=20, pady=8, relief="flat", cursor="hand2",
               activebackground="#1a508b").pack(side="left", padx=5)

        Button(btn_frame, text="Logout", command=self.on_cancel,
               font=("Segoe UI", 11), bg="#666", fg="white",
               padx=20, pady=8, relief="flat", cursor="hand2",
               activebackground="#888").pack(side="left", padx=5)

        # --- Initialize ports ---
        self.refresh_ports()
        self.parent.bind('<Return>', lambda e: self.on_validate())

    # --------------------------------------------------------
    def refresh_ports(self):
        """Refresh available COM ports"""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        if not ports:
            ports = ["No ports found"]
        self.port_dropdown["values"] = ports
        if ports and ports[0] != "No ports found":
            self.port_dropdown.set(ports[0])
        self.set_status("🔍 Ports refreshed. Please connect.", "#0078d7")

    def connect_port(self):
        """Connect to the selected COM port and keep it open"""
        port = self.selected_port.get()
        baud = self.baud_combo.get()
        
        if not port or port == "No ports found":
            messagebox.showerror("Connection Error", "⚠️ No COM port selected.")
            return
        
        if not baud:
            messagebox.showerror("Connection Error", "⚠️ Please select a baud rate.")
            return

        try:
            # Close existing connection if any
            if self.connection and self.connection.is_open:
                self.connection.close()
            
            # Open new connection
            self.connection = serial.Serial(
                port=port,
                baudrate=int(baud),
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=2
            )
            
            self.set_status(f"✅ Connected to {port} at {baud} baud", "green")
            self.connect_btn.config(text="🔌 Connected", bg="#28a745")
            messagebox.showinfo("Success", f"✅ Connected to printer!\n\nPort: {port}\nBaud Rate: {baud}")
            
        except serial.SerialException as e:
            self.connection = None
            messagebox.showerror("Connection Error", f"Failed to connect:\n{e}\n\nPlease check:\n• Printer is ON\n• Cable is connected\n• Correct COM port")
            self.set_status("❌ Failed to connect.", "red")
            self.connect_btn.config(text="🔌 Connect", bg="#1a508b")

    def close_connection(self):
        """Close the serial connection properly"""
        try:
            if self.connection and self.connection.is_open:
                self.connection.close()
                self.set_status("🔌 Connection closed.", "#0078d7")
        except Exception as e:
            print(f"Error closing connection: {e}")

    def set_status(self, text, color):
        self.status_label.config(text=text, fg=color)

# ✅ UPDATED: Pass connection without closing it
def handle_success(validation_instance, serial_num, po_num):
    """
    Handle successful validation - transition to main UI
    Pass printer connection to main UI WITHOUT closing it
    """
    # Check if connected
    if not validation_instance.ui.connection or not validation_instance.ui.connection.is_open:
        messagebox.showerror("Connection Required", "⚠️ Please connect to the printer first!")
        return
    
    # DON'T close the connection - pass it to main UI
    validation_instance.ui.container.destroy()
    validation_instance.on_success_callback(
        validation_instance.root, 
        validation_instance.username, 
        serial_num, 
        po_num,
        validation_instance.ui.connection  # ✅ Pass the connection
    )

def handle_cancel(validation_instance):
    """Handle logout/cancel"""
    # Close COM port before logging out
    if validation_instance.ui.connection:
        validation_instance.ui.close_connection()
    
    from login_ui import build_login_ui
    validation_instance.ui.container.destroy()
    build_login_ui(
        validation_instance.root, 
        lambda r, u: validation_instance.__class__(r, u, validation_instance.on_success_callback)
    )