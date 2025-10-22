import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
# =========================
# 🔹 UI Setup
# =========================
def create_widgets(self):
    # Printer Connection
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

    # Pallet Progress Display
    self.progress_frame = ttk.LabelFrame(self.root, text="Pallet Progress", padding=10)
    self.progress_frame.pack(fill="x", padx=10, pady=5)

    self.pallet_label = ttk.Label(self.progress_frame, text="Current Pallet: 1", font=("Arial", 12, "bold"))
    self.pallet_label.grid(row=0, column=0, padx=10, pady=5)

    self.unit_label = ttk.Label(self.progress_frame, text="Units: 0 / 0", font=("Arial", 12))
    self.unit_label.grid(row=0, column=1, padx=10, pady=5)

    self.progress_bar = ttk.Progressbar(self.progress_frame, length=400, mode='determinate')
    self.progress_bar.grid(row=1, column=0, columnspan=2, pady=5)

    # Barcode Scanning
    scan_frame = ttk.LabelFrame(self.root, text="Barcode Scanning", padding=10)
    scan_frame.pack(fill="x", padx=10, pady=10)

    ttk.Label(scan_frame, text="Scan Serial Number:").grid(row=0, column=0, padx=5, pady=5)
    self.serial_entry = ttk.Entry(scan_frame, width=25, font=("Arial", 12))
    self.serial_entry.grid(row=0, column=1, padx=5)
    self.serial_entry.bind("<Return>", self.on_serial_enter)
    self.serial_entry.focus()

    ttk.Button(scan_frame, text="Check Database", command=self.check_serial_in_db).grid(row=0, column=2, padx=5)

    self.result_box = scrolledtext.ScrolledText(scan_frame, height=5, width=70)
    self.result_box.grid(row=1, column=0, columnspan=3, pady=5)
    self.result_box.insert("1.0", "→ Waiting for scan...\n")

    # Log Frame
    log_frame = ttk.LabelFrame(self.root, text="Log", padding=10)
    log_frame.pack(fill="both", expand=True, padx=10, pady=5)

    self.log_text = scrolledtext.ScrolledText(log_frame, height=6, width=70)
    self.log_text.pack(fill="both", expand=True)