# CONSOLIDATED PACKAGING APPLICATION
# All functionality in one file: Login, GUI, Database, Printer, and Styling

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import re
from datetime import datetime
from PIL import Image, ImageTk
import serial
import serial.tools.list_ports
import pymysql
import atexit
import time
from types import MethodType

# ============================================
# SECTION 1: WIDGET STYLING
# ============================================

def apply_widget_styles():
    """Apply all ttk widget styles"""
    style = ttk.Style()
    style.theme_use("clam")

    # --- Refresh Button ---
    style.configure(
        "Refresh.TButton",
        background="#E6F0FF",
        foreground="#004AAD",
        font=("Segoe UI", 9, "bold"),
        padding=6
    )
    style.map(
        "Refresh.TButton",
        background=[("active", "#CCE0FF")],
        foreground=[("active", "#002F7A")]
    )

    # --- Connect Button ---
    style.configure(
        "Connect.TButton",
        background="#E8FBE8",
        foreground="#006400",
        font=("Segoe UI", 9, "bold"),
        padding=6
    )
    style.map(
        "Connect.TButton",
        background=[("active", "#BFFFBF")],
        foreground=[("active", "#004D00")]
    )

    # --- Disconnect Button ---
    style.configure(
        "Disconnect.TButton",
        background="#FFE5E5",
        foreground="#B22222",
        font=("Segoe UI", 9, "bold"),
        padding=6
    )
    style.map(
        "Disconnect.TButton",
        background=[("active", "#FFCCCC")],
        foreground=[("active", "#8B0000")]
    )

    # --- Check Database Button ---
    style.configure(
        "CheckDB.TButton",
        background="#E6F7E6",
        foreground="#006400",
        font=("Segoe UI", 9, "bold"),
        padding=(4, 2)
    )
    style.map(
        "CheckDB.TButton",
        background=[("active", "#C2EABD")],
        relief=[("pressed", "sunken")]
    )

    # --- Logout Button ---
    style.configure(
        "Logout.TButton",
        background="#FFE6E6",
        foreground="#B30000",
        font=("Segoe UI", 9, "bold"),
        padding=(4, 2),
        borderwidth=1,
        relief="solid"
    )
    style.map(
        "Logout.TButton",
        background=[
            ("active", "#FFCCCC"),
            ("pressed", "#FFB3B3")
        ],
        foreground=[("active", "#800000")]
    )

    # --- Login Button ---
    style.configure(
        "Login.TButton",
        font=("Segoe UI", 11, "bold"),
        foreground="black",
        background="#0078D7",
        padding=(10, 6),
        relief="flat"
    )
    style.map(
        "Login.TButton",
        background=[
            ("active", "#005A9E"),
            ("disabled", "#A0A0A0")
        ],
        relief=[("pressed", "groove")]
    )

    # --- User Info Label ---
    style.configure(
        "UserInfo.TLabel",
        font=("Segoe UI", 9, "bold"),
        padding=4
    )


def create_green_header(parent, text, image_path=None, img_size=(32, 32)):
    """Creates a green-bordered header with image (left) + text (right)"""
    header_frame = tk.Frame(
        parent,
        bg="white",
        highlightbackground="#28a745",
        highlightthickness=2,
        bd=0,
        relief="solid"
    )
    header_frame.pack(pady=10, fill="x", padx=20)

    inner_frame = tk.Frame(header_frame, bg="white")
    inner_frame.pack(pady=6)

    if image_path:
        try:
            img = Image.open(image_path)
            img = img.resize(img_size, Image.Resampling.LANCZOS)
            header_image = ImageTk.PhotoImage(img)
            img_label = tk.Label(inner_frame, image=header_image, bg="white")
            img_label.image = header_image
            img_label.pack(side="left", padx=(0, 10))
        except Exception as e:
            print(f"[WARNING] Could not load image: {e}")

    header_label = tk.Label(
        inner_frame,
        text=text,
        bg="white",
        fg="black",
        font=("Segoe UI", 14, "bold")
    )
    header_label.pack(side="left")

    return header_frame


def create_bordered_box(parent, username):
    """Create a compact single-row bordered box with welcome message"""
    box_frame = tk.Frame(
        parent,
        bg="white",
        highlightbackground="#28a745",
        highlightthickness=2,
        bd=0,
        relief="solid",
        padx=8,
        pady=1
    )
    box_frame.pack(pady=10, fill="x", padx=30)

    welcome_label = tk.Label(
        box_frame,
        text=f"Welcome {username}",
        bg="white",
        fg="black",
        font=("Segoe UI", 11, "bold")
    )
    welcome_label.pack(anchor="center", padx=10)

    return box_frame


def add_tooltip(widget, text):
    """Add a tooltip to a widget"""
    tip = tk.Toplevel(widget)
    tip.withdraw()
    tip.overrideredirect(True)
    label = tk.Label(tip, text=text, background="#FFFFE0", relief="solid", borderwidth=1, font=("Segoe UI", 8))
    label.pack()

    def enter(event):
        x, y, _, _ = widget.bbox("insert")
        x += widget.winfo_rootx() + 25
        y += widget.winfo_rooty() + 20
        tip.geometry(f"+{x}+{y}")
        tip.deiconify()

    def leave(event):
        tip.withdraw()

    widget.bind("<Enter>", enter)
    widget.bind("<Leave>", leave)


# ============================================
# SECTION 2: PRINTER HANDLER
# ============================================

