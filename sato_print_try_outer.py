import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports

class LabelPrinterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SATO Label Printer")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="SATO Label Printer", 
                                font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Input fields
        # SKU
        ttk.Label(main_frame, text="SKU:", font=('Arial', 10)).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.sku_entry = ttk.Entry(main_frame, width=40, font=('Arial', 10))
        self.sku_entry.grid(row=1, column=1, pady=5, padx=(10, 0))
        self.sku_entry.insert(0, "43000166102")
        
        # Lot Code
        ttk.Label(main_frame, text="Lot Code:", font=('Arial', 10)).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.lot_entry = ttk.Entry(main_frame, width=40, font=('Arial', 10))
        self.lot_entry.grid(row=2, column=1, pady=5, padx=(10, 0))
        self.lot_entry.insert(0, "5296C")
        
        # Quantity
        ttk.Label(main_frame, text="Quantity:", font=('Arial', 10)).grid(row=3, column=0, sticky=tk.W, pady=5)
        self.qty_entry = ttk.Entry(main_frame, width=40, font=('Arial', 10))
        self.qty_entry.grid(row=3, column=1, pady=5, padx=(10, 0))
        self.qty_entry.insert(0, "10")
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=20)
        
        # Printer connection settings
        ttk.Label(main_frame, text="COM Port:", font=('Arial', 10)).grid(row=5, column=0, sticky=tk.W, pady=5)
        
        port_frame = ttk.Frame(main_frame)
        port_frame.grid(row=5, column=1, pady=5, padx=(10, 0), sticky=tk.W)
        
        self.port_combo = ttk.Combobox(port_frame, width=25, font=('Arial', 10))
        self.port_combo.grid(row=0, column=0)
        
        refresh_btn = ttk.Button(port_frame, text="🔄", width=3, 
                                command=self.refresh_ports)
        refresh_btn.grid(row=0, column=1, padx=(5, 0))
        
        # Baud Rate
        ttk.Label(main_frame, text="Baud Rate:", font=('Arial', 10)).grid(row=6, column=0, sticky=tk.W, pady=5)
        self.baud_combo = ttk.Combobox(main_frame, width=37, font=('Arial', 10))
        self.baud_combo['values'] = ('9600', '19200', '38400', '57600', '115200')
        self.baud_combo.grid(row=6, column=1, pady=5, padx=(10, 0))
        self.baud_combo.set('9600')
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=20)
        
        # Preview button
        self.preview_btn = ttk.Button(button_frame, text="Preview ZPL", 
                                      command=self.preview_zpl, width=15)
        self.preview_btn.grid(row=0, column=0, padx=5)
        
        # Print button
        self.print_btn = ttk.Button(button_frame, text="Print Label", 
                                    command=self.print_label, width=15)
        self.print_btn.grid(row=0, column=1, padx=5)
        
        # Save ZPL button
        self.save_btn = ttk.Button(button_frame, text="Save ZPL to File", 
                                   command=self.save_zpl, width=15)
        self.save_btn.grid(row=0, column=2, padx=5)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready", 
                                     font=('Arial', 9), foreground='green')
        self.status_label.grid(row=8, column=0, columnspan=2, pady=10)
        
        # Populate COM ports after status_label is created
        self.refresh_ports()
    
    def refresh_ports(self):
        """Refresh available COM ports"""
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        
        if port_list:
            self.port_combo['values'] = port_list
            self.port_combo.set(port_list[0])
            self.status_label.config(text=f"Found {len(port_list)} COM port(s)", foreground='green')
        else:
            self.port_combo['values'] = []
            self.port_combo.set('')
            self.status_label.config(text="No COM ports found", foreground='orange')
        
    def generate_zpl(self):
        """Generate ZPL code with current values"""
        sku = self.sku_entry.get()
        lot_code = self.lot_entry.get()
        quantity = self.qty_entry.get()
        
        zpl = f"""^XA
^PW2070
^LL3307

^FO1670,200
^A0R,150,150
^FDSKU#:^FS

^FO1670,700
^BY5.5
^BCR,180,N,N,N
^FD43000166102^FS

^FO1870,950
^A0R,70,70
^FD{sku}^FS

^FO1670,1730
^A0R,150,150
^FDLot Code:^FS

^FO1670,2430
^BY5.5
^BCR,180,N,N,N
^FD5293C^FS

^FO1870,2580
^A0R,70,70
^FD{lot_code}^FS

^FO1520,160
^GB15,2820,10,R^FS

^FO1160,200
^A0R,150,150
^FDDESCRIPTION:^FS

^FO1190,1090
^A0R,80,100
^FDDDG DEVICE SPECTRALITE FACEWARE PRO^FS

^FO1070,160
^GB15,2820,10,R^FS

^FO680,200
^A0R,150,150
^FDQTY:^FS

^FO880,650
^A0R,70,70
^FD10^FS

^FO670,540
^BY6
^BCR,200,N,N,N
^FD10^FS

^FO560,160
^GB15,2820,10,R^FS

^FO340,200
^A0R,80,80
^FDLED Technologies, Inc.^FS

^FO250,200
^A0R,80,80
^FD11701 Belcher Rd, #110^FS

^FO160,200
^A0R,80,80
^FDLargo, FL, 33773^FS

^FO250,2250
^A0R,80,80
^FDPO#: 458105224^FS

^XZ
"""
        return zpl
    
    def preview_zpl(self):
        """Show ZPL code in a new window"""
        zpl = self.generate_zpl()
        
        preview_window = tk.Toplevel(self.root)
        preview_window.title("ZPL Preview")
        preview_window.geometry("600x600")
        
        text_frame = ttk.Frame(preview_window, padding="10")
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(text_frame, text="ZPL Code:", font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=('Courier', 9))
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=scrollbar.set)
        
        text_widget.insert('1.0', zpl)
        text_widget.config(state=tk.DISABLED)
        
        # Copy button
        def copy_to_clipboard():
            self.root.clipboard_clear()
            self.root.clipboard_append(zpl)
            messagebox.showinfo("Copied", "ZPL code copied to clipboard!")
        
        ttk.Button(preview_window, text="Copy to Clipboard", 
                  command=copy_to_clipboard).pack(pady=10)
    
    def print_label(self):
        """Send ZPL to printer via COM port"""
        try:
            port = self.port_combo.get()
            baud = int(self.baud_combo.get())
            
            if not port:
                messagebox.showerror("Error", "Please select a COM port")
                return
            
            zpl = self.generate_zpl()
            
            self.status_label.config(text="Connecting to printer...", foreground='orange')
            self.root.update()
            
            # Connect to printer via serial
            ser = serial.Serial(
                port=port,
                baudrate=baud,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=5
            )
            
            # Send ZPL
            ser.write(zpl.encode())
            ser.close()
            
            self.status_label.config(text="Label sent successfully!", foreground='green')
            messagebox.showinfo("Success", "Label sent to printer successfully!")
            
        except serial.SerialException as e:
            self.status_label.config(text="Connection failed", foreground='red')
            messagebox.showerror("Error", f"Failed to connect to COM port:\n{str(e)}")
        except Exception as e:
            self.status_label.config(text="Print failed", foreground='red')
            messagebox.showerror("Error", f"Failed to print label:\n{str(e)}")
    
    def save_zpl(self):
        """Save ZPL to a text file"""
        from tkinter import filedialog
        
        zpl = self.generate_zpl()
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".zpl",
            filetypes=[("ZPL files", "*.zpl"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(zpl)
                self.status_label.config(text=f"Saved to {filename}", foreground='green')
                messagebox.showinfo("Success", f"ZPL saved to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LabelPrinterGUI(root)
    root.mainloop()