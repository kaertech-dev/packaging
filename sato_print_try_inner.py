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
        self.sku_entry.insert(0, "SKU123456")
        
        # Lot Code
        ttk.Label(main_frame, text="Lot Code:", font=('Arial', 10)).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.lot_entry = ttk.Entry(main_frame, width=40, font=('Arial', 10))
        self.lot_entry.grid(row=2, column=1, pady=5, padx=(10, 0))
        self.lot_entry.insert(0, "LOT2024001")
        
        # Quantity
        ttk.Label(main_frame, text="Quantity:", font=('Arial', 10)).grid(row=3, column=0, sticky=tk.W, pady=5)
        self.qty_entry = ttk.Entry(main_frame, width=40, font=('Arial', 10))
        self.qty_entry.grid(row=3, column=1, pady=5, padx=(10, 0))
        self.qty_entry.insert(0, "100")
        
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
^MD 20
^PR3,3
^LT0 
^MNW 
^PON 
^PMN 
^LH0,0 
^JMA 
^PR3,3 ~SD40 
^JUS 
^LRN 
^CI27 
^PA0,1,1,0
^XA
^PW1890
^LL2362
^LS0

^FX SKU LABEL
^CF0,70
^FO160,1823^FD{sku}^FS
^CF0,70
^A0I,70
^FO1450,443^FD{sku}^FS

^FX BARCODE - NOW INCLUDES SKU AND LOT CODE
^BY4.5,3,170
^BCI,180,N,N,N
^FO160,2103^FD(91)5293C43000166102002^FS
^CF0,70
^FO160,2030^FD{barcode_data}^FS

^BY4.5,2,170
^BCI,180,N,N,N
^FO350,100^FD(91)5293C43000166102002^FS
^CF0,70
^A0I,70
^FO1065,280^FD{barcode_data}^FS

^FX Quantity pcs
^CF0,70
^FO160,1726^FD{quantity} PCS^FS
^A0I,70
^FO1660,569^FD{quantity} PCS^FS

^FX LOT CODE
^CF0,70
^FO839,1411^FD{lot}^FS
^A0I,70
^FO839,910^FD{lot}^FS

^CF0,40
^FO1339,1500^FDTHIS SIDE UP^FS

^FX ===============MADE IN PHILIPPINES ===================
^CF0, 70
^FO674,1923^FD MADE IN PHILIPPINES^FS
^FX =========== MADE IN PHILIPPINES (ROTATED 180°) ========
^CF0,70
^A0I,70
^FO674,380^FD MADE IN PHILIPPINES^FS

^FX ==============DDG DEVICE TEXT MIRROR=================
^A0I,90
^CF0,70
^FO210,680^FDDDG DEVICE SPECTRALITE FACEWARE PRO^FS

^FX ===============DDG DEVICE ====================
^CF0,90
^FO160,1621^FDDDG DEVICE SPECTRALITE FACEWARE PRO^FS