class PrinterHandler:
    """Handle serial connections to label printers"""
    
    def __init__(self):
        self.inner_printer = None
        self.outer_printer = None
        atexit.register(self.safe_cleanup)

    def list_ports(self):
        """List available COM ports"""
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect_inner(self, port, baud):
        """Connect to inner box label printer"""
        if self.inner_printer and self.inner_printer.is_open:
            try:
                self.inner_printer.close()
            except Exception as e:
                print(f"[WARNING] Failed to close inner printer: {e}")
            self.inner_printer = None

        try:
            self.inner_printer = serial.Serial(port, baudrate=baud, timeout=1)
            print(f"[INFO] Inner printer connected to {port}")
            return True
        except serial.SerialException as e:
            print(f"[ERROR] Could not connect inner printer to {port}: {e}")
            self.inner_printer = None
            return False

    def connect_outer(self, port, baud):
        """Connect to outer box label printer"""
        if self.outer_printer and self.outer_printer.is_open:
            try:
                self.outer_printer.close()
            except Exception as e:
                print(f"[WARNING] Failed to close outer printer: {e}")
            self.outer_printer = None

        try:
            self.outer_printer = serial.Serial(port, baudrate=baud, timeout=1)
            print(f"[INFO] Outer printer connected to {port}")
            return True
        except serial.SerialException as e:
            print(f"[ERROR] Could not connect outer printer to {port}: {e}")
            self.outer_printer = None
            return False

    def disconnect_inner(self):
        """Close inner printer port and release it completely"""
        if self.inner_printer:
            try:
                if self.inner_printer.is_open:
                    self.inner_printer.close()
                print("[INFO] Inner printer port closed.")
            except Exception as e:
                print(f"[WARNING] Failed to close inner printer port: {e}")
            finally:
                try:
                    self.inner_printer = None
                except:
                    pass
        time.sleep(1)
        print("[INFO] Inner printer port fully released.")

    def disconnect_outer(self):
        """Close outer printer port and release it completely"""
        if self.outer_printer:
            try:
                if self.outer_printer.is_open:
                    self.outer_printer.close()
                print("[INFO] Outer printer port closed.")
            except Exception as e:
                print(f"[WARNING] Failed to close outer printer port: {e}")
            finally:
                try:
                    self.outer_printer = None
                except:
                    pass
        time.sleep(1)
        print("[INFO] Outer printer port fully released.")

    def disconnect_all(self):
        """Disconnect both printers"""
        self.disconnect_inner()
        self.disconnect_outer()

    def safe_cleanup(self):
        """Ensure all ports are closed before exiting"""
        if self.inner_printer:
            if self.inner_printer.is_open:
                try:
                    self.inner_printer.close()
                    print("[CLEANUP] Inner printer port safely released.")
                except Exception as e:
                    print(f"[CLEANUP WARNING] Error closing inner printer port: {e}")
            self.inner_printer = None
        
        if self.outer_printer:
            if self.outer_printer.is_open:
                try:
                    self.outer_printer.close()
                    print("[CLEANUP] Outer printer port safely released.")
                except Exception as e:
                    print(f"[CLEANUP WARNING] Error closing outer printer port: {e}")
            self.outer_printer = None

    def is_inner_connected(self):
        return self.inner_printer and self.inner_printer.is_open

    def is_outer_connected(self):
        return self.outer_printer and self.outer_printer.is_open

    def is_all_connected(self):
        """Check if both printers are connected"""
        return self.is_inner_connected() and self.is_outer_connected()

    def send_to_inner_printer(self, zpl_data):
        """Send ZPL data to inner box printer"""
        if self.is_inner_connected():
            try:
                self.inner_printer.write(zpl_data.encode("utf-8"))
                print("[INFO] Data sent to inner printer.")
                return True
            except serial.SerialException as e:
                print(f"[ERROR] Failed to send data to inner printer: {e}")
                self.disconnect_inner()
                return False
        else:
            print("[WARNING] Inner printer not connected.")
            return False

    def send_to_outer_printer(self, zpl_data):
        """Send ZPL data to outer box printer"""
        if self.is_outer_connected():
            try:
                self.outer_printer.write(zpl_data.encode("utf-8"))
                print("[INFO] Data sent to outer printer.")
                return True
            except serial.SerialException as e:
                print(f"[ERROR] Failed to send data to outer printer: {e}")
                self.disconnect_outer()
                return False
        else:
            print("[WARNING] Outer printer not connected.")
            return False


# ============================================
# SECTION 3: DATABASE HANDLERS
# ============================================

class DatabaseHandler:
    """Handle database queries"""
    
    def __init__(self):
        self.config = {
            'host': '192.168.1.38',
            'user': 'labeling',
            'password': 'labeling',
            'database': 'ledtech'
        }

    def get_batch_and_po(self, serial_num):
        """Fetch batch_code and po_num from faceware_assembly1"""
        try:
            db = pymysql.connect(**self.config)
            cursor = db.cursor()
            cursor.execute("SELECT batch_code, po_num FROM faceware_assembly1 WHERE serial_num = %s", (serial_num,))
            result = cursor.fetchone()
            cursor.close()
            db.close()
            if result:
                return result
            else:
                return None, None
        except pymysql.Error as err:
            print(f"[DB ERROR] {err}")
            return None, None


