# beacon_scanner_production_mysql.py
#
# Production Beacon Scanner v1.0 - Refactored with Production GUI + MySQL
# - Operator Login in main GUI
# - BLED112 BGAPI scanning (pygatt)
# - Production-style interface
# - All safety features preserved
"""
Merged changes:
- MySQL integration: inserts into mainboard_blescan and updates mainboard_main
- CSV logging unified to a single CSV matching mainboard_blescan columns
- Enforced max scan timeout = 15s
- Smart early stop: scanning stops immediately when DUT MAC found
- Test repetition handling and serial naming as specified
- FIXED: Removed 'id' column references to fix database error
"""
import os
import csv
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import platform
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext

# Windows sounds
if platform.system() == "Windows":
    import winsound

# Try to import pygatt BGAPI backend
try:
    import pygatt
    from pygatt.backends.bgapi.bgapi import BGAPIBackend
    PYGATT_OK = True
    PYGATT_ERR = None
except Exception as e:
    PYGATT_OK = False
    PYGATT_ERR = str(e)

# MySQL connector
try:
    import mysql.connector
    from mysql.connector import Error
    MYSQL_OK = True
except Exception:
    MYSQL_OK = False

# ============================================================================
# CONFIGURATION
# ============================================================================
class Config:
    """Application configuration constants"""
    DEFAULT_COM = "COM5"
    DEFAULT_SCAN_TIMEOUT = 8  # default displayed; enforced max 15s in code
    MAX_SCAN_TIMEOUT = 20
    LOGS_DIR = "logs"
    LOG_FILENAME = "BeaconScanner_Log.csv"
    DESKTOP_COPY_NAME = "BeaconScanner_Log_COPY.csv"
    
    # CSV headers now match the mainboard_blescan schema
    CSV_HEADERS = [
        "serial_num", "po_num", "operator_en", "shift", "date_time",
        "mac_address", "rssi", "test_rep", "remarks", "status"
    ]
    
    # Colors matching production style
    COLOR_BG = "#1a1a1a"
    COLOR_FG = "white"
    COLOR_PASS = "#00ff00"
    COLOR_FAIL = "#ff0000"
    COLOR_WARN = "#ffaa00"
    COLOR_INPUT_BG = "#2d2d2d"


# ============================================================================
# DATABASE CONFIG
# ============================================================================
class DBConfig:
    HOST = "192.168.1.38"
    USER = "testing"
    PASSWORD = "testing"
    DATABASE = "synaptron"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
class Utils:
    """Utility functions for MAC formatting, file operations, and sounds"""
    
    @staticmethod
    def normalize_mac(mac: str) -> str:
        """Return uppercase contiguous hex string without separators (12 chars)."""
        if not mac:
            return ""
        chars = [c for c in str(mac).strip() if c.isalnum()]
        return "".join(chars).upper()
    
    @staticmethod
    def pretty_mac(norm: str) -> str:
        """Return colon-separated MAC if 12 hex chars, else original."""
        if not norm or len(norm) != 12:
            return norm
        return ":".join(norm[i:i+2] for i in range(0, 12, 2))
    
    @staticmethod
    def bytes_to_hex(b: bytes) -> str:
        """Convert bytes to uppercase hex string"""
        return b.hex().upper() if b else ""
    
    @staticmethod
    def set_windows_readonly(path: str) -> None:
        """Set windows readonly attribute (best-effort)"""
        if platform.system() != "Windows":
            return
        try:
            os.system(f'attrib +R "{path}"')
        except Exception:
            pass
    
    @staticmethod
    def remove_windows_readonly(path: str) -> None:
        """Remove windows readonly attribute (best-effort)"""
        if platform.system() != "Windows":
            return
        try:
            os.system(f'attrib -R "{path}"')
        except Exception:
            pass
    
    @staticmethod
    def copy_to_desktop(src_path: str, dest_name: str) -> None:
        """Copy file to desktop"""
        try:
            desktop = Path.home() / "Desktop"
            if not desktop.is_dir():
                return
            dest = desktop / dest_name
            import shutil
            shutil.copy(src_path, dest)
        except Exception:
            pass


class SoundPlayer:
    """Handle sound notifications"""
    
    @staticmethod
    def beep_pass() -> None:
        if platform.system() == "Windows":
            try:
                winsound.Beep(1400, 160)
            except Exception:
                pass
    
    @staticmethod
    def beep_fail() -> None:
        if platform.system() == "Windows":
            try:
                winsound.Beep(600, 400)
            except Exception:
                pass
    
    @staticmethod
    def beep_warn() -> None:
        if platform.system() == "Windows":
            try:
                winsound.Beep(900, 220)
            except Exception:
                pass


