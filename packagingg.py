import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import serial
import serial.tools.list_ports
import mysql.connector
from zpl_codes import zpl_code

class ZPLPrinterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Packaging")
        self.root.geometry("750x700")

        # Serial connection
        self.ser = None

        # Create UI
        self.create_widgets()
        self.refresh_ports()

    def create_widgets(self):
        # =========================
        # 🔹 Printer Connection Frame
        # =========================
        conn_frame = ttk.LabelFrame(self.root, text="Printer Connection", padding=10)
        conn_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(conn_frame, text="COM Port:").grid(row=0, column=0, sticky="w", padx=5)
        self.port_combo = ttk.Combobox(conn_frame, width=15, state="readonly")
        self.port_combo.grid(row=0, column=1, padx=5)

        ttk.Button(conn_frame, text="Refresh", command=self.refresh_ports).grid(row=0, column=2, padx=5)

        ttk.Label(conn_frame, text="Baud Rate:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.baud_combo = ttk.Combobox(conn_frame, width=15, state="readonly",
                                       values=["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.set("9600")
        self.baud_combo.grid(row=1, column=1, padx=5, pady=5)

        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.grid(row=1, column=2, padx=5, pady=5)

        self.status_label = ttk.Label(conn_frame, text="Status: Disconnected", foreground="red")
        self.status_label.grid(row=2, column=0, columnspan=3, pady=5)

        # =========================
        # 🔹 ZPL Code Frame
        # =========================
        zpl_frame = ttk.LabelFrame(self.root, text="ZPL Code", padding=10)
        zpl_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.zpl_text = scrolledtext.ScrolledText(zpl_frame, height=12, width=70)
        self.zpl_text.pack(fill="both", expand=True)

        sample_zpl = """^XA
^FO50,50^A0N,50,50^FDZebra ZT410 Test^FS
^FO50,120^A0N,30,30^FDPrinter: ZT410 600 DPI^FS
^FO50,170^A0N,30,30^FDDate: $(D)^FS
^FO50,220^BY3^BCN,100,Y,N,N^FD123456789^FS
^XZ"""
        self.zpl_text.insert("1.0", sample_zpl)

        # Buttons Frame
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(btn_frame, text="Print Label", command=self.print_label).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Clear", command=self.clear_zpl).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Load Sample", command=self.load_sample).pack(side="left", padx=5)

        # =========================
        # 🔹 Barcode Scanning Frame
        # =========================
        scan_frame = ttk.LabelFrame(self.root, text="Barcode Scanning", padding=10)
        scan_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(scan_frame, text="Scan Serial Number:").grid(row=0, column=0, padx=5, pady=5)
        self.serial_entry = ttk.Entry(scan_frame, width=25, font=("Arial", 12))
        self.serial_entry.grid(row=0, column=1, padx=5)
        self.serial_entry.bind("<Return>", lambda event: self.check_serial_in_db())
        self.serial_entry.focus()

        ttk.Button(scan_frame, text="Check Database", command=self.check_serial_in_db).grid(row=0, column=2, padx=5)

        self.result_box = scrolledtext.ScrolledText(scan_frame, height=5, width=70)
        self.result_box.grid(row=1, column=0, columnspan=3, pady=5)
        self.result_box.insert("1.0", "→ Waiting for scan...\n")

        # =========================
        # 🔹 Log Frame
        # =========================
        log_frame = ttk.LabelFrame(self.root, text="Log", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, width=70)
        self.log_text.pack(fill="both", expand=True)

    # =========================
    # 🔹 Serial Port Handling
    # =========================
    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        self.port_combo['values'] = port_list
        if port_list:
            self.port_combo.current(0)
            self.log(f"Found {len(port_list)} port(s)")
        else:
            self.log("No COM ports found")

    def toggle_connection(self):
        if self.ser and self.ser.is_open:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        try:
            port = self.port_combo.get()
            baud = int(self.baud_combo.get())

            if not port:
                messagebox.showerror("Error", "Please select a COM port")
                return

            self.ser = serial.Serial(
                port=port,
                baudrate=baud,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )

            self.status_label.config(text=f"Status: Connected to {port}", foreground="green")
            self.connect_btn.config(text="Disconnect")
            self.log(f"Connected to {port} at {baud} baud")

        except serial.SerialException as e:
            messagebox.showerror("Connection Error", f"Failed to connect:\n{str(e)}")
            self.log(f"Connection failed: {str(e)}")

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.status_label.config(text="Status: Disconnected", foreground="red")
            self.connect_btn.config(text="Connect")
            self.log("Disconnected from printer")

    # =========================
    # 🔹 Print Label Functions
    # =========================
    def print_label(self):
        if not self.ser or not self.ser.is_open:
            messagebox.showwarning("Not Connected", "Please connect to the printer first")
            return

        zpl_code = self.zpl_text.get("1.0", "end-1c")

        if not zpl_code.strip():
            messagebox.showwarning("Empty ZPL", "Please enter ZPL code")
            return

        try:
            self.ser.write(zpl_code.encode('utf-8'))
            self.log("Label sent to printer successfully")
            messagebox.showinfo("Success", "Label sent to printer")
        except Exception as e:
            messagebox.showerror("Print Error", f"Failed to print:\n{str(e)}")
            self.log(f"Print failed: {str(e)}")

    def clear_zpl(self):
        self.zpl_text.delete("1.0", "end")

    def load_sample(self):
        sample_zpl = """^XA
^FO50,50^A0N,50,50^FDZebra ZT410 Test^FS
^FO50,120^A0N,30,30^FDPrinter: ZT410 600 DPI^FS
^FO50,170^A0N,30,30^FDDate: $(D)^FS
^FO50,220^BY3^BCN,100,Y,N,N^FD123456789^FS
^XZ"""
        self.zpl_text.delete("1.0", "end")
        self.zpl_text.insert("1.0", sample_zpl)
        self.log("Sample ZPL loaded")

    # =========================
    # 🔹 Barcode Database Check
    # =========================
    def check_serial_in_db(self):
        serial_num = self.serial_entry.get().strip()

        if not serial_num:
            messagebox.showwarning("Empty Input", "Please scan or enter a serial number.")
            return

        try:
            # Connect to MySQL
            db = mysql.connector.connect(
                host="192.168.1.38",
                user="labeling",
                password="labeling",
                database="ledtech"
            )
            cursor = db.cursor()

            query = "SELECT batch_code FROM faceware_assembly1 WHERE serial_num = %s"
            cursor.execute(query, (serial_num,))
            result = cursor.fetchone()

            if result:
                batch_code = result[0]
                msg = f"✅ Serial: {serial_num} → Batch Code: {batch_code}\n"
                self.result_box.insert("end", msg)
                self.log(msg)
            else:
                msg = f"❌ Serial '{serial_num}' not found in database.\n"
                self.result_box.insert("end", msg)
                self.log(msg)

            cursor.close()
            db.close()
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")
            self.log(f"Database error: {err}")

        # Reset for next scan
        self.serial_entry.delete(0, tk.END)
        self.serial_entry.focus()

    # =========================
    # 🔹 Utility Log
    # =========================
    def log(self, message):
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")

    def on_closing(self):
        self.disconnect()
        self.root.destroy()

# =========================
# 🔹 Run the App
# =========================
if __name__ == "__main__":
    root = tk.Tk()
    app = ZPLPrinterGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