class InsertDatabaseHandler:
    """Handle database inserts and updates"""
    
    def __init__(self):
        self.config = {
            'host': '192.168.1.38',
            'user': 'labeling',
            'password': 'labeling',
            'database': 'ledtech'
        }

    def record_operator_activity(self, operator, shift, serial_num, batch_code, po_num, 
                                 ship_mode, innerbox, outerbox, pallet_num):
        """Insert operator data with box counting information"""
        try:
            db = pymysql.connect(**self.config)
            cursor = db.cursor(pymysql.cursors.DictCursor)

            # Verify serial exists in faceware_main
            cursor.execute("SELECT * FROM faceware_main WHERE serial_num = %s", (serial_num,))
            main_data = cursor.fetchone()

            if not main_data:
                messagebox.showerror("Database Error", f"Serial {serial_num} not found in faceware_main")
                cursor.close()
                db.close()
                return False

            # Verify all required stations have status = 1
            required_stations = [
                "assembly1", "lasermarking1",
                "assembly2", "soldering2", "vi2",
                "assembly4", "vi3", "finaltest",
                "packing", "lasermarking2", "fvi"
            ]

            incomplete_stations = [
                s for s in required_stations
                if s not in main_data or main_data[s] != 1
            ]

            if incomplete_stations:
                messagebox.showerror(
                    "Incomplete Stations",
                    f"Serial {serial_num} hasn't completed all required stations.\n"
                    f"Missing: {', '.join(incomplete_stations)}"
                )
                cursor.close()
                db.close()
                return False

            # Get batch_code & PO if not provided
            if not batch_code or not po_num:
                cursor.execute(
                    "SELECT batch_code, po_num FROM faceware_assembly1 WHERE serial_num = %s",
                    (serial_num,)
                )
                result = cursor.fetchone()
                if result:
                    batch_code, po_num = result
                else:
                    messagebox.showerror("Database Error", f"Could not find batch info for {serial_num}")
                    cursor.close()
                    db.close()
                    return False

            # Prevent duplicate packaging entries
            check_query = """
                SELECT COUNT(*) AS cnt FROM faceware_packaging 
                WHERE serial_num = %s AND po_num = %s AND batch_code = %s
            """
            cursor.execute(check_query, (serial_num, po_num, batch_code))
            if cursor.fetchone()["cnt"] > 0:
                messagebox.showwarning(
                    "Duplicate Entry",
                    f"Serial {serial_num} is already packaged!"
                )
                cursor.close()
                db.close()
                return False

            # Insert new packaging record
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            insert_query = """
                INSERT INTO faceware_packaging 
                (serial_num, po_num, operator_en, shift, date_time, sku, batch_code, 
                 ship_mode, innerbox, outerbox, pallet_num)
                VALUES (%s, %s, %s, %s, %s, 43000166102, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                serial_num, po_num, operator, shift, now,
                batch_code, ship_mode, innerbox, outerbox, pallet_num
            ))
            db.commit()

            print(f"[DB] ✅ Recorded: Serial {serial_num} | "
                  f"Innerbox {innerbox} | Outerbox {outerbox} | Pallet {pallet_num}")

            cursor.close()
            db.close()
            return True

        except pymysql.Error as err:
            print(f"[DB ERROR] {err}")
            messagebox.showerror("Database Error", f"⚠️ Database error occurred:\n{err}")
            return False

    def check_existing_packaging(self, serial_num, po_num, batch_code):
        """Check if serial_num already exists in faceware_packaging"""
        try:
            db = pymysql.connect(**self.config)
            cursor = db.cursor(pymysql.cursors.DictCursor)
            
            query = """
                SELECT * FROM faceware_packaging 
                WHERE serial_num = %s AND po_num = %s AND batch_code = %s
            """
            cursor.execute(query, (serial_num, po_num, batch_code))
            result = cursor.fetchone()
            
            cursor.close()
            db.close()
            return result
                
        except pymysql.Error as err:
            print(f"[DB ERROR] {err}")
            return None

    def get_batch_unit_count(self, batch_code, po_num):
        """Count units packaged for a batch code"""
        try:
            db = pymysql.connect(**self.config)
            cursor = db.cursor()
            
            query = """
                SELECT COUNT(*) FROM faceware_packaging 
                WHERE batch_code = %s AND po_num = %s
            """
            cursor.execute(query, (batch_code, po_num))
            count = cursor.fetchone()[0]
            
            cursor.close()
            db.close()
            return count
                
        except pymysql.Error as err:
            print(f"[DB ERROR] {err}")
            return 0

    def get_pallet_unit_count(self, pallet_num, po_num):
        """Count units in a specific pallet"""
        try:
            db = pymysql.connect(**self.config)
            cursor = db.cursor()
            
            query = """
                SELECT COUNT(*) FROM faceware_packaging 
                WHERE pallet_num = %s AND po_num = %s
            """
            cursor.execute(query, (pallet_num, po_num))
            count = cursor.fetchone()[0]
            
            cursor.close()
            db.close()
            return count
                
        except pymysql.Error as err:
            print(f"[DB ERROR] {err}")
            return 0

    def update_packaging_status(self, serial_num, po_num, batch_code):
        """Update packaging status after label printing"""
        try:
            db = pymysql.connect(**self.config)
            cursor = db.cursor()

            update_main_query = """
                UPDATE faceware_main 
                SET packaging = 1 
                WHERE serial_num = %s
            """
            cursor.execute(update_main_query, (serial_num,))
            
            update_packaging_query = """
                UPDATE faceware_packaging 
                SET status = 1 
                WHERE serial_num = %s AND po_num = %s AND batch_code = %s
            """
            cursor.execute(update_packaging_query, (serial_num, po_num, batch_code))
            
            db.commit()
            cursor.close()
            db.close()
            return True

        except pymysql.Error as err:
            print(f"[DB ERROR] {err}")
            return False

    def get_unfinished_batches(self):
        """Return list of unfinished batches"""
        try:
            db = pymysql.connect(**self.config)
            cursor = db.cursor(pymysql.cursors.DictCursor)
            
            query = """
                SELECT batch_code, po_num, COUNT(*) as unit_count
                FROM faceware_packaging
                WHERE status = 0
                GROUP BY batch_code, po_num
            """
            cursor.execute(query)
            results = cursor.fetchall()
            
            cursor.close()
            db.close()
            return results
                
        except pymysql.Error as err:
            print(f"[DB ERROR] {err}")
            return []


# ============================================
# SECTION 4: ZPL CODE GENERATION
# ============================================

def generate_inner_zpl(sku, quantity, lot):
    """Generate ZPL code for inner box labels"""
    barcode_data = f"(91){lot}{sku}002"
    
    return f"""
CT~~CD,~CC^~CT~ 
^XA
^MD20
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

^FX BARCODE - INCLUDES SKU AND LOT CODE
^BY4.5,2,170
^BCI,180,N,N,N
^FO160,2103^FD{barcode_data}^FS
^CF0,70
^FO160,2030^FD{barcode_data}^FS

^BY4.5,2,170
^BCI,180,N,N,N
^FO350,100^FD{barcode_data}^FS
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

^FX MADE IN PHILIPPINES
^CF0, 70
^FO674,1923^FD MADE IN PHILIPPINES^FS
^CF0,70
^A0I,70
^FO674,380^FD MADE IN PHILIPPINES^FS

^FX DDG DEVICE TEXT
^A0I,90
^CF0,70
^FO210,680^FDDDG DEVICE SPECTRALITE FACEWARE PRO^FS

