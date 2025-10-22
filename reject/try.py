import tkinter as tk
from tkinter import messagebox
import serial
import time
from PIL import Image, ImageTk
import io
import urllib.request
import urllib.parse

class ZPLLabelEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("ZPL Label Editor & Printer")
        self.root.geometry("1200x800")
        self.root.configure(bg="#1a1a2e")
        
        # Variables
        self.vars = {
            "SKU# Barcode:": tk.StringVar(value="43000166102"),
            "Lot Code Barcode:": tk.StringVar(value="4341C"),
            "Quantity Barcode:": tk.StringVar(value="10"),
            "Description:": tk.StringVar(value="DDG DEVICE SPECTRALITE FACEWARE PRO"),
            "COM Port:": tk.StringVar(value="COM3")
        }
        
        self.setup_ui()
        self.update_preview()
    
    def setup_ui(self):
        # Main container
        main = tk.Frame(self.root, bg="#1a1a2e")
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        tk.Label(tk.Frame(main, bg="#0f3460", relief=tk.RAISED, bd=2), 
                 text="🏷️ ZPL Label Editor & Printer",
                 font=("Arial", 24, "bold"), bg="#0f3460", fg="white", pady=15
                ).pack()
        main.children[list(main.children.keys())[-1]].pack(fill=tk.X, pady=(0, 20))
        
        # Content
        content = tk.Frame(main, bg="#1a1a2e")
        content.pack(fill=tk.BOTH, expand=True)
        
        # Left panel
        left = tk.Frame(content, bg="#16213e", relief=tk.RAISED, bd=2)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        tk.Label(left, text="Label Fields", font=("Arial", 18, "bold"),
                bg="#16213e", fg="white", pady=10).pack(pady=10)
        
        # Input fields
        for label, var in self.vars.items():
            f = tk.Frame(left, bg="#16213e")
            f.pack(padx=20, pady=8, fill=tk.X)
            tk.Label(f, text=label, font=("Arial", 11, "bold"), bg="#16213e",
                    fg="white", width=18, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 10))
            entry = tk.Entry(f, textvariable=var, font=("Arial", 11), bg="#0d1117",
                           fg="white", insertbackground="white", relief=tk.SOLID, bd=2)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            entry.bind('<Return>', lambda e: self.update_preview())
        
        # Buttons
        btn_frame = tk.Frame(left, bg="#16213e")
        btn_frame.pack(pady=20, padx=20, fill=tk.X)
        
        for text, cmd, color in [
            ("🔄 Update Preview", self.update_preview, "#4a90e2"),
            ("🖨️ Print Label", self.print_label, "#2ecc71"),
            ("📋 Copy ZPL Code", self.copy_zpl, "#9b59b6")
        ]:
            tk.Button(btn_frame, text=text, command=cmd, font=("Arial", 12, "bold"),
                     bg=color, fg="white", relief=tk.RAISED, bd=3, padx=20, pady=10,
                     cursor="hand2").pack(fill=tk.X, pady=5)
        
        # Right panel
        right = tk.Frame(content, bg="#16213e", relief=tk.RAISED, bd=2)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        tk.Label(right, text="Label Preview", font=("Arial", 18, "bold"),
                bg="#16213e", fg="white", pady=10).pack()
        
        # Preview
        self.preview_frame = tk.Frame(right, bg="white", relief=tk.SUNKEN, bd=2)
        self.preview_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        self.preview_label = tk.Label(self.preview_frame, text="Loading preview...",
                                      bg="white", font=("Arial", 12))
        self.preview_label.pack(expand=True)
        
        # ZPL Code
        zpl_frame = tk.Frame(right, bg="#16213e")
        zpl_frame.pack(padx=20, pady=10, fill=tk.BOTH)
        
        tk.Label(zpl_frame, text="ZPL Code:", font=("Arial", 12, "bold"),
                bg="#16213e", fg="white").pack(anchor=tk.W)
        
        text_frame = tk.Frame(zpl_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.zpl_text = tk.Text(text_frame, height=8, font=("Courier", 9),
                               bg="#0d1117", fg="#58a6ff", relief=tk.SUNKEN, bd=2,
                               yscrollcommand=scrollbar.set)
        self.zpl_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.zpl_text.yview)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(main, textvariable=self.status_var, font=("Arial", 10),
                bg="#0f3460", fg="white", relief=tk.SUNKEN, anchor=tk.W,
                padx=10, pady=5).pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
    
    def generate_zpl(self):
        v = list(self.vars.values())
        return f"""^XA

^CF0,150
^FO200,140^FDSKU#:^FS
^FO900,110^BY4
^BCN,180,N,N,N
^FO800,110^FD43000166102^FS
^CF0,70
^FO950,30^FD43000166102^FS

^CF0,150
^FO1800,140^FDLot Code:^FS
^FO900,110^BY4
^BCN,180,N,N,N
^FO2500,110^FD4341C^FS
^CF0,70
^FO2580,30^FD4341C^FS

^FO160,410^GB2820,15,10^FS   ; line

^CF0,150
^FO200,600^FDDESCRIPTION:^FS
^CF0,105
^FO1140,620^FDDDG DEVICE SPECTRALITE FACEWARE PRO^FS

^FO160,870^GB2820,15,10^FS   ; line

^CF0,150
^FO200,1150^FDQTY:^FS
^FO900,110^BY6
^BCN,300,N,N,N
^FO800,1050^FD10^FS
^CF0,70
^FO950,30^FD10^FS


^XZ"""
    
    def update_preview(self):
        try:
            self.status_var.set("Generating preview...")
            self.root.update()
            
            zpl = self.generate_zpl()
            self.zpl_text.delete(1.0, tk.END)
            self.zpl_text.insert(1.0, zpl)
            
            encoded = urllib.parse.quote(zpl)
            url = f"http://api.labelary.com/v1/printers/8dpmm/labels/4x6/0/{encoded}"
            
            with urllib.request.urlopen(url, timeout=5) as response:
                img = Image.open(io.BytesIO(response.read()))
            
            w, h = 500, int(500 * img.height / img.width)
            photo = ImageTk.PhotoImage(img.resize((w, h), Image.Resampling.LANCZOS))
            
            self.preview_label.config(image=photo, text="")
            self.preview_label.image = photo
            self.status_var.set("Preview updated successfully")
            
        except Exception as e:
            self.preview_label.config(text=f"Preview unavailable\n{e}\n\nZPL valid for printing", image="")
            self.status_var.set(f"Preview error: {e}")
    
    def copy_zpl(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.generate_zpl())
        self.status_var.set("ZPL code copied to clipboard!")
        messagebox.showinfo("Success", "ZPL code copied to clipboard!")
    
    def print_label(self):
        port = list(self.vars.values())[4].get()
        zpl_data = self.generate_zpl().encode('utf-8')
        
        try:
            self.status_var.set(f"Connecting to {port}...")
            self.root.update()
            
            for attempt in range(2):
                try:
                    ser = serial.Serial(port=port, baudrate=9600, bytesize=serial.EIGHTBITS,
                                       parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                                       timeout=1, write_timeout=3, dsrdtr=False, rtscts=False)
                    
                    ser.dtr = ser.rts = False
                    time.sleep(0.3)
                    ser.dtr = ser.rts = True
                    time.sleep(0.3)
                    
                    self.status_var.set(f"Sending label (attempt {attempt + 1})...")
                    self.root.update()
                    
                    ser.write(zpl_data)
                    ser.flush()
                    time.sleep(0.4)
                    ser.close()
                    
                    self.status_var.set("Label sent successfully!")
                    messagebox.showinfo("Success", "Label sent to printer successfully!")
                    return
                    
                except Exception as e:
                    if attempt == 0:
                        time.sleep(1.5)
                    else:
                        raise e
            
        except serial.SerialException as e:
            self.status_var.set(f"Printer error: {e}")
            messagebox.showerror("Printer Error", 
                f"Failed to connect to {port}\n\n{e}\n\nCheck:\n- Printer connected\n- Correct COM port\n- Printer powered on")
        except Exception as e:
            self.status_var.set(f"Error: {e}")
            messagebox.showerror("Error", f"Failed to print label:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ZPLLabelEditor(root)
    root.mainloop()