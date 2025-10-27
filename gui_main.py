# PACKAGINS/gui_main.py
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import ttk, messagebox, scrolledtext
from printer_handler import PrinterHandler
from database_handler import DatabaseHandler, insertDatabaseHandler
from zpl_codes import inner_zpl, outer_zpl
from widget_design import apply_widget_styles, add_tooltip
from gui_main_widget import create_widgets
from select_shipping_mode_ui import show_ship_mode_dialog
from check_serial_in_database import check_serial_in_db
from types import MethodType

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
        self.root.geometry("650x950")
        self.center_window(650, 950)
        self.printer = PrinterHandler()
        self.db = DatabaseHandler()
        self.check_serial_in_db = MethodType(check_serial_in_db, self)
        apply_widget_styles()
        create_widgets(self)
        self.refresh_ports()
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
        show_ship_mode_dialog()

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
        # Store currently selected ports
        current_inner = self.inner_port_combo.get()
        current_outer = self.outer_port_combo.get()
        
        # Get fresh list of ports
        ports = self.printer.list_ports()
        
        # Update dropdown values
        self.inner_port_combo['values'] = ports
        self.outer_port_combo['values'] = ports
        
        if ports:
            # Try to maintain previous selections if they still exist
            if current_inner in ports:
                self.inner_port_combo.set(current_inner)
                self.inner_port_combo.config(foreground="blue")
            elif len(ports) > 0:
                self.inner_port_combo.current(0)
                self.inner_port_combo.config(foreground="blue")
            
            if current_outer in ports:
                self.outer_port_combo.set(current_outer)
                self.outer_port_combo.config(foreground="blue")
            elif len(ports) > 1:
                self.outer_port_combo.current(1)
                self.outer_port_combo.config(foreground="blue")
            elif len(ports) == 1:
                self.outer_port_combo.current(0)
                self.outer_port_combo.config(foreground="blue")
            
            self.log(f"🔄 Refreshed ports: Found {len(ports)} port(s): {', '.join(ports)}")
        else:
            # Clear selections if no ports found
            self.inner_port_combo.set('')
            self.outer_port_combo.set('')
            self.log("⚠️ No COM ports found. Please check connections.")
            messagebox.showwarning(
                "No Ports Found",
                "No COM ports detected.\n\n"
                "Please check:\n"
                "• Printers are powered on\n"
                "• USB cables are connected\n"
                "• Drivers are installed"
            )

    def toggle_connection(self):
        """Toggle connection for BOTH printers at once"""
        # 🔴 If connected → Disconnect all
        if self.printer.is_inner_connected() or self.printer.is_outer_connected():
            try:
                inner_was_connected = self.printer.is_inner_connected()
                outer_was_connected = self.printer.is_outer_connected()

                # Store port names before disconnecting (for logging)
                inner_port = self.inner_port_combo.get() if inner_was_connected else None
                outer_port = self.outer_port_combo.get() if outer_was_connected else None

                # Fully disconnect and release COM ports
                self.printer.disconnect_all()

                # Update GUI status
                self.inner_status_label.config(text="Status: Disconnected", foreground="red")
                self.outer_status_label.config(text="Status: Disconnected", foreground="red")
                self.connect_btn.config(text="Connect Both", style="Connect.TButton")

                # Log disconnection
                disconnected_ports = []
                if inner_was_connected and inner_port:
                    disconnected_ports.append(f"Inner Printer ({inner_port})")
                if outer_was_connected and outer_port:
                    disconnected_ports.append(f"Outer Printer ({outer_port})")

                if disconnected_ports:
                    self.log(f"🔌 Disconnected {' & '.join(disconnected_ports)} and released COM ports.")
                
                # ✅ CRITICAL: Refresh port list after disconnect
                # This ensures ports are released and available for reconnection
                import time
                time.sleep(0.2)  # Brief delay to allow OS to release ports
                self.refresh_ports()
                
                messagebox.showinfo(
                    "Disconnected", 
                    "✅ All active printer ports have been safely disconnected.\n\n"
                    "Ports have been refreshed and are ready for reconnection."
                )
            except Exception as e:
                messagebox.showerror("Disconnection Error", f"⚠️ Failed to disconnect properly:\n{e}")
                # Still try to refresh ports even if error occurred
                self.refresh_ports()
            return  # Stop here after disconnect

        # 🟢 Otherwise → Try to connect both
        inner_port = self.inner_port_combo.get()
        outer_port = self.outer_port_combo.get()

        # Validate port selections
        if not inner_port or not outer_port:
            messagebox.showwarning(
                "No Port Selected",
                "Please select COM ports for both printers.\n\n"
                "Inner Printer: Select port for innerbox labels\n"
                "Outer Printer: Select port for outerbox labels"
            )
            return

        if inner_port == outer_port:
            messagebox.showerror(
                "Same Port Selected",
                "Inner and Outer printers cannot use the same COM port!\n"
                "Please select different ports for each printer."
            )
            return

        # Get baud rates
        inner_baud = int(self.inner_baud_combo.get())
        outer_baud = int(self.outer_baud_combo.get())

        # ✅ IMPORTANT: Disconnect any existing connections before attempting new ones
        # This prevents port conflicts
        if self.printer.is_inner_connected() or self.printer.is_outer_connected():
            self.printer.disconnect_all()
            import time
            time.sleep(0.2)  # Allow time for ports to be released

        # Attempt to connect
        inner_success = self.printer.connect_inner(inner_port, inner_baud)
        outer_success = self.printer.connect_outer(outer_port, outer_baud)

        # Update labels and logs
        if inner_success:
            self.inner_status_label.config(text=f"Status: Connected to {inner_port}", foreground="green")
            self.log(f"📦 Inner printer connected to {inner_port} at {inner_baud} baud")
        else:
            self.inner_status_label.config(text="Status: Connection Failed", foreground="red")
            self.log(f"❌ Failed to connect inner printer to {inner_port}")

        if outer_success:
            self.outer_status_label.config(text=f"Status: Connected to {outer_port}", foreground="green")
            self.log(f"📦 Outer printer connected to {outer_port} at {outer_baud} baud")
        else:
            self.outer_status_label.config(text="Status: Connection Failed", foreground="red")
            self.log(f"❌ Failed to connect outer printer to {outer_port}")

        # Update button based on results
        if inner_success or outer_success:
            self.connect_btn.config(text="Disconnect Both", style="Disconnect.TButton")

        # Show appropriate messages
        if inner_success and outer_success:
            messagebox.showinfo(
                "Success",
                f"✅ Both printers connected successfully!\n\n"
                f"Inner Printer: {inner_port} ({inner_baud} baud)\n"
                f"Outer Printer: {outer_port} ({outer_baud} baud)"
            )
        elif inner_success or outer_success:
            messagebox.showwarning(
                "Partial Connection",
                f"⚠️ Only one printer connected successfully.\n\n"
                f"Inner Printer: {'✅ Connected to ' + inner_port if inner_success else '❌ Failed'}\n"
                f"Outer Printer: {'✅ Connected to ' + outer_port if outer_success else '❌ Failed'}\n\n"
                f"Check your COM port settings and try again."
            )
        else:
            messagebox.showerror(
                "Connection Failed",
                "❌ Failed to connect both printers.\n\n"
                "Possible issues:\n"
                "• Printers are not powered on\n"
                "• Wrong COM ports selected\n"
                "• Ports are in use by another application\n"
                "• USB cables are disconnected\n\n"
                "Please check your settings and try again."
            )
            # Refresh ports on failure to show current available ports
            self.refresh_ports()

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
    
    def update_progress_display(self):
        """Update progress bar and labels"""
        self.pallet_label.config(text=f"Current Pallet: {self.pallet_count}")
        self.unit_label.config(text=f"Units: {self.unit_count} / {self.total_units_per_pallet}")
        
        if self.total_units_per_pallet > 0:
            progress_percent = (self.unit_count / self.total_units_per_pallet) * 100
            self.progress_bar['value'] = progress_percent
        else:
            self.progress_bar['value'] = 0

    # 🆕 NEW METHODS - ADD THESE TWO METHODS HERE
    def refresh_batch_count(self):
        """Manually refresh the database batch count display"""
        if self.current_pallet_batch_code is None:
            messagebox.showinfo(
                "No Batch Code",
                "No batch code is currently set.\n"
                "Scan an item to set a batch code first."
            )
            return
        
        # Fetch count from database
        existing_count = self.insert_db.get_batch_unit_count(
            self.current_pallet_batch_code, 
            self.po_num
        )
        
        # Update display
        self.batch_count_label.config(
            text=f"DB Batch Count: {existing_count} units",
            foreground="#0066CC"
        )
        
        self.log(f"🔄 Manual refresh: Batch '{self.current_pallet_batch_code}' has {existing_count} units in database")
        
        messagebox.showinfo(
            "Batch Count Refreshed",
            f"✅ Database Count Updated\n\n"
            f"Batch Code: {self.current_pallet_batch_code}\n"
            f"Total Units in DB: {existing_count}"
        )

    def update_batch_count_display(self, batch_code=None, po_num=None):
        """Update the batch count label with database count"""
        if batch_code is None:
            batch_code = self.current_pallet_batch_code
        if po_num is None:
            po_num = self.po_num
            
        if batch_code is None:
            self.batch_count_label.config(
                text="DB Batch Count: --",
                foreground="gray"
            )
            return
        
        # Fetch current count from database
        existing_count = self.insert_db.get_batch_unit_count(batch_code, po_num)
        
        # Update label
        self.batch_count_label.config(
            text=f"DB Batch Count: {existing_count} units",
            foreground="#0066CC"
        )
        
        self.log(f"📊 Batch count display updated: {existing_count} units for batch '{batch_code}'")

    # ✅ EXISTING METHODS CONTINUE BELOW
    def write_to_result_box(self, text):
        """Write text to the result box (handles read-only state)"""
        self.result_box.config(state='normal')
        self.result_box.insert("end", text)
        self.result_box.see("end")
        self.result_box.config(state='disabled')

    def clear_result_box(self):
        """Clear the barcode scanning result box"""
        self.result_box.config(state='normal')
        self.result_box.delete("1.0", tk.END)
        self.result_box.insert("1.0", "→ Waiting for scan...\n")
        self.result_box.config(state='disabled')
        self.log("Result box cleared")

    def clear_log(self):
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
        self.log_text.config(state='disabled')

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