# ============================================================================
# LOG MANAGEMENT
# ============================================================================
class LogManager:
    """Manages CSV logging and historical data loading"""
    
    def __init__(self, logs_dir: str, log_filename: str):
        self.logs_dir = Path(logs_dir)
        self.logfile = self.logs_dir / log_filename
        self.logs_dir.mkdir(exist_ok=True)
        self._ensure_logfile_header()
    
    def _ensure_logfile_header(self) -> None:
        """Create logfile with header if it doesn't exist"""
        if not self.logfile.exists():
            try:
                with open(self.logfile, "w", newline='', encoding='utf-8') as f:
                    csv.writer(f).writerow(Config.CSV_HEADERS)
                Utils.set_windows_readonly(str(self.logs_dir))
                Utils.set_windows_readonly(str(self.logfile))
            except Exception:
                pass
    
    def load_pass_entries(self) -> Tuple[Set[str], Set[str]]:
        """Load PASS MACs and Serials from all CSV files (backwards compatibility)"""
        pass_macs = set()
        pass_serials = set()
        
        try:
            for csv_file in self.logs_dir.glob("*.csv"):
                self._process_csv_file(csv_file, pass_macs, pass_serials)
        except Exception:
            pass
        
        return pass_macs, pass_serials
    
    def _process_csv_file(self, filepath: Path, pass_macs: Set[str], 
                          pass_serials: Set[str]) -> None:
        """Process a single CSV file for PASS entries"""
        try:
            with open(filepath, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader, None)
                
                if not headers:
                    return
                
                indices = self._get_column_indices(headers)
                
                for row in reader:
                    self._extract_pass_data(row, indices, pass_macs, pass_serials)
        except Exception:
            pass
    
    @staticmethod
    def _get_column_indices(headers: List[str]) -> Dict[str, int]:
        """Determine column indices from headers"""
        # default mapping if different schema present
        mapping = {'serial': 0, 'mac': 5, 'result': 9}
        for i, header in enumerate(headers):
            hl = header.strip().lower()
            if hl in ("mac", "device", "address", "mac_address"):
                mapping['mac'] = i
            elif hl in ("result", "status"):
                mapping['result'] = i
            elif hl in ("serial", "serial_num", "serialnumber", "sn"):
                mapping['serial'] = i
        return mapping
    
    @staticmethod
    def _extract_pass_data(row: List[str], indices: Dict[str, int],
                          pass_macs: Set[str], pass_serials: Set[str]) -> None:
        """Extract MAC and Serial from row if result is PASS"""
        try:
            mac = Utils.normalize_mac(row[indices['mac']]) if len(row) > indices['mac'] else ""
            result = row[indices['result']].strip() if len(row) > indices['result'] else ""
            serial = row[indices['serial']].strip() if len(row) > indices['serial'] else ""
            
            if result.upper().startswith("PASS") or result == "1":
                if mac:
                    pass_macs.add(mac)
                if serial:
                    pass_serials.add(serial)
        except Exception:
            pass
    
    def write_log_entry(self, serial_num: str, po_num: str, operator_en: str, shift: str,
                        date_time: str, mac_address: str, rssi: Optional[int],
                        test_rep: int, remarks: str, status: int) -> None:
        """Write a single log entry to CSV (consolidated file)"""
        rssi_s = str(rssi) if rssi is not None else ""
        
        Utils.remove_windows_readonly(str(self.logfile))
        Utils.remove_windows_readonly(str(self.logs_dir))
        
        try:
            with open(self.logfile, "a", newline='', encoding='utf-8') as f:
                csv.writer(f).writerow([
                    serial_num, po_num, operator_en, shift, date_time,
                    mac_address, rssi_s, test_rep, remarks, status
                ])
        except Exception:
            pass
        
        Utils.copy_to_desktop(str(self.logfile), Config.DESKTOP_COPY_NAME)
        Utils.set_windows_readonly(str(self.logfile))
        Utils.set_windows_readonly(str(self.logs_dir))


# ============================================================================
# BLE SCANNER
# ============================================================================
class BleScanner:
    """Manages BLED112 BGAPI scanning operations (incremental for early stop)"""
    
    def __init__(self, com_port: str = Config.DEFAULT_COM):
        self.com_port = com_port
        self.adapter = None
        self.started = False
        self.lock = threading.Lock()
    
    def start_adapter(self) -> None:
        """Start BGAPI adapter. May raise on failure."""
        if not PYGATT_OK:
            raise RuntimeError(f"pygatt not available: {PYGATT_ERR or 'unknown'}")
        
        with self.lock:
            if self.adapter and self.started:
                return
            self.adapter = BGAPIBackend(serial_port=self.com_port)
            self.adapter.start()
            self.started = True
    
    def stop_adapter(self) -> None:
        """Stop the adapter"""
        with self.lock:
            try:
                if self.adapter and self.started:
                    self.adapter.stop()
            except Exception:
                pass
            self.adapter = None
            self.started = False
    
    def scan_once(self, timeout: int = Config.DEFAULT_SCAN_TIMEOUT,
                  target_mac: Optional[str] = None) -> List[Dict]:
        """
        Perform scanning with incremental slices to allow early stop.
        If target_mac is provided, stop as soon as it's found.
        """
        if not PYGATT_OK:
            return []
        
        if not (self.adapter and self.started):
            self.start_adapter()
        
        devices_accum: Dict[str, Dict] = {}
        start = time.time()
        elapsed = 0.0
        slice_sec = 1  # 1 second per slice for responsiveness
        
        while elapsed < timeout:
            remaining = timeout - elapsed
            this_slice = min(slice_sec, remaining)
            try:
                found = self.adapter.scan(timeout=this_slice)
            except Exception:
                # Scan failure — return what we have
                break
            
            # process devices returned
            for d in found:
                p = self._process_device(d)
                devices_accum[p['address']] = p
            
            # if target_mac seen, return immediately (early stop)
            if target_mac and target_mac in devices_accum:
                return list(devices_accum.values())
            
            elapsed = time.time() - start
        
        return list(devices_accum.values())
    
    def _process_device(self, device: Dict) -> Dict:
        """Process a single device from scan results"""
        addr = device.get('address') or device.get('mac') or ""
        norm = Utils.normalize_mac(addr)
        name = device.get('name') or ""
        rssi = device.get('rssi')
        mfg_bytes = self._extract_manufacturer_data(device)
        
        return {
            'address': norm,
            'name': name,
            'rssi': rssi,
            'mfg_bytes': mfg_bytes,
            'raw': device
        }
    
    @staticmethod
    def _extract_manufacturer_data(device: Dict) -> Optional[bytes]:
        """Extract manufacturer data from device dictionary"""
        if 'manufacturer_data' in device and isinstance(device['manufacturer_data'], dict):
            vals = list(device['manufacturer_data'].values())
            if vals:
                try:
                    return bytes(vals[0])
                except Exception:
                    pass
        
        for key in ('data', 'adv_data', 'advertisement', 'raw_data'):
            if key in device and device[key]:
                val = device[key]
                if isinstance(val, (bytes, bytearray)):
                    return bytes(val)
                if isinstance(val, dict):
                    for vv in val.values():
                        if isinstance(vv, (bytes, bytearray)):
                            return bytes(vv)
        
        return None


