import tkinter as tk
from PIL import Image, ImageTk
from tkinter import ttk, messagebox, scrolledtext
from printer_handler import PrinterHandler
from database_handler import DatabaseHandler, insertDatabaseHandler
from zpl_codes import inner_zpl, outer_zpl
from widget_design import apply_widget_styles, add_tooltip

class ZPLPrinterGUI:
    def __init__(self, root, username, serial_num, po_num, shift, ship_mode, logout_callback):
        self.root = root
        self.username = username
        self.serial_num = serial_num
        self.po_num = po_num
        self.shift = shift
        self.ship_mode = ship_mode
        self.logout_callback = logout_callback
        
        # Box counting variables
        self.box_count_var = tk.StringVar()
        self.pallet_count = 1
        self.unit_count = 0
        self.total_units_per_pallet = 0
        self.units_per_innerbox = 2
        self.innerboxes_per_outerbox = 5
        
        # ✅ NEW: Batch code lock for pallet
        self.current_pallet_batch_code = None
        
        self.box_dropdown = None
        self.box_count_frame = None
        self.capacity_label = None
        
        self.insert_db = insertDatabaseHandler()
        self.root.title("Packaging")
        self.root.geometry("650x700")
        
        self.center_window(650, 730)

        self.printer = PrinterHandler()
        self.db = DatabaseHandler()

        apply_widget_styles()

        self.create_widgets()      # ← CREATE WIDGETS FIRST (line 45)
        self.refresh_ports()       # ← THEN REFRESH PORTS (line 46) ❌ THIS IS THE PROBLEM
        self.create_box_dropdown()
        
        self.box_count_var.trace("w", lambda *args: self.update_pallet_capacity())

    def center_window(self, width, height):
        """Center the window on the screen"""
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

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

        # --- RIGHT SIDE: Logo + User Info + Logout + Pallet Progress ---
        right_conn = ttk.Frame(conn_frame)
        right_conn.pack(side="right", anchor="ne", padx=(0, 10), pady=(10, 0))

        # 🖼 Load image + user info container
        try:
            logo_image = Image.open("kaertech_logo512.png")
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

        '''# 🧾 LOG SECTION (CRITICAL - MUST BE OUTSIDE try/except!)
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
        self.log_text.pack(fill="both", expand=True)'''

