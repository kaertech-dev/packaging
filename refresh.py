# PACKAGIN/refresh.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import serial
import serial.tools.list_ports

class ZPLPrinterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Packaging")
        self.root.geometry("700x600")
        
        # Serial connection
        self.ser = None
        
        # Create UI
        self.create_widgets()
        self.refresh_ports()
        
    def create_widgets(self):
        # Connection Frame
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
        
        # ZPL Code Frame
        zpl_frame = ttk.LabelFrame(self.root, text="ZPL Code", padding=10)
        zpl_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.zpl_text = scrolledtext.ScrolledText(zpl_frame, height=15, width=70)
        self.zpl_text.pack(fill="both", expand=True)
        
        # Sample ZPL code for ZT410 at 600 DPI
        sample_zpl = """^XA
^LH0,0
^FO50,30^A0N,30,30^FDEN: EK0147^FS
^FO50,70^A0N,30,30^FDName: Arnel De Rosales^FS
^FO50,110^A0N,30,30^FDPW: q{C661|?^FS
^FO50,160^BY2
^BCN,100,Y,N,N
^FD>BEK0147^FS
^XZ

^XA
^LH0,0
^FO50,30^A0N,30,30^FDEN: EK0131^FS
^FO50,70^A0N,30,30^FDName: Pathrick Erdaje^FS
^FO50,110^A0N,30,30^FDPW: 8}73Tknp^FS
^FO50,160^BY2
^BCN,100,Y,N,N
^FD>BEK0131^FS
^XZ

^XA
^LH0,0
^FO50,30^A0N,30,30^FDEN: EK0008^FS
^FO50,70^A0N,30,30^FDName: Nico Vivares^FS
^FO50,110^A0N,30,30^FDPW: 4OzF1"-8^FS
^FO50,160^BY2
^BCN,100,Y,N,N
^FD>BEK0008^FS
^XZ

^XA
^LH0,0
^FO50,30^A0N,30,30^FDEN: EK0099^FS
^FO50,70^A0N,30,30^FDName: Nenito Solas^FS
^FO50,110^A0N,30,30^FDPW: w}a=Q709^FS
^FO50,160^BY2
^BCN,100,Y,N,N
^FD>BEK0099^FS
^XZ"""
        self.zpl_text.insert("1.0", sample_zpl)
        
        # Buttons Frame
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(btn_frame, text="Print Label", command=self.print_label,
                  style="Accent.TButton").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Clear", command=self.clear_zpl).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Load Sample", command=self.load_sample).pack(side="left", padx=5)
        
        # Log Frame
        log_frame = ttk.LabelFrame(self.root, text="Log", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, width=70)
        self.log_text.pack(fill="both", expand=True)
        
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
            
    def print_label(self):
        if not self.ser or not self.ser.is_open:
            messagebox.showwarning("Not Connected", "Please connect to the printer first")
            return
            
        zpl_code = self.zpl_text.get("1.0", "end-1c")
        
        if not zpl_code.strip():
            messagebox.showwarning("Empty ZPL", "Please enter ZPL code")
            return
            
        try:
            # Send ZPL code to printer
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
        
    def log(self, message):
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        
    def on_closing(self):
        self.disconnect()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ZPLPrinterGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()