^FX ===============IMAGE=============
^FO138,1472^GFA,1121,5695,67,:Z64:eJy12MvN3CAQAGAQB46UQAsp4JdoKcccInnTmdOJpTTgow/IExjeZvDacdaKsvt78Wcew5Oxcln29FIwPyUm2B4KAgBezwjliIfZ0Jbp/RkxLYw/JHxFfD0SBDzLgbvkfwisp0HhGmR9TJiF3W1UdQjFaXZMJkp30W2y6uLHUIRMcFjcv5xuZ4BXl0Mfzi35IgmX7lciptV1xdIN/PelIjAsCMJs+veRgPjSjTclGRGwiJ7A6pGu6E39y50khEvHA2ELsYQieqauG5qQ7o08NU8mMPvGsvITEpYk/KsaYosP41++nIXQNOEL2xBrynF42lQxrTeSaHKbCKyBcFdXndPQhM94RwjfJPhfzNApARSBN0Jj1E2CvxHEShBYDeH9ouppNIGfBLGmWuAVASQhaMLXEJa8CYzQRD0xU4R/fNrKcyXHPSEHhI0lzx85Qx2B4xJNxBSFELcIF7MphdneELrEYUfMB0Ji43SEGRAQ31lH+IjYSUJBjqlCKGAUMY2Il4xE6SQjwj4m4IRgByKMoz2xkYSLOAWpEs8JfocwJCFgvUHYu8SeiFckpkDgNFMIiR8kkSahMuaErmvCpHOBWK4SYUl9kYBTIs5gmRAksVKExt+vEfxjBPb1i4RIj9DEsTrPiENopb+vETNFTDcI+TEC7HUirmP/gZDnRFwTUkTV2SOh7xHUeKHDlwMRhouPE+kzbQE6YhkS3SRAE3JM9PPINCDmt0RehYeh80ioE6KblmFAvGhClZndZGK7SxyXKJwmdNq7nBBTJtZ7xJ5G27zWEjQRm5pcKOVFYyRkvai5QthEVBuXmSKmEeGbwbQDQeyoHWFHxJZiyo843/HWTcIXQsXNxIv9wFuxux2I2NQEsaaxxkM/sVp3mlgHhP81dCBfHINpLEXwEcHD4n6JFesPBmTaN7eEyPuaAxFGbXyBf1IuvkArRcS+3hOh70w2ZkX4DU5KUxPf8glHv1sOaztIb3Ff8sGcroiv1EXizF5v+7HqfDyGaDCLyicZNWFScBIEVp0Ey0N+VFIZa84S9B/YRsSSb2/p20oQKt/OhGmOQKpTFE2fUUp4d4Kq4M3pJu/Pf7oUYM9TmLdnZbGD/wUh51Bo:B543
^FO1403,1355^GFA,225,1840,16,:Z64:eJzt0DEKAyEQhWElhaVtur1IwKvsSVaPtkfJESwtxAnMe6sS0qQJBLQZPvhhBo0xd4O3cz44M+eBYQvdMG6Xha7sJOl0VyenTs/O0Vv3k07ssDj0Dosiu0BLd6Uzu4Yzeic4A52l3eQEN3a62I9OF23sPB0mZ/pkV/SM0VWcoV2E7exGF3aCM3Dg+I/08b+Wl5f/x799UeZXjCx/5fjmF7sgmK8=:6D86

^FX================ seido img MIRROR=================
^FO1224,825^GFA,1109,5695,67,:Z64:eJzF2E0SnCoQAGAoFuziEbjJ42bBo3mUyQ3MzoXPjtDQIjQyaqVC1dQ4I34iQvMjhJAAopM0jJfnB4BPhzAwX553AGuHAFi4v228cH8OiOV0EI4VjCYcpdIpgC0vkqC/sXSa8kpoEBp+c8ReA1iM/TlNhnGEgdFK+Ej8TYSBVYVjt98Ayzm0CLuJgSEcTMJMvqoWXy94johYi5Fwq1A1ERqDnv3B7O8/Yk5fRzXh78IRe365xFajwJfHzTwR7lITOtTgT1+AlAmvYAjlv2tiCD//2//YjqJOtwgT8pu9JtdYYQKvZAjt89aEDdn0JFxouvaKCJVdEy6UX41Yh+FxNIgHBGXzlTpsTUJEYsqJ1PWi7F9tkzAsIVMAwBYRCHOPUAcxJqlJ2I0n8GwKaf4svl6GcCyhD4KqpE2sHDHgr1jbPveMOZ8Q20EsDQKuCRMj7359m1g4wqRcXxCyRYgzYZ8TdqVvaBDYhirCpi5il4OY/xqBbagiqKO658RaEGaTLQIbQEXQQOzmx8RyhxjfEqZBzG8JeYew8ZJPnDzAl4Q+RnZsACVBQeufEjqFi28IbEP3CdUnxq/fCIaLr4hWvIg0jqmSiIGIvLPzhMqJcLdIiLeEuUV8WGKriGb4jW+vTeQRnB/NBp6w6x1i/I5wTcLwBIVOGlP39tEY2WlSUxBLSexvzvJTlC6hgXI3ZjlxyCmJY6lFU5TmRMn1CHVMlFrEyhOfgvBfAz91jcG+IORBxKiMUWZkiZknpkSINO8UDUL2CQwY/t0qdjGRSlwQlIcI30j59UicHl8R2FVDO2dXRZonNIWL1ElCW2PXZilGXhDYwkOdhQKVRApwJZEtn/VRv4ZbZBqeGDJC4iLTXzQAQ6S4UBL5ZsNR2mzNnhELS5glI3weGwesas0+UV+4Inzvii2w2r/4NVMrLAibb6vsLz6tTmxVio1eXkl8MkKmIS5VRk44mhoWhMsJdi8nEYb6dEFkvUxc7yhJOI5SJiTGUz67iDvJnOjHSW39PJ2kezth/TTce3YunVrW/fRj/7jpFWFm7N5viO0ULZ4kDf93tyZ7yfU3SPvFeFkVIu0qvivGqRB/AOYcXok=:6600
^PQ1,0,1,Y
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