# Add these new methods to handle dual printer connections:
    def start_new_batch(self):
        """Start a new batch code - return to shipping mode selection"""
        if self.current_pallet_batch_code is None:
            messagebox.showinfo(
                "No Active Batch",
                "There is no active batch code.\nScan an item to start a new batch."
            )
            return
        
        if self.unit_count == 0:
            messagebox.showinfo(
                "No Units",
                "Current batch has no units.\nJust scan a new item to change batch code."
            )
            return
        
        # Confirm the action
        result = messagebox.askyesno(
            "Start New Batch",
            f"⚠️ Current Batch Information:\n\n"
            f"Batch Code: {self.current_pallet_batch_code}\n"
            f"Current Pallet: {self.pallet_count}\n"
            f"Units Scanned: {self.unit_count} / {self.total_units_per_pallet}\n\n"
            f"Starting a new batch will:\n"
            f"• Mark current pallet as complete (incomplete)\n"
            f"• Allow you to select a new shipping mode\n"
            f"• Reset to a new pallet\n\n"
            f"Continue?"
        )
        
        if not result:
            return
        
        # Log the incomplete pallet
        old_batch = self.current_pallet_batch_code
        old_pallet = self.pallet_count
        old_units = self.unit_count
        
        self.log(
            f"🔄 BATCH CHANGE: Pallet {old_pallet} finished with {old_units} units "
            f"(Batch: {old_batch}) - Incomplete"
        )
        
        # Reset for new batch
        self.pallet_count += 1
        self.unit_count = 0
        self.current_pallet_batch_code = None
        self.batch_label.config(
            text="Batch Code: Not Set",
            foreground="orange"
        )
        self.update_progress_display()
        
        # Show shipping mode selection dialog
        self.show_ship_mode_dialog()

    def show_ship_mode_dialog(self):
        """Show dialog to select new shipping mode"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Shipping Mode")
        dialog.geometry("350x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 350) // 2
        y = (dialog.winfo_screenheight() - 200) // 2
        dialog.geometry(f"350x200+{x}+{y}")
        
        # Content
        ttk.Label(
            dialog,
            text="Starting New Batch",
            font=("Arial", 14, "bold")
        ).pack(pady=15)
        
        ttk.Label(
            dialog,
            text=f"Operator: {self.username} | Shift: {self.shift}",
            font=("Arial", 10)
        ).pack(pady=5)
        
        ttk.Label(
            dialog,
            text="Select Shipping Mode:",
            font=("Arial", 11)
        ).pack(pady=10)
        
        ship_mode_var = tk.StringVar()
        ship_dropdown = ttk.Combobox(
            dialog,
            textvariable=ship_mode_var,
            values=["SEA", "AIR"],
            state="readonly",
            font=("Arial", 11),
            width=15
        )
        ship_dropdown.pack(pady=5)
        ship_dropdown.set(self.ship_mode)  # Default to current mode
        
        def confirm_mode():
            new_mode = ship_mode_var.get()
            if not new_mode:
                messagebox.showwarning("No Selection", "Please select a shipping mode.")
                return
            
            # Update shipping mode
            old_mode = self.ship_mode
            self.ship_mode = new_mode
            
            # Recreate box dropdown for new mode
            self.create_box_dropdown()
            
            self.log(f"🚢 Shipping mode changed: {old_mode} → {new_mode}")
            messagebox.showinfo(
                "Mode Updated",
                f"Shipping mode set to: {new_mode}\n"
                f"New Pallet: {self.pallet_count}\n"
                f"Ready to scan new batch code."
            )
            
            dialog.destroy()
            self.serial_entry.focus()
        
        ttk.Button(
            dialog,
            text="Confirm",
            command=confirm_mode,
            style="Connect.TButton"
        ).pack(pady=15)
        
        # Bind Enter key
        dialog.bind('<Return>', lambda e: confirm_mode())
        ship_dropdown.focus()

    def create_box_dropdown(self):
        """Create dropdown based on shipping mode"""
        if self.box_count_frame:
            self.box_count_frame.destroy()

        self.box_count_frame = ttk.LabelFrame(self.root, text="Box Configuration", padding=10)
        self.box_count_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(self.box_count_frame, text="Shipping Mode:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        mode_label = ttk.Label(self.box_count_frame, text=self.ship_mode.upper(), font=("Arial", 10, "bold"))
        mode_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(self.box_count_frame, text="Boxes per Pallet:").grid(row=1, column=0, padx=5, pady=5, sticky="w")

        if self.ship_mode.upper() == "SEA":
            options = ["20 box", "21 box", "27 box"]
        elif self.ship_mode.upper() == "AIR":
            options = ["15 box", "10 box"]
        else:
            options = []

        self.box_dropdown = ttk.Combobox(self.box_count_frame, textvariable=self.box_count_var, 
                                         values=options, state="readonly", width=15)
        if options:
            self.box_dropdown.current(0)
        self.box_dropdown.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        self.capacity_label = ttk.Label(self.box_count_frame, text="Total Capacity: 0 units", 
                                       font=("Arial", 9), foreground="blue")
        self.capacity_label.grid(row=2, column=0, columnspan=2, pady=5)

        self.update_pallet_capacity()

    def update_pallet_capacity(self):
        """Calculate and display total units per pallet"""
        if not self.box_count_var.get():
            self.total_units_per_pallet = 0
            if self.capacity_label:
                self.capacity_label.config(text="Total Capacity: 0 units")
            return
        
        selected_outer_boxes = int(self.box_count_var.get().split()[0])
        self.total_units_per_pallet = selected_outer_boxes * self.innerboxes_per_outerbox * self.units_per_innerbox
        
        if self.capacity_label:
            self.capacity_label.config(
                text=f"Total Capacity: {self.total_units_per_pallet} units "
                     f"({selected_outer_boxes} boxes × {self.innerboxes_per_outerbox} innerboxes × {self.units_per_innerbox} units)"
            )
        
        self.update_progress_display()
 
    def refresh_ports(self):
        """Refresh available COM ports for both printers"""
        ports = self.printer.list_ports()
        self.inner_port_combo['values'] = ports
        self.outer_port_combo['values'] = ports
        
        if ports:
            if len(ports) > 0:
                self.inner_port_combo.current(0)
                self.inner_port_combo.config(foreground="blue")
            if len(ports) > 1:
                self.outer_port_combo.current(1)
                self.outer_port_combo.config(foreground="blue")
            elif len(ports) == 1:
                self.outer_port_combo.current(0)
                self.outer_port_combo.config(foreground="blue")
            
            '''self.log(f"Found {len(ports)} port(s): {', '.join(ports)}")
        else:
            self.log("No COM ports found")'''

    def toggle_inner_connection(self):
        """Toggle connection for inner box printer"""
        if self.printer.is_inner_connected():
            self.printer.disconnect_inner()
            self.inner_status_label.config(text="Status: Disconnected", foreground="red")
            self.inner_connect_btn.config(text="Connect", style="Connect.TButton")
            self.log("Disconnected from inner box printer")
        else:
            port = self.inner_port_combo.get()
            if not port:
                messagebox.showwarning("No Port Selected", "Please select a COM port for inner printer.")
                return
            
            baud = int(self.inner_baud_combo.get())
            if self.printer.connect_inner(port, baud):
                self.inner_status_label.config(text=f"Status: Connected to {port}", foreground="green")
                self.inner_connect_btn.config(text="Disconnect", style="Disconnect.TButton")
                self.log(f"Inner box printer connected to {port}")
            else:
                messagebox.showerror("Connection Error", f"Failed to connect to inner printer on {port}")

    def toggle_outer_connection(self):
        """Toggle connection for outer box printer"""
        if self.printer.is_outer_connected():
            self.printer.disconnect_outer()
            self.outer_status_label.config(text="Status: Disconnected", foreground="red")
            self.outer_connect_btn.config(text="Connect", style="Connect.TButton")
            self.log("Disconnected from outer box printer")
        else:
            port = self.outer_port_combo.get()
            if not port:
                messagebox.showwarning("No Port Selected", "Please select a COM port for outer printer.")
                return
            
            baud = int(self.outer_baud_combo.get())
            if self.printer.connect_outer(port, baud):
                self.outer_status_label.config(text=f"Status: Connected to {port}", foreground="green")
                self.outer_connect_btn.config(text="Disconnect", style="Disconnect.TButton")
                self.log(f"Outer box printer connected to {port}")
            else:
                messagebox.showerror("Connection Error", f"Failed to connect to outer printer on {port}")
                
    def toggle_connection(self):
        """Toggle connection for BOTH printers at once"""
        # Check if either printer is connected
        if self.printer.is_inner_connected() or self.printer.is_outer_connected():
            # Disconnect both
            self.printer.disconnect_all()
            self.inner_status_label.config(text="Status: Disconnected", foreground="red")
            self.outer_status_label.config(text="Status: Disconnected", foreground="red")
            self.connect_btn.config(text="Connect Both", style="Connect.TButton")
            self.log("🔌 Disconnected from both printers")
        else:
            # Connect both
            inner_port = self.inner_port_combo.get()
            outer_port = self.outer_port_combo.get()
            
            if not inner_port or not outer_port:
                messagebox.showwarning("No Port Selected", 
                    "Please select COM ports for both printers.\n\n"
                    "Inner Printer: Select port for innerbox labels\n"
                    "Outer Printer: Select port for outerbox labels")
                return
            
            if inner_port == outer_port:
                messagebox.showerror("Same Port Selected", 
                    "Inner and Outer printers cannot use the same COM port!\n"
                    "Please select different ports for each printer.")
                return
            
            inner_baud = int(self.inner_baud_combo.get())
            outer_baud = int(self.outer_baud_combo.get())
            
            # Try to connect both
            inner_success = self.printer.connect_inner(inner_port, inner_baud)
            outer_success = self.printer.connect_outer(outer_port, outer_baud)
            
            # Update status labels
            if inner_success:
                self.inner_status_label.config(text=f"Status: Connected to {inner_port}", foreground="green")
                self.log(f"📦 Inner box printer connected to {inner_port}")
            else:
                self.inner_status_label.config(text="Status: Connection Failed", foreground="red")
                self.log(f"❌ Failed to connect inner printer to {inner_port}")
            
            if outer_success:
                self.outer_status_label.config(text=f"Status: Connected to {outer_port}", foreground="green")
                self.log(f"📦 Outer box printer connected to {outer_port}")
            else:
                self.outer_status_label.config(text="Status: Connection Failed", foreground="red")
                self.log(f"❌ Failed to connect outer printer to {outer_port}")
            
            # Update button based on results
            if inner_success and outer_success:
                self.connect_btn.config(text="Disconnect Both", style="Disconnect.TButton")
                messagebox.showinfo("Success", 
                    f"✅ Both printers connected successfully!\n\n"
                    f"Inner Printer: {inner_port}\n"
                    f"Outer Printer: {outer_port}")
            elif inner_success or outer_success:
                self.connect_btn.config(text="Disconnect Both", style="Disconnect.TButton")
                messagebox.showwarning("Partial Connection", 
                    f"⚠️ Only one printer connected successfully.\n\n"
                    f"Inner Printer: {'✅ Connected' if inner_success else '❌ Failed'}\n"
                    f"Outer Printer: {'✅ Connected' if outer_success else '❌ Failed'}\n\n"
                    f"Check your COM port settings and try again.")
            else:
                messagebox.showerror("Connection Failed", 
                    "❌ Failed to connect both printers.\n"
                    "Please check your COM port settings and try again.")

    def clear_batch_code(self):
        """Clear the current pallet batch code lock"""
        if self.current_pallet_batch_code is None:
            messagebox.showinfo("No Batch Code", "There is no batch code currently set.")
            return
        
        if self.unit_count > 0:
            result = messagebox.askyesnocancel(
                "Clear Batch Code",
                f"⚠️ WARNING: Current pallet has {self.unit_count} units!\n\n"
                f"Current Batch Code: {self.current_pallet_batch_code}\n\n"
                f"Clearing the batch code will allow different batch codes to be added.\n"
                f"Do you want to:\n\n"
                f"• YES - Clear batch code only (keep current units)\n"
                f"• NO - Reset entire pallet (clear units and batch code)\n"
                f"• CANCEL - Keep everything as is"
            )
            
            if result is None:
                return
            elif result:
                old_batch = self.current_pallet_batch_code
                self.current_pallet_batch_code = None
                self.batch_label.config(
                    text="Batch Code: Not Set",
                    foreground="orange"
                )
                self.log(f"🔓 Batch code '{old_batch}' cleared (keeping {self.unit_count} units)")
                messagebox.showinfo("Batch Code Cleared", 
                    f"Batch code cleared.\n"
                    f"Current units ({self.unit_count}) remain on pallet.\n"
                    f"Next scan will set a new batch code.")
            else:
                old_batch = self.current_pallet_batch_code
                old_units = self.unit_count
                self.current_pallet_batch_code = None
                self.unit_count = 0
                self.batch_label.config(
                    text="Batch Code: Not Set",
                    foreground="orange"
                )
                self.update_progress_display()
                self.log(f"🔄 Pallet {self.pallet_count} reset: Batch '{old_batch}' and {old_units} units cleared")
                messagebox.showinfo("Pallet Reset", 
                    f"Pallet {self.pallet_count} has been reset.\n"
                    f"Batch code and units cleared.\n"
                    f"Ready for new items.")
        else:
            old_batch = self.current_pallet_batch_code
            self.current_pallet_batch_code = None
            self.batch_label.config(
                text="Batch Code: Not Set",
                foreground="orange"
            )
            self.log(f"🔓 Batch code '{old_batch}' cleared")
            messagebox.showinfo("Batch Code Cleared", "Batch code has been cleared.")

    def on_serial_enter(self, event):
        """Handle Enter key press in serial entry"""
        self.check_serial_in_db()
        return "break"
    
    # Update the check_serial_in_db method to use the correct printers:

    def check_serial_in_db(self):
        serial_num = self.serial_entry.get().strip()
        if not serial_num:
            messagebox.showwarning("Empty Input", "Please scan or enter a serial number.")
            return

        if self.total_units_per_pallet == 0:
            messagebox.showwarning("No Box Selection", "Please select boxes per pallet first.")
            return

        batch_code, po_num = self.db.get_batch_and_po(serial_num)

        if not batch_code or not po_num:
            msg = f"❌ Serial '{serial_num}' not found in faceware_assembly1.\n"
            self.write_to_result_box(msg)
            self.log(msg)
            self.serial_entry.delete(0, tk.END)
            self.serial_entry.focus()
            return

        # Check batch code consistency
        if self.current_pallet_batch_code is None:
            self.current_pallet_batch_code = batch_code
            self.batch_label.config(
                text=f"Pallet Batch Code: {batch_code}",
                foreground="green"
            )
            self.log(f"🔒 Pallet {self.pallet_count} locked to Batch Code: {batch_code}")
        elif self.current_pallet_batch_code != batch_code:
            messagebox.showerror(
                "Batch Code Mismatch",
                f"❌ Cannot add this item to current pallet!\n\n"
                f"Current Pallet Batch Code: {self.current_pallet_batch_code}\n"
                f"Scanned Item Batch Code: {batch_code}\n\n"
                f"All items in a pallet must have the same batch code.\n\n"
                f"Click 'New Batch Code' button to start a new batch."
            )
            msg = f"❌ REJECTED: Serial '{serial_num}' has different batch code ({batch_code})\n"
            self.write_to_result_box(msg)
            self.log(msg)
            self.serial_entry.delete(0, tk.END)
            self.serial_entry.focus()
            return

        msg = f"✅ Serial: {serial_num}\n→ Batch Code: {batch_code}\n→ PO Number: {po_num}\n"
        self.write_to_result_box(msg)
        self.log(msg)
        
        next_unit = self.unit_count + 1
        current_innerbox = ((next_unit - 1) // self.units_per_innerbox) + 1
        current_outerbox = ((current_innerbox - 1) // self.innerboxes_per_outerbox) + 1
        
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
            self.serial_entry.delete(0, tk.END)
            self.serial_entry.focus()
            return
        
        self.unit_count += 1
        self.update_progress_display()
        
        # Check printer connections
        if not self.printer.is_inner_connected() and not self.printer.is_outer_connected():
            messagebox.showwarning("Printers Not Connected", "Connect to printers before scanning.")
            self.serial_entry.delete(0, tk.END)
            self.serial_entry.focus()
            return

        # Print innerbox label when needed
        if self.unit_count % self.units_per_innerbox == 0:
            if not self.printer.is_inner_connected():
                messagebox.showwarning("Inner Printer Not Connected", 
                    "Inner box printer is not connected. Label not printed.")
            else:
                sku = "43000166102"
                barcode = f"{batch_code}-IB{current_innerbox:03d}"
                quantity = self.units_per_innerbox
                lot = batch_code
                innerbox_zpl = inner_zpl(sku, barcode, quantity, lot)
                
                if self.printer.send_to_inner_printer(innerbox_zpl):
                    self.log(f"📦 INNERBOX #{current_innerbox} label printed (Outerbox {current_outerbox})")
                else:
                    self.log(f"❌ Failed to print INNERBOX #{current_innerbox} label")
        
        # Print outerbox label when needed
        if self.unit_count % (self.units_per_innerbox * self.innerboxes_per_outerbox) == 0:
            if not self.printer.is_outer_connected():
                messagebox.showwarning("Outer Printer Not Connected", 
                    "Outer box printer is not connected. Label not printed.")
            else:
                sku = "43000166102"
                lot_code = batch_code
                quantity = self.innerboxes_per_outerbox * self.units_per_innerbox
                outerbox_zpl_data = outer_zpl(sku, lot_code, quantity, current_outerbox)
                
                if self.printer.send_to_outer_printer(outerbox_zpl_data):
                    self.log(f"📦📦 OUTERBOX #{current_outerbox} label printed")
                else:
                    self.log(f"❌ Failed to print OUTERBOX #{current_outerbox} label")

        if self.unit_count >= self.total_units_per_pallet:
            messagebox.showinfo("Pallet Complete", 
                f"🎉 Pallet {self.pallet_count} is complete!\n"
                f"Batch Code: {self.current_pallet_batch_code}\n"
                f"Total units: {self.unit_count}\n"
                f"Starting new pallet...")
            self.pallet_count += 1
            self.unit_count = 0
            self.current_pallet_batch_code = None
            self.batch_label.config(
                text="Batch Code: Not Set",
                foreground="orange"
            )
            self.update_progress_display()
        
        self.serial_entry.delete(0, tk.END)
        self.serial_entry.focus()

    def generate_innerbox_label(self, batch_code, current_innerbox, current_outerbox):
        """Generate ZPL for innerbox label"""
        sku = "43000166102"
        barcode = f"{batch_code}-IB{current_innerbox:03d}"
        quantity = self.units_per_innerbox
        lot = batch_code
        return inner_zpl(sku, barcode, quantity, lot)

    def generate_outerbox_label(self, batch_code, current_outerbox):
        """Generate ZPL for outerbox label"""
        sku = "43000166102"
        lot_code = batch_code
        quantity = self.innerboxes_per_outerbox * self.units_per_innerbox
        return outer_zpl(sku, lot_code, quantity, current_outerbox)

    def update_progress_display(self):
        """Update progress bar and labels"""
        self.pallet_label.config(text=f"Current Pallet: {self.pallet_count}")
        self.unit_label.config(text=f"Units: {self.unit_count} / {self.total_units_per_pallet}")
        
        if self.total_units_per_pallet > 0:
            progress_percent = (self.unit_count / self.total_units_per_pallet) * 100
            self.progress_bar['value'] = progress_percent
        else:
            self.progress_bar['value'] = 0

    # ✅ NEW: Helper method to write to result box (handles read-only state)
    def write_to_result_box(self, text):
        """Write text to the result box (handles read-only state)"""
        self.result_box.config(state='normal')
        self.result_box.insert("end", text)
        self.result_box.see("end")
        self.result_box.config(state='disabled')

    # ✅ NEW: Clear result box method
    def clear_result_box(self):
        """Clear the barcode scanning result box"""
        self.result_box.config(state='normal')
        self.result_box.delete("1.0", tk.END)
        self.result_box.insert("1.0", "→ Waiting for scan...\n")
        self.result_box.config(state='disabled')
        self.log("Result box cleared")

    # ✅ NEW: Clear log method
    '''def clear_log(self):
        """Clear the log text box"""
        if messagebox.askyesno("Clear Log", "Are you sure you want to clear the log?"):
            self.log_text.config(state='normal')
            self.log_text.delete("1.0", tk.END)
            self.log_text.config(state='disabled')

    def log(self, msg):
        """Write to log (handles read-only state)"""
        self.log_text.config(state='normal')
        self.log_text.insert("end", f"{msg}\n")
        self.log_text.see("end")
        self.log_text.config(state='disabled')'''

    def logout(self):
        """Handle logout - confirm and return to login screen"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            if self.printer.is_inner_connected() or self.printer.is_outer_connected():
                self.printer.disconnect_all()
            self.logout_callback()

    def on_closing(self):
        if self.printer.is_inner_connected() or self.printer.is_outer_connected():
            self.printer.disconnect_all()
        self.root.destroy()