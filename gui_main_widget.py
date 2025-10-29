# PACKAGINS/gui_main_widget.py
from tkinter import ttk, scrolledtext
from PIL import Image, ImageTk
import tkinter as tk
from widget_design import add_tooltip

def create_widgets(self):
        """Create all UI widgets"""
        # 📦 PRINTER CONNECTION SECTION
        conn_frame = ttk.LabelFrame(self.root, text="Printer Connection", padding=10)
        conn_frame.pack(fill="x", padx=10, pady=5)

        # --- LEFT SIDE: Printer Controls (Stacked Vertically) ---
        left_conn = ttk.Frame(conn_frame)
        left_conn.pack(side="left", anchor="nw", padx=5, pady=5)

        # Inner Printer Section (TOP)
        inner_frame = ttk.LabelFrame(left_conn, text="Inner Box Printer", padding=8)
        inner_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(inner_frame, text="COM Port:").grid(row=0, column=0, sticky="w", padx=5, pady=3)
        self.inner_port_combo = ttk.Combobox(inner_frame, width=15, state="readonly")
        self.inner_port_combo.grid(row=0, column=1, padx=5, pady=3)

        ttk.Label(inner_frame, text="Baud Rate:").grid(row=1, column=0, sticky="w", padx=5, pady=3)
        self.inner_baud_combo = ttk.Combobox(
            inner_frame,
            width=15,
            state="readonly",
            values=["9600", "19200", "38400", "57600", "115200"]
        )
        self.inner_baud_combo.set("9600")
        self.inner_baud_combo.grid(row=1, column=1, padx=5, pady=3)

        self.inner_status_label = ttk.Label(inner_frame, text="Status: Disconnected", foreground="red")
        self.inner_status_label.grid(row=2, column=0, columnspan=2, pady=3)

        # Outer Printer Section (BELOW INNER)
        outer_frame = ttk.LabelFrame(left_conn, text="Outer Box Printer", padding=8)
        outer_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(outer_frame, text="COM Port:").grid(row=0, column=0, sticky="w", padx=5, pady=3)
        self.outer_port_combo = ttk.Combobox(outer_frame, width=15, state="readonly")
        self.outer_port_combo.grid(row=0, column=1, padx=5, pady=3)

        ttk.Label(outer_frame, text="Baud Rate:").grid(row=1, column=0, sticky="w", padx=5, pady=3)
        self.outer_baud_combo = ttk.Combobox(
            outer_frame,
            width=15,
            state="readonly",
            values=["9600", "19200", "38400", "57600", "115200"]
        )
        self.outer_baud_combo.set("9600")
        self.outer_baud_combo.grid(row=1, column=1, padx=5, pady=3)

        self.outer_status_label = ttk.Label(outer_frame, text="Status: Disconnected", foreground="red")
        self.outer_status_label.grid(row=2, column=0, columnspan=2, pady=3)

        # Control Buttons (Below both printer sections)
        button_frame = ttk.Frame(left_conn)
        button_frame.pack(fill="x")

        ttk.Button(
            button_frame,
            text="Refresh Ports",
            command=self.refresh_ports,
            style="Refresh.TButton",
            width=20
        ).pack(pady=3)

        self.connect_btn = ttk.Button(
            button_frame,
            text="Connect Both",
            command=self.toggle_connection,
            style="Connect.TButton",
            width=20
        )
        self.connect_btn.pack(pady=3)

        # --- NEW: Total Units Scanned Display ---
        total_units_frame = ttk.LabelFrame(left_conn, text="Production Summary", padding=8)
        total_units_frame.pack(fill="x", pady=(5, 0))

        self.total_units_label = ttk.Label(
            total_units_frame,
            text="Total Units Scanned: --",
            font=("Arial", 10, "bold"),
            foreground="#006400"
        )
        self.total_units_label.pack(pady=2)

        add_tooltip(self.total_units_label, "Total units packaged - updates automatically every 10 seconds")
        
        # --- RIGHT SIDE: Logo + User Info + Logout + Pallet Progress ---
        right_conn = ttk.Frame(conn_frame)
        right_conn.pack(side="right", anchor="ne", padx=(0, 10), pady=(10, 0))

        # 🖼 Load image + user info container
        try:
            logo_image = Image.open("packagins/kaertech_logo512.png")
            logo_image = logo_image.resize((110, 110))
            self.logo_photo = ImageTk.PhotoImage(logo_image)

            info_frame = ttk.Frame(right_conn)
            info_frame.pack(side="top", anchor="ne", fill="x")

            logo_border = tk.Frame(
                info_frame,
                bg="white",
                highlightbackground="#5A5A5A",
                highlightthickness=1,
                bd=0,
                relief="flat"
            )
            logo_border.pack(side="left", padx=(0, 10), pady=5)

            logo_label = ttk.Label(logo_border, image=self.logo_photo, background="white")
            logo_label.pack(padx=3, pady=3)

            text_frame = ttk.Frame(info_frame)
            text_frame.pack(side="left", anchor="w", padx=(5, 0))

            user_frame = ttk.Frame(text_frame)
            user_frame.pack(anchor="w", pady=(0, 5), padx=(0, 0))

            user_info = ttk.Label(
                user_frame,
                text=f"👤 {self.username}\nShift: {self.shift}\nMode: {self.ship_mode}",
                style="UserInfo.TLabel",
                anchor="w",
                justify="left",
                background="lightgray"
            )
            user_info.pack(anchor="w", padx=(0, 0))

            logout_btn = ttk.Button(
                text_frame,
                text="Logout",
                command=self.logout,
                style="Disconnect.TButton",
                width=10
            )
            logout_btn.pack(anchor="e")

            add_tooltip(logout_btn, "Click to logout and return to login screen.")

        except Exception as e:
            print(f"Image load error: {e}")

        # 🪜 PALLET PROGRESS SECTION (BELOW USER INFO)
        self.progress_frame = ttk.LabelFrame(right_conn, text="Pallet Progress", padding=10)
        self.progress_frame.pack(fill="both", expand=True, pady=(10, 0))

        self.pallet_label = ttk.Label(
            self.progress_frame,
            text="Current Pallet: 1",
            font=("Arial", 11, "bold")
        )
        self.pallet_label.pack(pady=(5, 2))

        self.unit_label = ttk.Label(
            self.progress_frame,
            text="Units: 0 / 0",
            font=("Arial", 10)
        )
        self.unit_label.pack(pady=2)

        # ✅ NEW: Database batch count display
        self.batch_count_label = ttk.Label(
            self.progress_frame,
            text="DB Batch Count: --",
            font=("Arial", 9),
            foreground="#0066CC"
        )
        self.batch_count_label.pack(pady=2)
        add_tooltip(self.batch_count_label, "Total units already packaged for current batch code in database")

        # ✅ Batch code display with clear button
        batch_frame = ttk.Frame(self.progress_frame)
        batch_frame.pack(pady=5)
        
        self.batch_label = ttk.Label(
            batch_frame,
            text="Batch Code: Not Set",
            font=("Arial", 9),
            foreground="orange"
        )
        self.batch_label.pack(pady=2)
        
        button_row1 = ttk.Frame(batch_frame)
        button_row1.pack(pady=2)
        
        clear_batch_btn = ttk.Button(
            button_row1,
            text="Clear Batch",
            command=self.clear_batch_code,
            style="Refresh.TButton",
            width=12
        )
        clear_batch_btn.pack(side="left", padx=2)
        add_tooltip(clear_batch_btn, "Clear the current pallet batch code lock")

        self.new_batch_btn = ttk.Button(
            button_row1,
            text="New Batch Code",
            command=self.start_new_batch,
            style="Connect.TButton",
            width=13
        )
        self.new_batch_btn.pack(side="left", padx=2)
        add_tooltip(self.new_batch_btn, "Finish current batch and start new one with different batch code")

        # ✅ NEW: Refresh batch count button
        refresh_batch_btn = ttk.Button(
            batch_frame,
            text="🔄 Refresh Batch Count",
            command=self.refresh_batch_count,
            style="Refresh.TButton",
            width=20
        )
        refresh_batch_btn.pack(pady=2)
        add_tooltip(refresh_batch_btn, "Manually refresh the database batch count")

        self.progress_bar = ttk.Progressbar(self.progress_frame, length=250, mode='determinate')
        self.progress_bar.pack(pady=(5, 10))

        # 📦 BARCODE SCANNING SECTION
        scan_frame = ttk.LabelFrame(self.root, text="Barcode Scanning", padding=10)
        scan_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(scan_frame, text="Scan Serial Number:").grid(row=0, column=0, padx=5, pady=5)
        self.serial_entry = ttk.Entry(scan_frame, width=25, font=("Arial", 12))
        self.serial_entry.grid(row=0, column=1, padx=5)
        self.serial_entry.bind("<Return>", self.on_serial_enter)
        self.serial_entry.focus()

        check_db_btn = ttk.Button(
            scan_frame,
            text="Check Database",
            command=self.check_serial_in_db,
            style="CheckDB.TButton"
        )
        check_db_btn.grid(row=0, column=2, padx=5)
        add_tooltip(check_db_btn, "Click to verify serial number in the database")

        clear_result_btn = ttk.Button(
            scan_frame,
            text="Clear Results",
            command=self.clear_result_box,
            style="Refresh.TButton",
            width=12
        )
        clear_result_btn.grid(row=0, column=3, padx=5)
        add_tooltip(clear_result_btn, "Clear the barcode scanning results")

        self.result_box = scrolledtext.ScrolledText(scan_frame, height=5, width=70, state='disabled')
        self.result_box.grid(row=1, column=0, columnspan=4, pady=5)
        self.write_to_result_box("→ Waiting for scan...\n")

        # 🧾 LOG SECTION (CRITICAL - MUST BE OUTSIDE try/except!)
        log_frame = ttk.LabelFrame(self.root, text="Log", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        log_header_frame = ttk.Frame(log_frame)
        log_header_frame.pack(fill="x", pady=(0, 5))

        clear_log_btn = ttk.Button(
            log_header_frame,
            text="Clear Log",
            command=self.clear_log,
            style="Refresh.TButton",
            width=10
        )
        clear_log_btn.pack(side="right")
        add_tooltip(clear_log_btn, "Clear the log display")

        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, width=70, state='disabled')
        self.log_text.pack(fill="both", expand=True)