^FX DDG DEVICE
^CF0,90
^FO160,1621^FDDDG DEVICE SPECTRALITE FACEWARE PRO^FS

^PQ1,0,1,Y
^XZ
"""


def generate_outer_zpl(sku, lot_code, quantity):
    """Generate ZPL code for outer box labels"""
    return f"""
^XA
^PW2070
^LL3307

^FO1670,200
^A0R,150,150
^FDSKU#:^FS

^FO1670,700
^BY5.5
^BCR,180,N,N,N
^FD{sku}^FS

^FO1870,950
^A0R,70,70
^FD{sku}^FS

^FO1670,1730
^A0R,150,150
^FDLot Code:^FS

^FO1670,2430
^BY5.5
^BCR,180,N,N,N
^FD{lot_code}^FS

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
^FD{quantity}^FS

^FO670,540
^BY6
^BCR,200,N,N,N
^FD{quantity}^FS

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

# ============================================
# SECTION 5: PLACEHOLDER (REMOVED)
# ============================================
# Login and shipmode selection integrated into main GUI

# ============================================
# SECTION 6: MAIN PACKAGING GUI
# ============================================

class ZPLPrinterGUI:
    """Main packaging application GUI - Integrated with login and shipmode selection"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Packaging")
        self.root.geometry("1400x750")  # Landscape orientation
        self.center_window(1400, 750)
        
        # Login/Shipmode variables
        self.username_var = tk.StringVar()
        self.shift_var = tk.StringVar()
        self.ship_mode_var = tk.StringVar()
        self.shift_warning_count = 0
        
        # Login widget references (for disabling/enabling)
        self.operator_entry = None
        self.shift_dropdown = None
        self.ship_dropdown = None
        self.login_btn = None
        
        # Main application variables
        self.username = None
        self.serial_num = ""
        self.po_num = ""
        self.shift = None
        self.ship_mode = None
        self.is_logged_in = False
        
        # Box counting variables
        self.box_count_var = tk.StringVar()
        self.pallet_count = 1
        self.unit_count = 0
        self.total_units_per_pallet = 0
        self.units_per_innerbox = 2
        self.innerboxes_per_outerbox = 5
        
        self.current_pallet_batch_code = None
        
        self.box_dropdown = None
        self.box_count_frame = None
        self.capacity_label = None
        
        # UI widgets to enable/disable based on login
        self.scanning_widgets = []
        
        self.insert_db = InsertDatabaseHandler()
        self.printer = PrinterHandler()
        self.db = DatabaseHandler()
        
        apply_widget_styles()
        
        # Start with integrated login + main UI
        self.create_widgets()
        
        # Auto-disconnect any existing connections on startup
        self.auto_disconnect_on_startup()
        
        # Auto-refresh ports after UI is created
        self.root.after(500, self.refresh_ports)

    def center_window(self, width, height):
        """Center the window on screen"""
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def auto_disconnect_on_startup(self):
        """Automatically disconnect any existing COM port connections on startup"""
        print("[INFO] Checking for any existing COM port connections...")
        try:
            self.printer.disconnect_all()
            print("[INFO] Auto-disconnect on startup completed.")
        except Exception as e:
            print(f"[WARNING] Error during auto-disconnect: {e}")

    # ============================================
    # LOGIN VALIDATION
    # ============================================

    def validate_and_login(self):
        """Validate login credentials and enable scanning"""
        username = self.username_var.get().strip()
        shift = self.shift_var.get()
        ship_mode = self.ship_mode_var.get()
        
        if not re.match(r"^(KE|LL)\d{4}$", username):
            messagebox.showerror(
                "Invalid Format",
                "Invalid Operator ID.\nUse uppercase KE0000 or LL0000 only (e.g., KE0412)."
            )
            return
        
        if shift == "---Select Shift---" or not shift:
            self.shift_warning_count += 1
            
            if self.shift_warning_count >= 2:
                messagebox.showerror("Ang kulit!", "Ang kulit, Select Shift nga MUNA!!")
            else:
                messagebox.showwarning("Missing Shift", "Please select a shift (A or B or C).")
            
            return
        
        if ship_mode == "---Select Mode---" or not ship_mode:
            messagebox.showwarning("Missing Ship Mode", "Please select a shipping mode (SEA or AIR).")
            return
        
        # All validations passed
        self.shift_warning_count = 0
        self.username = username
        self.shift = shift
        self.ship_mode = ship_mode
        self.is_logged_in = True
        
        messagebox.showinfo("Login Successful", f"Welcome, {self.username} ({self.shift}) - {ship_mode} Mode")
        
        # Enable scanning interface
        self.enable_scanning_interface()
        
        # Disable login interface
        self.disable_login_interface()
        
        # Update display
        self.update_operator_info_display()
        self.create_box_dropdown()
        self.refresh_ports()
        self.box_count_var.trace("w", lambda *args: self.update_pallet_capacity())
        
        # Focus on serial entry
        self.serial_entry.focus()

    # ============================================
    # LOGIN AND SHIPMODE SCREENS
    # ============================================

    def create_widgets(self):
        """Create all UI widgets with integrated login"""
        # TOP SECTION: Header
        header_frame = tk.Frame(self.root, bg="white", highlightbackground="#28a745", highlightthickness=2, relief="solid")
        header_frame.pack(pady=5, fill="x", padx=10)
        
        ttk.Label(header_frame, text="Packaging", font=("Segoe UI", 20, "bold"), background="white").pack(pady=5)

        # MAIN CONTENT: Login on Left + Scanning on Right
        main_content = ttk.Frame(self.root)
        main_content.pack(fill="both", expand=True, padx=10, pady=5)

        # ========== LEFT SIDE: LOGIN SECTION ==========
        login_frame = ttk.LabelFrame(main_content, text="Login & Setup", padding=15)
        login_frame.pack(side="left", fill="both", padx=(0, 10), pady=5, expand=False)

        # Operator ID
        ttk.Label(login_frame, text="Operator ID (KE0000 or LL0000):", font=("Arial", 10, "bold")).pack(pady=(10, 5), anchor="w")
        self.operator_entry = ttk.Entry(login_frame, textvariable=self.username_var, font=("Arial", 11), width=25)
        self.operator_entry.pack(pady=5, anchor="w")

        # Shift Selection
        ttk.Label(login_frame, text="Shift:", font=("Arial", 10, "bold")).pack(pady=(15, 5), anchor="w")
        self.shift_dropdown = ttk.Combobox(
            login_frame,
            textvariable=self.shift_var,
            values=["---Select Shift---", "A", "B", "C"],
            state="readonly",
            font=("Arial", 11),
            width=23
        )
        self.shift_dropdown.pack(pady=5, anchor="w")
        self.shift_dropdown.current(0)

        # Shipping Mode Selection
        ttk.Label(login_frame, text="Shipping Mode:", font=("Arial", 10, "bold")).pack(pady=(15, 5), anchor="w")
        self.ship_dropdown = ttk.Combobox(
            login_frame,
            textvariable=self.ship_mode_var,
            values=["---Select Mode---", "SEA", "AIR"],
            state="readonly",
            font=("Arial", 11),
            width=23
        )
        self.ship_dropdown.pack(pady=5, anchor="w")
        self.ship_dropdown.current(0)

        # Login Button
        self.login_btn = ttk.Button(
            login_frame,
            text="🔓 Login & Start Scanning",
            command=self.validate_and_login,
            style="Login.TButton"
        )
        self.login_btn.pack(pady=20, fill="x")

        # Separator
        ttk.Separator(login_frame, orient="horizontal").pack(pady=10, fill="x")

        # Printer Status Section
        printer_frame = ttk.LabelFrame(login_frame, text="Printer Connection", padding=10)
        printer_frame.pack(fill="x", pady=10)

        ttk.Label(printer_frame, text="Inner Printer:", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        ttk.Label(printer_frame, text="COM Port:").grid(row=1, column=0, sticky="w", padx=5, pady=3)
        self.inner_port_combo = ttk.Combobox(printer_frame, width=15, state="readonly")
        self.inner_port_combo.grid(row=1, column=1, padx=5, pady=3)

        ttk.Label(printer_frame, text="Baud Rate:").grid(row=2, column=0, sticky="w", padx=5, pady=3)
        self.inner_baud_combo = ttk.Combobox(
            printer_frame,
            width=15,
            state="readonly",
            values=["9600", "19200", "38400", "57600", "115200"]
        )
        self.inner_baud_combo.set("9600")
        self.inner_baud_combo.grid(row=2, column=1, padx=5, pady=3)

        self.inner_status_label = ttk.Label(printer_frame, text="Status: Disconnected", foreground="red")
        self.inner_status_label.grid(row=3, column=0, columnspan=2, pady=3)

        ttk.Label(printer_frame, text="Outer Printer:", font=("Arial", 9, "bold")).grid(row=4, column=0, sticky="w", pady=(10, 5))
        ttk.Label(printer_frame, text="COM Port:").grid(row=5, column=0, sticky="w", padx=5, pady=3)
        self.outer_port_combo = ttk.Combobox(printer_frame, width=15, state="readonly")
        self.outer_port_combo.grid(row=5, column=1, padx=5, pady=3)

        ttk.Label(printer_frame, text="Baud Rate:").grid(row=6, column=0, sticky="w", padx=5, pady=3)
        self.outer_baud_combo = ttk.Combobox(
            printer_frame,
            width=15,
            state="readonly",
            values=["9600", "19200", "38400", "57600", "115200"]
        )
        self.outer_baud_combo.set("9600")
        self.outer_baud_combo.grid(row=6, column=1, padx=5, pady=3)

        self.outer_status_label = ttk.Label(printer_frame, text="Status: Disconnected", foreground="red")
        self.outer_status_label.grid(row=7, column=0, columnspan=2, pady=3)

        # Printer Control Buttons
        button_frame = ttk.Frame(printer_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=10, sticky="ew")

        ttk.Button(
            button_frame,
            text="Refresh Ports",
            command=self.refresh_ports,
            style="Refresh.TButton",
            width=15
        ).pack(side="left", padx=2)

        self.connect_btn = ttk.Button(
            button_frame,
            text="Connect",
            command=self.toggle_connection,
            style="Connect.TButton",
            width=15
        )
        self.connect_btn.pack(side="left", padx=2)

        # ========== RIGHT SIDE: SCANNING & OPERATIONS ==========
        right_panel = ttk.Frame(main_content)
        right_panel.pack(side="right", fill="both", expand=True, pady=5)

        # COMBINED: Operator Session, Box Configuration, and Pallet Progress (Side-by-side)
        self.operator_info_frame = ttk.LabelFrame(right_panel, text="Session & Progress", padding=10)
        self.operator_info_frame.pack(fill="x", pady=(0, 10))

        # Create three columns: Left (Session), Middle (Config), Right (Separator + Progress)
        left_session = ttk.Frame(self.operator_info_frame)
        left_session.pack(side="left", fill="y", padx=(0, 10))

        middle_config = ttk.Frame(self.operator_info_frame)
        middle_config.pack(side="left", fill="y", padx=(0, 15))

        right_progress = ttk.Frame(self.operator_info_frame)
        right_progress.pack(side="right", fill="both", expand=True)

        # ===== LEFT COLUMN: Operator Session =====
        ttk.Label(left_session, text="Operator Session", font=("Arial", 9, "bold")).pack(anchor="w", pady=(0, 5))

        self.operator_label = ttk.Label(left_session, text="Operator: Not Logged In", font=("Arial", 9))
        self.operator_label.pack(anchor="w")

        self.shift_label = ttk.Label(left_session, text="Shift: --", font=("Arial", 9))
        self.shift_label.pack(anchor="w")

        self.mode_label = ttk.Label(left_session, text="Mode: --", font=("Arial", 9))
        self.mode_label.pack(anchor="w")

        logout_btn = ttk.Button(
            left_session,
            text="Logout",
            command=self.logout,
            style="Logout.TButton",
            width=18
        )
        logout_btn.pack(pady=(10, 0))

        # ===== MIDDLE COLUMN: Box Configuration =====
        ttk.Label(middle_config, text="Box Configuration", font=("Arial", 9, "bold")).pack(anchor="w", pady=(0, 5))

        config_frame = ttk.Frame(middle_config)
        config_frame.pack(fill="x", padx=5)

        ttk.Label(config_frame, text="Shipping Mode:").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.mode_display_label = ttk.Label(config_frame, text="--", font=("Arial", 10, "bold"))
        self.mode_display_label.grid(row=0, column=1, padx=5, pady=3, sticky="w")

        ttk.Label(config_frame, text="Boxes per Pallet:").grid(row=1, column=0, padx=5, pady=3, sticky="w")
        self.box_dropdown = ttk.Combobox(config_frame, textvariable=self.box_count_var, state="readonly", width=15)
        self.box_dropdown.grid(row=1, column=1, padx=5, pady=3, sticky="w")

        self.capacity_label = ttk.Label(config_frame, text="Total Capacity: -- units", font=("Arial", 9), foreground="blue")
        self.capacity_label.grid(row=2, column=0, columnspan=2, padx=5, pady=3)

        # Keep self.box_count_frame for compatibility
        self.box_count_frame = config_frame

        # ===== RIGHT COLUMN: Separator + Pallet Progress =====
        # Vertical separator line
        ttk.Separator(right_progress, orient="vertical").pack(side="left", fill="y", padx=(0, 15))

        # Pallet Progress Section
        pallet_content = ttk.Frame(right_progress)
        pallet_content.pack(side="right", fill="both", expand=True)

        ttk.Label(pallet_content, text="Pallet Progress", font=("Arial", 9, "bold")).pack(anchor="w", pady=(0, 5))

        progress_inner = ttk.Frame(pallet_content)
        progress_inner.pack(fill="x", padx=5)

        self.pallet_label = ttk.Label(progress_inner, text="Current Pallet: 1", font=("Arial", 11, "bold"))
        self.pallet_label.pack(pady=3)

        self.unit_label = ttk.Label(progress_inner, text="Units: 0 / 0", font=("Arial", 10))
        self.unit_label.pack(pady=2)

        self.batch_count_label = ttk.Label(progress_inner, text="DB Batch Count: --", font=("Arial", 9), foreground="#0066CC")
        self.batch_count_label.pack(pady=2)

        self.batch_label = ttk.Label(progress_inner, text="Batch Code: Not Set", font=("Arial", 9), foreground="orange")
        self.batch_label.pack(pady=3)

        self.progress_bar = ttk.Progressbar(progress_inner, length=250, mode='determinate')
        self.progress_bar.pack(pady=(3, 5), fill="x")

        # Keep self.progress_frame for compatibility
        self.progress_frame = progress_inner

        # BARCODE SCANNING SECTION (disabled until login)
        scan_frame = ttk.LabelFrame(right_panel, text="Barcode Scanning", padding=10)
        scan_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(scan_frame, text="Serial Number:").pack(side="left", padx=5)
        self.serial_entry = ttk.Entry(scan_frame, font=("Arial", 12), width=25, state="disabled")
        self.serial_entry.pack(side="left", padx=5)
        self.serial_entry.bind('<Return>', self.on_serial_enter)

        # RESULT & LOG SECTION (disabled until login) - Side-by-side with separator
        result_log_container = ttk.Frame(right_panel)
        result_log_container.pack(fill="both", expand=True)

        # RESULT BOX (left side)
        result_frame = ttk.LabelFrame(result_log_container, text="Result", padding=10)
        result_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.result_box = scrolledtext.ScrolledText(result_frame, height=5, state="disabled")
        self.result_box.pack(fill="both", expand=True)

        # VERTICAL SEPARATOR
        ttk.Separator(result_log_container, orient="vertical").pack(side="left", fill="y", padx=5)

        # LOG SECTION (right side)
        log_frame = ttk.LabelFrame(result_log_container, text="Activity Log", padding=10)
        log_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        self.log_box = scrolledtext.ScrolledText(log_frame, height=5, state="disabled", font=("Courier", 9))
        self.log_box.pack(fill="both", expand=True)

        # Store widgets that should be disabled until login
        self.scanning_widgets = [
            self.serial_entry, self.result_box, self.log_box,
            self.box_dropdown, self.progress_bar, self.pallet_label, self.unit_label,
            self.batch_count_label, self.batch_label, self.capacity_label
        ]

    def disable_scanning_interface(self):
        """Disable scanning interface until login"""
        self.serial_entry.config(state="disabled")
        self.result_box.config(state="disabled")
        self.log_box.config(state="disabled")
        self.box_dropdown.config(state="disabled")

    def enable_scanning_interface(self):
        """Enable scanning interface after login"""
        self.serial_entry.config(state="normal")
        self.result_box.config(state="normal")
        self.log_box.config(state="normal")
        self.box_dropdown.config(state="readonly")

    def disable_login_interface(self):
        """Disable login fields and button after successful login"""
        self.operator_entry.config(state="disabled")
        self.shift_dropdown.config(state="disabled")
        self.ship_dropdown.config(state="disabled")
        self.login_btn.config(state="disabled")

    def enable_login_interface(self):
        """Enable login fields and button for logout"""
        self.operator_entry.config(state="normal")
        self.shift_dropdown.config(state="readonly")
        self.ship_dropdown.config(state="readonly")
        self.login_btn.config(state="normal")

    def update_operator_info_display(self):
        """Update operator info display after login"""
        self.operator_label.config(text=f"Operator: {self.username}")
        self.shift_label.config(text=f"Shift: {self.shift}")
        self.mode_label.config(text=f"Mode: {self.ship_mode}")
        self.mode_display_label.config(text=self.ship_mode.upper())

    def refresh_ports(self):
        """Refresh available COM ports"""
        ports = self.printer.list_ports()
        if ports:
            self.inner_port_combo['values'] = ports
            self.outer_port_combo['values'] = ports
            if len(ports) > 0:
                self.inner_port_combo.current(0)
            if len(ports) > 1:
                self.outer_port_combo.current(1)
        else:
            messagebox.showwarning("No Ports", "No COM ports detected!")
            self.inner_port_combo['values'] = []
            self.outer_port_combo['values'] = []

    def toggle_connection(self):
        """Connect or disconnect printers"""
        if self.printer.is_all_connected():
            self.printer.disconnect_all()
            self.inner_status_label.config(text="Status: Disconnected", foreground="red")
            self.outer_status_label.config(text="Status: Disconnected", foreground="red")
            self.connect_btn.config(text="Connect Both")
        else:
            # Refresh ports before attempting connection (fixes stale port issues after restart)
            self.refresh_ports()
            self.root.update()  # Allow UI to update
            
            inner_port = self.inner_port_combo.get().strip()
            outer_port = self.outer_port_combo.get().strip()
            
            if not inner_port or not outer_port:
                messagebox.showerror("Error", "Please select ports for both printers!\n\nClick 'Refresh Ports' first if dropdown is empty.")
                return

            if inner_port == outer_port:
                messagebox.showerror("Error", "Inner and Outer printers cannot use the same port!")
                return

            try:
                inner_baud = int(self.inner_baud_combo.get())
                outer_baud = int(self.outer_baud_combo.get())
            except ValueError:
                messagebox.showerror("Error", "Invalid baud rate selected!")
                return

            # Validate ports exist before attempting connection
            available_ports = self.printer.list_ports()
            print(f"[DEBUG] Available ports: {available_ports}")
            print(f"[DEBUG] Trying to connect Inner: {inner_port} ({inner_baud}), Outer: {outer_port} ({outer_baud})")
            
            if not available_ports:
                messagebox.showerror("No Ports Available", 
                    "No COM ports detected!\n\n"
                    "Please:\n"
                    "1. Check USB connections\n"
                    "2. Check device manager for the ports\n"
                    "3. Click 'Refresh Ports' again")
                return
            
            if inner_port not in available_ports:
                messagebox.showerror("Port Error", 
                    f"Inner printer port {inner_port} is not available!\n\n"
                    f"Available ports: {', '.join(available_ports)}\n\n"
                    "Click 'Refresh Ports' to update the list.")
                return
            
            if outer_port not in available_ports:
                messagebox.showerror("Port Error", 
                    f"Outer printer port {outer_port} is not available!\n\n"
                    f"Available ports: {', '.join(available_ports)}\n\n"
                    "Click 'Refresh Ports' to update the list.")
                return

            # Attempt connection
            inner_ok = self.printer.connect_inner(inner_port, inner_baud)
            outer_ok = self.printer.connect_outer(outer_port, outer_baud)

            if inner_ok:
                self.inner_status_label.config(text="Status: Connected", foreground="green")
            else:
                self.inner_status_label.config(text="Status: Failed", foreground="red")

            if outer_ok:
                self.outer_status_label.config(text="Status: Connected", foreground="green")
            else:
                self.outer_status_label.config(text="Status: Failed", foreground="red")

            if inner_ok and outer_ok:
                self.connect_btn.config(text="Disconnect Both")
                messagebox.showinfo("Success", "Both printers connected successfully!")
            else:
                # Show which printers failed
                failed = []
                if not inner_ok:
                    failed.append(f"Inner ({inner_port})")
                if not outer_ok:
                    failed.append(f"Outer ({outer_port})")
                
                error_msg = f"Failed to connect: {', '.join(failed)}\n\n"
                error_msg += "Troubleshooting steps:\n"
                error_msg += "1. Unplug the USB cable from both printers\n"
                error_msg += "2. Wait 5 seconds\n"
                error_msg += "3. Plug the USB cables back in\n"
                error_msg += "4. Click 'Refresh Ports'\n"
                error_msg += "5. Try connecting again"
                
                messagebox.showerror("Connection Failed", error_msg)

    def create_box_dropdown(self):
        """Create box configuration dropdown"""
        if self.ship_mode.upper() == "SEA":
            options = ["100", "120", "150"]
        elif self.ship_mode.upper() == "AIR":
            options = ["50", "75", "100"]
        else:
            options = []

        self.box_dropdown['values'] = options
        if options:
            self.box_count_var.set(options[0])
        
        self.update_pallet_capacity()

    def update_pallet_capacity(self):
        """Update pallet capacity display"""
        try:
            box_count = int(self.box_count_var.get())
            self.total_units_per_pallet = box_count * 2  # 2 units per box
            capacity_text = f"Total Capacity: {self.total_units_per_pallet} units"
            self.capacity_label.config(text=capacity_text)
            self.update_progress_display()
        except (ValueError, tk.TclError):
            pass

    def on_serial_enter(self, event):
        """Handle serial entry and check database"""
        if not self.is_logged_in:
            messagebox.showwarning("Not Logged In", "Please login first before scanning")
            return
        
        serial_num = self.serial_entry.get().strip()
        if serial_num:
            self.check_serial_in_db(serial_num)

    def check_serial_in_db(self, serial_num):
        """Check serial in database and handle printing"""
        # Validate input
        if not serial_num:
            messagebox.showerror("Error", "Please enter a serial number")
            return

        # Check box selection
        if self.total_units_per_pallet == 0:
            messagebox.showerror("Error", "Please select a box configuration first")
            return

        # Validate serial in database
        batch_code, po_num = self.db.get_batch_and_po(serial_num)
        if not batch_code or not po_num:
            messagebox.showerror("Not Found", f"Serial {serial_num} not found in database")
            self.serial_entry.delete(0, tk.END)
            self.serial_entry.focus()
            return

        # Check if serial is already packaged
        existing_packaging = self.insert_db.check_existing_packaging(serial_num, po_num, batch_code)
        
        if existing_packaging:
            # Serial already exists - ask if user wants to reprint
            result = messagebox.askyesno(
                "Serial Already Packaged",
                f"Serial {serial_num} is already in the database.\n\n"
                f"Do you want to reprint the inner label?"
            )
            
            if result:
                # User chose to reprint
                self.log(f"🔄 Reprinting label for serial: {serial_num}")
                
                # Update status to 1 in database
                if self.insert_db.update_packaging_status(serial_num, po_num, batch_code):
                    self.log(f"✅ Status updated to 1 for reprint")
                    self.write_to_result_box(f"✅ Serial: {serial_num}\n→ Reprinting Inner Label\n→ Status: Updated\n")
                else:
                    self.log(f"⚠️ Failed to update status")
                    messagebox.showerror("Database Error", "Failed to update status")
            else:
                # User chose not to reprint
                self.log(f"⏭️ Skipped reprint for serial: {serial_num}")
            
            # Clear entry and refocus
            self.serial_entry.delete(0, tk.END)
            self.serial_entry.focus()
            return

        # Display validation success
        self.write_to_result_box(f"✅ Serial: {serial_num}\n→ Batch Code: {batch_code}\n→ PO Number: {po_num}\n")
        
        # Get existing count and calculate box numbers
        existing_count = self.insert_db.get_batch_unit_count(batch_code, po_num)
        next_unit = existing_count + 1
        current_innerbox = ((next_unit - 1) // self.units_per_innerbox) + 1
        current_outerbox = ((current_innerbox - 1) // self.innerboxes_per_outerbox) + 1
        
        self.log(f"📊 Database check: {existing_count} units already packaged for batch {batch_code}")
        self.update_batch_count_display(batch_code, po_num)

        # Record to database
        success = self.insert_db.record_operator_activity(
            operator=self.username,
            shift=self.shift,
            serial_num=serial_num,
            batch_code=batch_code,
            po_num=po_num,
            ship_mode=self.ship_mode,
            innerbox=current_innerbox,
            outerbox=current_outerbox,
            pallet_num=self.pallet_count
        )
        
        if not success:
            messagebox.showerror("Database Error", "Failed to record packaging")
            self.serial_entry.delete(0, tk.END)
            self.serial_entry.focus()
            return
        
        self.log(f"✅ Database record successful (innerbox={current_innerbox}, outerbox={current_outerbox})")
        
        # Update counters
        self.unit_count += 1
        self.log(f"📊 Local unit count updated: {self.unit_count}/{self.total_units_per_pallet}")
        self.update_progress_display()
        
        # Update database status
        if self.insert_db.update_packaging_status(serial_num, po_num, batch_code):
            self.log(f"✅ Packaging status updated")
        else:
            self.log(f"⚠️ Failed to update packaging status")

        # Check if pallet is complete
        if self.unit_count >= self.total_units_per_pallet:
            messagebox.showinfo(
                "Pallet Complete", 
                f"🎉 Pallet {self.pallet_count} is complete!\n"
                f"Total units: {self.unit_count}\n"
                f"Starting new pallet..."
            )
            self.log(f"🎉 PALLET {self.pallet_count} COMPLETED - Starting new pallet")
            self.pallet_count += 1
            self.unit_count = 0
            self.current_pallet_batch_code = None
            self.batch_label.config(text="Batch Code: Not Set", foreground="orange")
            self.update_progress_display()
        
        # Clear entry and refocus
        self.serial_entry.delete(0, tk.END)
        self.serial_entry.focus()
        self.log(f"{'='*60}")

    def update_progress_display(self):
        """Update progress display"""
        self.pallet_label.config(text=f"Current Pallet: {self.pallet_count}")
        self.unit_label.config(text=f"Units: {self.unit_count} / {self.total_units_per_pallet}")
        
        if self.total_units_per_pallet > 0:
            progress = (self.unit_count / self.total_units_per_pallet) * 100
            self.progress_bar['value'] = progress
        else:
            self.progress_bar['value'] = 0

    def refresh_batch_count(self):
        """Manually refresh batch count display"""
        if self.current_pallet_batch_code:
            self.update_batch_count_display(self.current_pallet_batch_code, self.po_num)
            self.log("🔄 Batch count refreshed")

    def update_batch_count_display(self, batch_code=None, po_num=None):
        """Update batch count display"""
        if batch_code and po_num:
            try:
                count = self.insert_db.get_batch_unit_count(batch_code, po_num)
                self.batch_count_label.config(text=f"DB Batch Count: {count}")
                self.current_pallet_batch_code = batch_code
                self.batch_label.config(text=f"Batch Code: {batch_code}", foreground="green")
            except Exception as e:
                self.log(f"⚠️ Error updating batch count: {e}")

    def log(self, msg):
        """Add message to log box"""
        self.log_box.insert(tk.END, msg + "\n")
        self.log_box.see(tk.END)

    def write_to_result_box(self, text):
        """Write to result box"""
        self.result_box.insert(tk.END, text)
        self.result_box.see(tk.END)

    def logout(self):
        """Handle logout and return to login state"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.username_var.set("")
            self.shift_var.set("")
            self.ship_mode_var.set("")
            self.username = None
            self.shift = None
            self.ship_mode = None
            self.shift_warning_count = 0
            self.pallet_count = 1
            self.unit_count = 0
            self.box_count_var.set("")
            self.is_logged_in = False
            
            # Clear displays
            self.operator_label.config(text="Operator: Not Logged In")
            self.shift_label.config(text="Shift: --")
            self.mode_label.config(text="Mode: --")
            self.mode_display_label.config(text="--")
            self.serial_entry.delete(0, tk.END)
            self.result_box.config(state="normal")
            self.result_box.delete(1.0, tk.END)
            self.result_box.config(state="disabled")
            self.log_box.config(state="normal")
            self.log_box.delete(1.0, tk.END)
            self.log_box.config(state="disabled")
            self.batch_label.config(text="Batch Code: Not Set", foreground="orange")
            self.batch_count_label.config(text="DB Batch Count: --")
            self.pallet_label.config(text="Current Pallet: 1")
            self.unit_label.config(text="Units: 0 / 0")
            self.progress_bar['value'] = 0
            
            # Disable scanning interface
            self.disable_scanning_interface()
            
            # Enable login interface
            self.enable_login_interface()

    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Do you really want to exit?"):
            self.printer.disconnect_all()
            self.root.destroy()


# ============================================
# SECTION 7: MAIN ENTRY POINT
# ============================================

if __name__ == "__main__":
    root = tk.Tk()
    app = ZPLPrinterGUI(root)
    
    # Set the close protocol
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start the main event loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