# ============================================================================
# DATABASE HELPERS
# ============================================================================
class DBHelper:
    """Simple helper functions for DB operations"""
    
    @staticmethod
    def _get_connection():
        if not MYSQL_OK:
            raise RuntimeError("mysql.connector is not available")
        return mysql.connector.connect(
            host=DBConfig.HOST,
            user=DBConfig.USER,
            password=DBConfig.PASSWORD,
            database=DBConfig.DATABASE,
            autocommit=False
        )
    
    @staticmethod
    def check_programming_passed(base_serial: str) -> Tuple[bool, Optional[str]]:
        """
        Return (passed, error_message). Check mainboard_main.programming == 1
        Returns False if no record exists or programming != 1
        """
        try:
            conn = DBHelper._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT programming FROM mainboard_main WHERE serial_num = %s", (base_serial,))
            row = cur.fetchone()
            cur.close()
            conn.close()
            if not row:
                return False, "No record found in mainboard_main for this serial number"
            programming = row[0]
            if programming != 1:
                return False, "Programming stage not passed (programming != 1)"
            return True, None
        except Error as e:
            return False, str(e)
    
    @staticmethod
    def fetch_existing_blescan(base_serial: str) -> List[Dict]:
        """
        Returns existing rows for this base serial (serial_num LIKE base_serial%)
        as list of dicts: {'serial_num':..., 'test_rep':...}
        """
        rows = []
        try:
            conn = DBHelper._get_connection()
            cur = conn.cursor()
            like_pattern = base_serial + '%'
            cur.execute("SELECT serial_num, test_rep FROM mainboard_blescan WHERE serial_num LIKE %s", (like_pattern,))
            for r in cur.fetchall():
                rows.append({'serial_num': r[0], 'test_rep': r[1]})
            cur.close()
            conn.close()
        except Exception:
            pass
        return rows
    
    @staticmethod
    def insert_blescan_and_update_main(base_serial: str, store_serial: str, po_num: str,
                                       operator_en: str, shift: str, date_time: str,
                                       mac_address: str, rssi: Optional[int],
                                       test_rep: int, remarks: str, status: int) -> Tuple[bool, Optional[str]]:
        """
        Inserts a row into mainboard_blescan and updates mainboard_main.blescan flag.
        Also renames older rows' serial_num so newest entry stays as base_serial (no underscore).
        Returns (success, error_message)
        """
        try:
            conn = DBHelper._get_connection()
            cur = conn.cursor()
            # Fetch existing rows with their test_rep and serial_num
            cur.execute("SELECT serial_num, test_rep FROM mainboard_blescan WHERE serial_num LIKE %s FOR UPDATE", (base_serial + '%',))
            existing = cur.fetchall()  # list of (serial_num, test_rep)
            existing_count = len(existing)
            new_test_rep = existing_count + 1
            
            # Update serials of existing rows so that oldest gets highest suffix,
            # and newest (to be inserted) will be base_serial (no suffix)
            for (old_serial, old_test_rep) in existing:
                # compute new suffix relative to new_test_rep
                suffix = new_test_rep - old_test_rep
                if suffix > 0:
                    new_serial_name = f"{base_serial}_{suffix}"
                else:
                    new_serial_name = base_serial
                # Update using WHERE serial_num = old_serial
                cur.execute("UPDATE mainboard_blescan SET serial_num = %s WHERE serial_num = %s", (new_serial_name, old_serial))
            
            # Now insert the new (latest) entry with serial = base_serial (no suffix)
            insert_q = """
                INSERT INTO mainboard_blescan
                (serial_num, po_num, operator_en, shift, date_time, mac_address, rssi, test_rep, remarks, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(insert_q, (
                base_serial, po_num, operator_en, shift, date_time, mac_address,
                rssi if rssi is not None else None, new_test_rep, remarks, status
            ))
            
            # Update mainboard_main.blescan according to status
            cur.execute("UPDATE mainboard_main SET blescan = %s WHERE serial_num = %s", (1 if status == 1 else 0, base_serial))
            
            conn.commit()
            cur.close()
            conn.close()
            return True, None
        except Error as e:
            try:
                conn.rollback()
            except Exception:
                pass
            try:
                cur.close()
                conn.close()
            except Exception:
                pass
            return False, str(e)


# ============================================================================
# SCAN RESULT HANDLER
# ============================================================================
class ScanResultHandler:
    """Handles scan result evaluation and recording"""
    
    def __init__(self, log_manager: LogManager, global_pass_macs: Set[str],
                 global_pass_serials: Set[str], session_scanned: Set[str]):
        self.log_manager = log_manager
        self.global_pass_macs = global_pass_macs
        self.global_pass_serials = global_pass_serials
        self.session_scanned = session_scanned
        # Track test_rep per serial for this session (in case DB is unavailable)
        self.session_test_reps: Dict[str, int] = {}
    
    def get_next_test_rep(self, base_serial: str) -> int:
        """Get the next test_rep for a serial (increment session counter)"""
        if base_serial not in self.session_test_reps:
            # First test for this serial in session
            # Try to get from DB first
            try:
                if MYSQL_OK:
                    from . import DBHelper
                    existing = DBHelper.fetch_existing_blescan(base_serial)
                    self.session_test_reps[base_serial] = len(existing)
                else:
                    self.session_test_reps[base_serial] = 0
            except Exception:
                self.session_test_reps[base_serial] = 0
        
        # Increment for this test
        self.session_test_reps[base_serial] += 1
        return self.session_test_reps[base_serial]
    
    def check_serial_duplicate(self, serial: str) -> bool:
        """Check if serial number already passed"""
        return serial in self.global_pass_serials
    
    def check_mac_duplicate(self, norm_mac: str) -> Tuple[bool, str]:
        """Check if MAC is duplicate. Returns (is_duplicate, reason)"""
        if norm_mac in self.global_pass_macs:
            return True, "MAC previously passed"
        if norm_mac in self.session_scanned:
            return True, "Duplicate entry this session"
        return False, ""
    
    def record_result(self, operator: str, shift: str, po: str, serial: str,
                     norm_mac: str, result: str, remarks: str,
                     rssi: Optional[int], rawhex: str,
                     update_globals: bool = True) -> Dict:
        """Record a scan result and return UI update info (NO CSV logging here)"""
        # Keep CSV-friendly serial for immediate UI; CSV logging done elsewhere
        mac_pretty = Utils.pretty_mac(norm_mac)
        
        # Decide status int
        status_int = 1 if result.upper().startswith("PASS") else 0
        
        # Timestamp string
        dt_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Update globals if pass
        if update_globals and result.upper().startswith("PASS"):
            if norm_mac:
                self.global_pass_macs.add(norm_mac)
            if serial:
                self.global_pass_serials.add(serial)
        
        if result.upper().startswith("FAIL") and norm_mac in self.session_scanned:
            self.session_scanned.discard(norm_mac)
        
        return {
            'serial': serial,
            'mac': mac_pretty,
            'result': result,
            'remarks': remarks,
            'rssi': rssi,
            'rawhex': rawhex,
            'date_time': dt_now,
            'status': status_int,
        }


# ============================================================================
# MAIN APPLICATION
# ============================================================================
class BeaconScannerApp:
    """Main application window and logic"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.operator = ""
        self.shift = ""
        self.po = ""
        
        # Initialize components
        self.log_manager = LogManager(Config.LOGS_DIR, Config.LOG_FILENAME)
        self.scanner = BleScanner(Config.DEFAULT_COM)
        
        # Load historical data
        global_pass_macs, global_pass_serials = self.log_manager.load_pass_entries()
        
        # Session state
        self.session_scanned = set()
        self.current_sn = ""
        self.pass_count = 0
        self.fail_count = 0
        self.remain_count = 5000  # Mass production target
        self.is_logged_in = False
        
        # Initialize result handler
        self.result_handler = ScanResultHandler(
            self.log_manager, global_pass_macs, 
            global_pass_serials, self.session_scanned
        )
        
        # Setup UI
        self.root.title("Beacon Scanner - PRODUCTION (MySQL)")
        self.root.configure(bg=Config.COLOR_BG)
        self.root.geometry("980x700")
        self._build_ui()
        self._populate_com_ports()
        self._update_datetime()
    
    def _build_ui(self) -> None:
        """Build the complete user interface"""
        # Top info section
        top_frame = tk.Frame(self.root, bg=Config.COLOR_BG)
        top_frame.pack(fill="x", padx=15, pady=10)
        
        # Left side - Operator info (EDITABLE)
        left_frame = tk.Frame(top_frame, bg=Config.COLOR_BG)
        left_frame.pack(side="left")
        
        tk.Label(left_frame, text="Operator:", bg=Config.COLOR_BG, fg=Config.COLOR_FG,
                font=("Arial", 10)).grid(row=0, column=0, sticky="e", pady=3, padx=5)
        self.operator_entry = tk.Entry(left_frame, width=25, bg="white",
                                      fg="black", font=("Arial", 10))
        self.operator_entry.grid(row=0, column=1, sticky="w", pady=3)
        self.operator_entry.bind("<Return>", lambda e: self.po_entry.focus_set())
        
        tk.Label(left_frame, text="PO Number:", bg=Config.COLOR_BG, fg=Config.COLOR_FG,
                font=("Arial", 10)).grid(row=1, column=0, sticky="e", pady=3, padx=5)
        self.po_entry = tk.Entry(left_frame, width=25, bg="white",
                                fg="black", font=("Arial", 10))
        self.po_entry.grid(row=1, column=1, sticky="w", pady=3)
        self.po_entry.bind("<Return>", lambda e: self.serial_entry.focus_set())
        
        tk.Label(left_frame, text="Serial Number (QR):", bg=Config.COLOR_BG, fg=Config.COLOR_FG,
                font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="e", pady=3, padx=5)
        self.serial_entry = tk.Entry(left_frame, width=25, bg="white",
                                    fg="black", font=("Consolas", 11))
        self.serial_entry.grid(row=2, column=1, sticky="w", pady=3)
        self.serial_entry.bind("<Return>", self._on_serial_enter)
        
        tk.Label(left_frame, text="MAC Address (QR):", bg=Config.COLOR_BG, fg=Config.COLOR_FG,
                font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="e", pady=3, padx=5)
        self.mac_entry = tk.Entry(left_frame, width=25, bg="white",
                                 fg="black", font=("Consolas", 11))
        self.mac_entry.grid(row=3, column=1, sticky="w", pady=3)
        self.mac_entry.bind("<Return>", self._on_mac_enter)
        
        # Middle - Shift and COM
        mid_frame = tk.Frame(top_frame, bg=Config.COLOR_BG)
        mid_frame.pack(side="left", padx=30)
        
        tk.Label(mid_frame, text="Shift:", bg=Config.COLOR_BG, fg=Config.COLOR_FG,
                font=("Arial", 10)).grid(row=0, column=0, sticky="e", padx=5)
        self.shift_combo = ttk.Combobox(mid_frame, values=["A", "B", "C"], width=8)
        self.shift_combo.set("A")
        self.shift_combo.grid(row=0, column=1, pady=5)
        
        tk.Label(mid_frame, text="COM Port:", bg=Config.COLOR_BG, fg=Config.COLOR_FG,
                font=("Arial", 10)).grid(row=1, column=0, sticky="e", padx=5)
        self.com_var = tk.StringVar(value=Config.DEFAULT_COM)
        self.com_combo = ttk.Combobox(mid_frame, textvariable=self.com_var, width=8)
        self.com_combo.grid(row=1, column=1, pady=5)
        
        tk.Label(mid_frame, text="Timeout (s):", bg=Config.COLOR_BG, fg=Config.COLOR_FG,
                font=("Arial", 10)).grid(row=2, column=0, sticky="e", padx=5)
        self.timeout_var = tk.IntVar(value=Config.DEFAULT_SCAN_TIMEOUT)
        # UI spinbox still allows up to 60 but code enforces max 15
        tk.Spinbox(mid_frame, from_=3, to=60, width=6, textvariable=self.timeout_var,
                  bg="white", fg="black").grid(row=2, column=1, pady=5)
        
        # Right side - DateTime
        right_frame = tk.Frame(top_frame, bg=Config.COLOR_BG)
        right_frame.pack(side="right")
        
        self.datetime_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        tk.Label(right_frame, textvariable=self.datetime_var, bg=Config.COLOR_BG, 
                fg=Config.COLOR_FG, font=("Arial", 11, "bold")).pack()
        
        # Result display (large PASS/FAIL)
        result_frame = tk.Frame(self.root, bg=Config.COLOR_BG, height=150)
        result_frame.pack(fill="x", padx=15, pady=10)
        result_frame.pack_propagate(False)
        
        self.result_label = tk.Label(result_frame, text="READY", 
                                     font=("Arial", 72, "bold"),
                                     bg=Config.COLOR_BG, fg=Config.COLOR_FG)
        self.result_label.pack(expand=True)
        
        self.status_label = tk.Label(result_frame, text="", 
                                     font=("Arial", 12),
                                     bg=Config.COLOR_BG, fg=Config.COLOR_WARN)
        self.status_label.pack()
        
        # Progress bar
        progress_frame = tk.Frame(self.root, bg=Config.COLOR_BG)
        progress_frame.pack(fill="x", padx=15, pady=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=950)
        self.progress_bar.pack()
        
        # MAC & Serial entry display
        mac_frame = tk.Frame(self.root, bg=Config.COLOR_BG)
        mac_frame.pack(fill="x", padx=15, pady=10)
        
        tk.Label(mac_frame, text="RETRY MAC:", font=("Arial", 14, "bold"),
                bg=Config.COLOR_BG, fg=Config.COLOR_FG).pack(side="left", padx=10)
        
        self.mac_display = tk.Label(mac_frame, text="--:--:--:--:--:--", 
                                   font=("Arial", 14, "bold"),
                                   bg=Config.COLOR_BG, fg=Config.COLOR_FG)
        self.mac_display.pack(side="left", padx=10)
        
        # NEW: Show scanned Serial too (keeps last serial visible)
        tk.Label(mac_frame, text="   SCANNED SERIAL:", font=("Arial", 14, "bold"),
                bg=Config.COLOR_BG, fg=Config.COLOR_FG).pack(side="left", padx=10)
        self.serial_display = tk.Label(mac_frame, text="--", 
                                   font=("Arial", 14, "bold"),
                                   bg=Config.COLOR_BG, fg=Config.COLOR_FG)
        self.serial_display.pack(side="left", padx=10)
        
        # Log console
        log_frame = tk.Frame(self.root, bg=Config.COLOR_BG)
        log_frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, 
                                                  bg="#0a0a0a", fg=Config.COLOR_FG,
                                                  font=("Consolas", 9), wrap="none")
        self.log_text.pack(fill="both", expand=True)
        
        # Configure text tags for colored output
        self.log_text.tag_config("pass", foreground=Config.COLOR_PASS)
        self.log_text.tag_config("fail", foreground=Config.COLOR_FAIL)
        self.log_text.tag_config("warn", foreground=Config.COLOR_WARN)
        self.log_text.tag_config("info", foreground="#00aaff")
        
        # Bottom buttons
        button_frame = tk.Frame(self.root, bg=Config.COLOR_BG)
        button_frame.pack(fill="x", padx=15, pady=10)
        
        self.stop_btn = tk.Button(button_frame, text="⬤ EMERGENCY STOP", 
                                  font=("Arial", 11, "bold"),
                                  bg="#cc0000", fg="white", 
                                  command=self._emergency_stop,
                                  padx=20, pady=8)
        self.stop_btn.pack(side="left", padx=10)
        
        self.scan_btn = tk.Button(button_frame, text="Scan MAC", 
                                  font=("Arial", 11, "bold"),
                                  bg="#004400", fg="white",
                                  command=self._on_scan_click,
                                  padx=20, pady=8)
        self.scan_btn.pack(side="left", padx=10)
        
        tk.Button(button_frame, text="Clear Session", 
                 font=("Arial", 10),
                 bg="#333333", fg="white",
                 command=self._clear_session,
                 padx=15, pady=8).pack(side="left", padx=10)
        
        # Hidden entry for QR scanner input
        self.hidden_entry = tk.Entry(self.root)
        self.hidden_entry.place(x=-1000, y=-1000)
        # Do not bind hidden entry - use visible entries instead
        
        # Set initial focus to operator entry
        self.operator_entry.focus_set()
        
        # Start adapter connection
        threading.Thread(target=self._adapter_connect_loop, daemon=True).start()
    
    def _on_serial_enter(self, event) -> None:
        """Handle serial entry - validate and move to MAC entry; check programming stage"""
        sn = self.serial_entry.get().strip()
        if not sn:
            messagebox.showwarning("Invalid Serial", "Please enter a Serial Number")
            return
        
        base_serial = sn  # assume scanned QR gives base serial (without suffix)
        
        # Pre-scan check: programming must be 1 in mainboard_main
        if MYSQL_OK:
            passed, err = DBHelper.check_programming_passed(base_serial)
            if not passed:
                # Show error message and prevent continuation
                error_msg = err if err else "Programming stage not passed"
                self._log_message(f"[BLOCKED] {error_msg}", "fail")
                messagebox.showerror("Cannot Continue", error_msg)
                # Clear serial entry and return focus
                self.serial_entry.delete(0, tk.END)
                self.serial_entry.focus_set()
                return
        
        # Get operator info
        operator, shift, po = self._get_operator_info()
        
        # Check if serial already passed (global)
        if self.result_handler.check_serial_duplicate(sn):
            ui_info = self.result_handler.record_result(
                operator, shift, po, sn, "",
                "FAIL (Duplicate Serial - Already Passed)",
                "Serial previously passed", None, "", False
            )
            # Update UI and show last serial/mac
            self.serial_display.config(text=sn)
            self._update_ui_result(ui_info, False)
            return
        
        # Store current serial and focus MAC entry
        self.current_sn = sn
        self.serial_display.config(text=sn)  # show scanned serial in GUI
        self.mac_entry.focus_set()
        self._log_message(f"Serial entered: {sn} - Ready for MAC scan", "info")
    
    def _on_mac_enter(self, event) -> None:
        """Handle MAC entry - trigger scan"""
        mac_in = self.mac_entry.get().strip()
        norm = Utils.normalize_mac(mac_in)
        
        if not norm or len(norm) != 12:
            messagebox.showwarning("Invalid MAC", "MAC must be 12 hex characters")
            self.mac_entry.delete(0, tk.END)
            return
        
        self._process_mac_scan(norm)
        
        # Start adapter connection
        threading.Thread(target=self._adapter_connect_loop, daemon=True).start()
    
    def _update_datetime(self) -> None:
        """Update date/time display"""
        now = datetime.now()
        self.datetime_var.set(now.strftime("%Y-%m-%d %H:%M:%S"))
        self.root.after(1000, self._update_datetime)
    
    def _populate_com_ports(self) -> None:
        """Populate COM port dropdown"""
        try:
            import serial.tools.list_ports
            ports = [p.device for p in serial.tools.list_ports.comports()]
            self.com_combo['values'] = ports
            
            if Config.DEFAULT_COM in ports:
                self.com_var.set(Config.DEFAULT_COM)
            elif ports:
                self.com_var.set(ports[0])
        except Exception:
            pass
    
    def _adapter_connect_loop(self) -> None:
        """Attempt to connect adapter with retries"""
        if not PYGATT_OK:
            self._log_message(f"ERROR: pygatt not available. Install: pip install pygatt pyserial", "fail")
            return
        
        attempt = 0
        while True:
            attempt += 1
            self._log_message(f"Connecting adapter (attempt {attempt})...", "info")
            try:
                self.scanner.com_port = self.com_var.get().strip() or Config.DEFAULT_COM
                self.scanner.start_adapter()
                self._log_message("Adapter connected successfully", "pass")
                return
            except Exception as e:
                self._log_message(f"Adapter connect failed: {str(e)}", "fail")
                time.sleep(2)
    
    def _get_operator_info(self) -> Tuple[str, str, str]:
        """Get current operator info from entries"""
        operator = self.operator_entry.get().strip() or "UNKNOWN"
        shift = self.shift_combo.get().strip() or "A"
        po = self.po_entry.get().strip() or "UNKNOWN"
        return operator, shift, po
    
    def _on_scan_click(self) -> None:
        """Manual scan button clicked"""
        mac_input = messagebox.askstring("Scan MAC", "Enter MAC address:")
        if mac_input:
            norm = Utils.normalize_mac(mac_input)
            if len(norm) == 12:
                self._process_mac_scan(norm)
            else:
                messagebox.showwarning("Invalid MAC", "MAC must be 12 hex characters")
    
    def _process_mac_scan(self, norm_mac: str) -> None:
        """Process a scanned MAC address"""
        # Get current operator info
        operator, shift, po = self._get_operator_info()
        
        # Get current serial (base)
        current_sn = self.current_sn or self.serial_entry.get().strip()
        
        if not current_sn:
            self._log_message("ERROR: No serial number entered", "fail")
            messagebox.showwarning("Missing Serial", "Please enter serial number first")
            return
        
        base_serial = current_sn
        
        # Check serial duplicate
        if self.result_handler.check_serial_duplicate(current_sn):
            ui_info = self.result_handler.record_result(
                operator, shift, po, current_sn, "",
                "FAIL (Duplicate Serial - Already Passed)",
                "Serial previously passed", None, "", False
            )
            # show last serial in GUI
            self.serial_display.config(text=current_sn)
            self._update_ui_result(ui_info, False)
            return
        
        # Check MAC duplicate
        is_dup, reason = self.result_handler.check_mac_duplicate(norm_mac)
        if is_dup:
            result = ("FAIL (Duplicate MAC - Previously Passed)" if "previously" in reason
                     else "FAIL (Duplicate - Session)")
            ui_info = self.result_handler.record_result(
                operator, shift, po, current_sn, norm_mac,
                result, reason, None, "", False
            )
            # update displays
            self.mac_display.config(text=Utils.pretty_mac(norm_mac))
            self.serial_display.config(text=current_sn)
            self._update_ui_result(ui_info, False)
            return
        
        # Start scan
        mac_pretty = Utils.pretty_mac(norm_mac)
        self.mac_display.config(text=mac_pretty)
        self.serial_display.config(text=current_sn)
        self.status_label.config(text="Scanning...")
        self.session_scanned.add(norm_mac)
        
        threading.Thread(
            target=self._scan_thread,
            args=(operator, shift, po, current_sn, norm_mac),
            daemon=True
        ).start()
    
    def _scan_thread(self, operator: str, shift: str, po: str, sn: str, norm_mac: str) -> None:
        """Background thread to perform scan"""
        # enforce max timeout
        requested = self.timeout_var.get()
        timeout = min(requested if isinstance(requested, int) else int(requested), Config.MAX_SCAN_TIMEOUT)
        
        try:
            if not (self.scanner.adapter and self.scanner.started):
                self.scanner.start_adapter()
        except Exception as e:
            # Get next test_rep for CSV logging
            test_rep = self.result_handler.get_next_test_rep(sn)
            date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Log to CSV
            self.log_manager.write_log_entry(
                sn, po, operator, shift, date_time,
                norm_mac, None, test_rep, f"ADAPTER_ERROR: {str(e)}", 0
            )
            
            ui_info = self.result_handler.record_result(
                operator, shift, po, sn, norm_mac,
                "FAIL (Adapter)", str(e), None, "", False
            )
            self._update_ui_result(ui_info, False)
            return
        
        try:
            devices = self.scanner.scan_once(timeout=timeout, target_mac=norm_mac)
        except Exception as e:
            # Get next test_rep for CSV logging
            test_rep = self.result_handler.get_next_test_rep(sn)
            date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Log to CSV
            self.log_manager.write_log_entry(
                sn, po, operator, shift, date_time,
                norm_mac, None, test_rep, f"SCAN_ERROR: {str(e)}", 0
            )
            
            ui_info = self.result_handler.record_result(
                operator, shift, po, sn, norm_mac,
                "FAIL (ScanErr)", str(e), None, "", False
            )
            self._update_ui_result(ui_info, False)
            return
        
        matched = next((d for d in devices if d.get('address') == norm_mac), None)
        
        if not matched:
            result_text = "FAIL"
            remarks = "not_scannable"
            status_int = 0
            rssi = None
        else:
            result_text = "PASS"
            remarks = "scannable"
            status_int = 1
            rssi = matched.get('rssi')
        
        rawhex = Utils.bytes_to_hex(matched.get('mfg_bytes')) if matched and matched.get('mfg_bytes') else ""
        
        # Get next test_rep BEFORE any DB operations
        test_rep = self.result_handler.get_next_test_rep(sn)
        
        # Determine current db/test repetition and insert
        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db_insert_success = False
        
        try:
            if MYSQL_OK:
                # compute new test repetition and rename older records accordingly inside transaction
                success, err = DBHelper.insert_blescan_and_update_main(
                    base_serial=sn,
                    store_serial=sn,  # store_serial is base (inserted as base)
                    po_num=po,
                    operator_en=operator,
                    shift=shift,
                    date_time=date_time,
                    mac_address=norm_mac,
                    rssi=rssi,
                    test_rep=0,  # actual test_rep determined in DB helper; passed only for logging fallback
                    remarks=remarks,
                    status=status_int
                )
                if not success:
                    # DB insert failed - force FAIL result
                    self._log_message(f"[DB Insert Error] {err}", "fail")
                    result_text = "FAIL"
                    remarks = f"DB_INSERT_ERROR: {err}"
                    status_int = 0
                    db_insert_success = False
                else:
                    db_insert_success = True
            else:
                self._log_message("MySQL not available; skipping DB insert", "warn")
                # If MySQL not available, treat as fail to prevent false passes
                result_text = "FAIL"
                remarks = "MySQL_NOT_AVAILABLE"
                status_int = 0
        except Exception as e:
            # Any exception during DB operation - force FAIL
            self._log_message(f"[DB Error] {e}", "fail")
            result_text = "FAIL"
            remarks = f"DB_ERROR: {str(e)}"
            status_int = 0
            db_insert_success = False
        
        # Write to CSV once with correct test_rep
        try:
            self.log_manager.write_log_entry(
                sn, po, operator, shift, date_time,
                norm_mac, rssi, test_rep, remarks, status_int
            )
        except Exception as csv_err:
            self._log_message(f"[CSV Error] {csv_err}", "fail")
        
        # Record to UI via result handler (no CSV logging in record_result)
        ui_info = self.result_handler.record_result(
            operator, shift, po, sn, norm_mac,
            result_text, remarks, rssi, rawhex, update_globals=(result_text == "PASS")
        )
        
        # Update UI - pass is_pass based on final result_text
        self._update_ui_result({**ui_info, 'date_time': date_time, 'status': status_int, 'test_rep': test_rep}, result_text == "PASS")
    
    def _update_ui_result(self, ui_info: Dict, is_pass: bool) -> None:
        """Update UI with scan results"""
        def update():
            # Ensure serial & mac displays reflect the last scanned values
            if ui_info.get('mac'):
                self.mac_display.config(text=ui_info['mac'])
            if ui_info.get('serial'):
                self.serial_display.config(text=ui_info['serial'])
            
            if is_pass:
                self._show_result("PASS", ui_info.get('remarks', ''))
                self.pass_count += 1
                SoundPlayer.beep_pass()
                self._log_message(
                    f"[{datetime.now().strftime('%H:%M:%S')}] PASS: MAC={ui_info.get('mac')} "
                    f"Serial={ui_info.get('serial')} RSSI={ui_info.get('rssi')}", 
                    "pass"
                )
            else:
                self._show_result("FAIL", ui_info.get('remarks', ''))
                self.fail_count += 1
                SoundPlayer.beep_fail()
                self._log_message(
                    f"[{datetime.now().strftime('%H:%M:%S')}] FAIL: {ui_info.get('remarks','')} "
                    f"MAC={ui_info.get('mac')} Serial={ui_info.get('serial')}", 
                    "fail"
                )
            
            # Update counters
            self._update_counters()
            
            # Clear inputs
            self.current_sn = ""
            self.serial_entry.delete(0, tk.END)
            self.mac_entry.delete(0, tk.END)
            # NOTE: keep status_label and result_label visible (do not clear to READY)
            self.serial_entry.focus_set()  # Focus back to serial entry for next scan
        
        self.root.after(50, update)
    
    def _show_result(self, result: str, message: str) -> None:
        """Display result in large label and keep it visible until next update"""
        if result == "PASS":
            self.result_label.config(text="PASS", fg=Config.COLOR_PASS)
        else:
            self.result_label.config(text="FAIL", fg=Config.COLOR_FAIL)
        
        # Show message in status_label and keep it visible (no auto-clear)
        self.status_label.config(text=message)
    
    def _update_counters(self) -> None:
        """Update pass/fail/remain counters and progress bar"""
        total = self.pass_count + self.fail_count
        
        # Update progress bar
        if self.remain_count > 0:
            progress = (total / self.remain_count) * 100
            self.progress_bar['value'] = min(progress, 100)
    
    def _log_message(self, message: str, tag: str = "info") -> None:
        """Add message to log console"""
        def log():
            self.log_text.insert(tk.END, message + "\n", tag)
            self.log_text.see(tk.END)
            # Keep log at reasonable size
            if int(self.log_text.index('end-1c').split('.')[0]) > 1000:
                self.log_text.delete('1.0', '100.0')
        
        self.root.after(0, log)
    
    def _emergency_stop(self) -> None:
        """Emergency stop button clicked"""
        if messagebox.askyesno("Emergency Stop", "Stop all operations?"):
            self._log_message("EMERGENCY STOP ACTIVATED", "fail")
            try:
                self.scanner.stop_adapter()
            except Exception:
                pass
            self.result_label.config(text="STOPPED", fg=Config.COLOR_FAIL)
    
    def _clear_session(self) -> None:
        """Clear current session data"""
        if messagebox.askyesno("Clear session", "Clear current session records?"):
            self.session_scanned.clear()
            self.pass_count = 0
            self.fail_count = 0
            # Clear test_rep tracking
            self.result_handler.session_test_reps.clear()
            self._update_counters()
            self.log_text.delete('1.0', tk.END)
            self.result_label.config(text="SESSION CLEARED", fg=Config.COLOR_FG)
            # reset visible serial/mac displays as session cleared
            self.mac_display.config(text="--:--:--:--:--:--")
            self.serial_display.config(text="--")
            self._log_message("Session cleared", "info")
    
    def _open_logs(self) -> None:
        """Open logs directory"""
        path = os.path.abspath(Config.LOGS_DIR)
        if os.name == "nt":
            os.startfile(path)
        else:
            messagebox.showinfo("Logs", path)
    
    def _show_summary(self) -> None:
        """Show session summary"""
        total = self.pass_count + self.fail_count
        messagebox.showinfo(
            "Summary",
            f"PASS: {self.pass_count}\n"
            f"FAIL: {self.fail_count}\n"
            f"TOTAL: {total}"
        )
    
    def on_close(self) -> None:
        """Handle application close"""
        try:
            self.scanner.stop_adapter()
        except Exception:
            pass
        self.root.destroy()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================
def main():
    """Application entry point"""
    root = tk.Tk()
    
    # Create main application (no login dialog)
    app = BeaconScannerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    
    # Show warning if pygatt missing
    if not PYGATT_OK:
        messagebox.showwarning(
            "Dependency missing",
            f"pygatt not available.\nInstall: pip install pygatt pyserial\n\n{PYGATT_ERR}"
        )
    if not MYSQL_OK:
        messagebox.showwarning(
            "Dependency missing",
            "mysql-connector-python not available. Install: pip install mysql-connector-python"
        )
    
    root.mainloop()


if __name__ == "__main__":
    main()