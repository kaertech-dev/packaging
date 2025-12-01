# PACKAGINS/check_serial_in_database.py
from tkinter import messagebox, ttk
import tkinter as tk

def check_serial_in_db(self):
    """Check serial number in database and handle printing"""
    serial_num = self.serial_entry.get().strip()
    
    # 1️⃣ Validate input
    if not serial_num:
        messagebox.showwarning("Empty Input", "Please scan or enter a serial number.")
        return

    # 2️⃣ Check box selection
    if self.total_units_per_pallet == 0:
        messagebox.showwarning("No Box Selection", "Please select boxes per pallet first.")
        return

    # 3️⃣ Check printer connections
    if not self.printer.is_inner_connected() and not self.printer.is_outer_connected():
        messagebox.showwarning(
            "Printers Not Connected", 
            "⚠️ Please connect to printers before scanning.\n\n"
            "No data will be recorded until printers are connected."
        )
        self._clear_and_focus()
        return

    # 4️⃣ Validate serial in database
    batch_code, po_num = self.db.get_batch_and_po(serial_num)
    if not batch_code or not po_num:
        self._log_and_display(f"❌ Serial '{serial_num}' not found in faceware_assembly1.\n")
        self._clear_and_focus()
        return

    # 5️⃣ Check if serial already exists
    existing_data = self.insert_db.check_existing_packaging(serial_num, po_num, batch_code)
    if existing_data:
        self._handle_reprint(serial_num, batch_code, existing_data)
        return

    # 6️⃣ Check batch code consistency
    if not self._validate_batch_code(batch_code):
        self._log_and_display(f"❌ REJECTED: Serial '{serial_num}' has different batch code ({batch_code})\n")
        self._clear_and_focus()
        return

    # 7️⃣ Display validation success
    self._log_and_display(f"✅ Serial: {serial_num}\n→ Batch Code: {batch_code}\n→ PO Number: {po_num}\n")
    
    # 8️⃣ Get existing count and calculate box numbers
    existing_count = self.insert_db.get_batch_unit_count(batch_code, po_num)
    next_unit = existing_count + 1
    current_innerbox = ((next_unit - 1) // self.units_per_innerbox) + 1
    current_outerbox = ((current_innerbox - 1) // self.innerboxes_per_outerbox) + 1
    
    self.log(f"📊 Database check: {existing_count} units already packaged for batch {batch_code}")
    self.update_batch_count_display(batch_code, po_num)
    
    # 9️⃣ Check pallet capacity
    if not self._check_pallet_capacity(po_num):
        return

    # 🔟 Record to database
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
        self.log("❌ Failed to record to database - STOPPING HERE")
        self._clear_and_focus()
        return
    
    self.log(f"✅ Database record successful (innerbox={current_innerbox}, outerbox={current_outerbox})")
    
    # 1️⃣1️⃣ Update counters and print labels
    self.unit_count += 1
    self.log(f"📊 Local unit count updated: {self.unit_count}/{self.total_units_per_pallet}")
    self.update_progress_display()
    
    self._print_innerbox_if_needed(current_innerbox, batch_code, next_unit)
    self._print_outerbox_if_needed(current_outerbox, batch_code, next_unit)
    
    # 1️⃣2️⃣ Update database status
    if self.insert_db.update_packaging_status(serial_num, po_num, batch_code):
        self.log(f"✅ Database updated: packaging=1, status=1 for serial {serial_num}")
    else:
        self.log(f"⚠️ Warning: Failed to update packaging status in database")

    # 1️⃣3️⃣ Check if pallet is complete
    if self.unit_count >= self.total_units_per_pallet:
        self._complete_pallet(batch_code)
    
    # 1️⃣4️⃣ Clear entry and refocus
    self._clear_and_focus()
    self.log(f"{'='*60}")

# ========== HELPER METHODS ==========

def _clear_and_focus(self):
    """Clear serial entry and refocus"""
    self.serial_entry.delete(0, tk.END)
    self.serial_entry.focus()

def _log_and_display(self, msg):
    """Log and display message in result box"""
    self.write_to_result_box(msg)
    self.log(msg)

def _validate_batch_code(self, batch_code):
    """Validate batch code consistency with current pallet"""
    if self.current_pallet_batch_code is None:
        self.current_pallet_batch_code = batch_code
        self.batch_label.config(text=f"Pallet Batch Code: {batch_code}", foreground="green")
        self.log(f"🔒 Pallet {self.pallet_count} locked to Batch Code: {batch_code}")
        self.sync_pallet_progress_with_db()
        return True
    elif self.current_pallet_batch_code != batch_code:
        messagebox.showerror(
            "Batch Code Mismatch",
            f"❌ Cannot add this item to current pallet!\n\n"
            f"Current Pallet Batch Code: {self.current_pallet_batch_code}\n"
            f"Scanned Item Batch Code: {batch_code}\n\n"
            f"All items in a pallet must have the same batch code.\n\n"
            f"Click 'New Batch Code' button to start a new batch."
        )
        return False
    return True

def _check_pallet_capacity(self, po_num):
    """Check if pallet has capacity, move to next if full"""
    current_pallet_db_count = self.insert_db.get_pallet_unit_count(self.pallet_count, po_num)
    total_in_pallet = current_pallet_db_count + 1
    
    self.log(f"🔍 Pallet Capacity Check: {current_pallet_db_count} + 1 = {total_in_pallet}/{self.total_units_per_pallet}")
    
    if total_in_pallet > self.total_units_per_pallet:
        messagebox.showinfo(
            "Pallet Full",
            f"⚠️ Current pallet {self.pallet_count} is at capacity!\n"
            f"Moving to pallet {self.pallet_count + 1}..."
        )
        self.pallet_count += 1
        self.unit_count = 0
        self.log(f"📦 Started new pallet: Pallet {self.pallet_count}")
        self.update_progress_display()
    return True

def _handle_reprint(self, serial_num, batch_code, existing_data):
    """Handle reprint option for already packaged serials"""
    innerbox_num = existing_data['innerbox']
    outerbox_num = existing_data['outerbox']
    pallet_num = existing_data['pallet_num']
    
    msg = (f"ℹ️ Serial '{serial_num}' is already packaged!\n"
           f"→ Batch Code: {batch_code}\n"
           f"→ Innerbox: {innerbox_num}\n"
           f"→ Outerbox: {outerbox_num}\n"
           f"→ Pallet: {pallet_num}\n")
    self._log_and_display(msg)
    
    if not messagebox.askyesno(
        "Already Packaged - Reprint?",
        f"📦 Serial '{serial_num}' is already in the database!\n\n"
        f"Details:\n• Batch Code: {batch_code}\n• Innerbox: {innerbox_num}\n"
        f"• Outerbox: {outerbox_num}\n• Pallet: {pallet_num}\n\n"
        f"Do you want to reprint the inner label?"
    ):
        self.log(f"ℹ️ User declined reprint for serial {serial_num}")
        self._clear_and_focus()
        return
    
    if not self.printer.is_inner_connected():
        messagebox.showwarning("Inner Printer Not Connected", "⚠️ Cannot reprint - inner printer is not connected!")
        self.log(f"⚠️ Reprint failed - inner printer not connected")
    else:
        from zpl_codes import inner_zpl
        innerbox_zpl = inner_zpl("43000166102", f"{batch_code}-IB{innerbox_num:03d}", self.units_per_innerbox, batch_code)
        
        if self.printer.send_to_inner_printer(innerbox_zpl):
            self.log(f"✅ REPRINT SUCCESS: Innerbox #{innerbox_num} label reprinted")
            messagebox.showinfo("Reprint Success", f"✅ Inner label reprinted!\n\nInnerbox: {innerbox_num}\nBatch Code: {batch_code}")
        else:
            self.log(f"❌ REPRINT FAILED: Could not reprint innerbox #{innerbox_num}")
            messagebox.showerror("Reprint Failed", "❌ Failed to send label to printer.")
    
    self._clear_and_focus()

def _print_innerbox_if_needed(self, current_innerbox, batch_code, next_unit):
    """Print inner box label if condition is met"""
    if next_unit % self.units_per_innerbox == 0:
        self.log(f"✅ INNERBOX CONDITION MET - Attempting to print innerbox #{current_innerbox}")
        
        if not self.printer.is_inner_connected():
            messagebox.showwarning("Inner Printer Not Connected", "⚠️ Inner box printer is not connected.\nLabel will NOT be printed!")
            self.log(f"⚠️ INNERBOX #{current_innerbox} label NOT printed - printer disconnected")
            return
        
        from zpl_codes import inner_zpl
        innerbox_zpl = inner_zpl("43000166102", f"{batch_code}-IB{current_innerbox:03d}", self.units_per_innerbox, batch_code)
        
        if self.printer.send_to_inner_printer(innerbox_zpl):
            self.log(f"✅ INNERBOX #{current_innerbox} label printed successfully")
        else:
            self.log(f"❌ Failed to print INNERBOX #{current_innerbox} label")
    else:
        remaining = self.units_per_innerbox - (next_unit % self.units_per_innerbox)
        self.log(f"ℹ️ Not time for innerbox yet (need {remaining} more units)")

def _print_outerbox_if_needed(self, current_outerbox, batch_code, next_unit):
    """Print outer box label if condition is met"""
    units_per_outerbox = self.units_per_innerbox * self.innerboxes_per_outerbox
    
    if next_unit % units_per_outerbox == 0:
        self.log(f"✅ OUTERBOX CONDITION MET! Attempting to print outerbox #{current_outerbox}")
        
        if not self.printer.is_outer_connected():
            messagebox.showwarning("Outer Printer Not Connected", "⚠️ Outer box printer is not connected.\nLabel will NOT be printed!")
            self.log(f"⚠️ OUTERBOX #{current_outerbox} label NOT printed - printer disconnected")
            return
        
        from zpl_codes import outer_zpl
        outerbox_zpl = outer_zpl("43000166102", batch_code, self.innerboxes_per_outerbox * self.units_per_innerbox)
        
        copies_printed = sum([self.printer.send_to_outer_printer(outerbox_zpl) for _ in range(2)])
        
        if copies_printed == 2:
            self.log(f"✅ OUTERBOX #{current_outerbox} - 2 labels printed successfully!")
        elif copies_printed == 1:
            self.log(f"⚠️ OUTERBOX #{current_outerbox} - Only 1 label printed (partial success)")
        else:
            self.log(f"❌ Failed to print OUTERBOX #{current_outerbox} labels")
    else:
        remaining = units_per_outerbox - (next_unit % units_per_outerbox)
        self.log(f"ℹ️ Not time for outerbox yet (need {remaining} more units)")

def _complete_pallet(self, batch_code):
    """Handle pallet completion"""
    messagebox.showinfo(
        "Pallet Complete", 
        f"🎉 Pallet {self.pallet_count} is complete!\n"
        f"Batch Code: {batch_code}\n"
        f"Total units: {self.unit_count}\n"
        f"Starting new pallet..."
    )
    self.log(f"🎉 PALLET {self.pallet_count} COMPLETED - Starting new pallet")
    self.pallet_count += 1
    self.unit_count = 0
    self.current_pallet_batch_code = None
    self.batch_label.config(text="Batch Code: Not Set", foreground="orange")
    self.update_progress_display()

# ...existing code...

# Add this new method to check_serial_in_database.py
# Replace the existing _show_batch_selection_dialog method with this improved version:

def show_batch_selection_dialog(self):
    """Display unfinished batches in a user-friendly dialog with dropdown selection."""
    batches = self.insert_db.get_unfinished_batches()
    
    if not batches:
        messagebox.showinfo(
            "No Unfinished Batches", 
            "✅ All batches are complete.\n\n"
            "You can start a new batch by scanning an item."
        )
        return

    # Create custom dialog window
    dialog = tk.Toplevel(self.root)
    dialog.title("Change Batch Code")
    dialog.geometry("500x400")
    dialog.transient(self.root)
    dialog.grab_set()
    
    # Center the dialog
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
    y = (dialog.winfo_screenheight() // 2) - (400 // 2)
    dialog.geometry(f"500x400+{x}+{y}")

    # Header
    header_frame = tk.Frame(dialog, bg="#0066CC", height=50)
    header_frame.pack(fill="x")
    header_label = tk.Label(
        header_frame,
        text="📦 Select Unfinished Batch Code",
        bg="#0066CC",
        fg="white",
        font=("Segoe UI", 12, "bold")
    )
    header_label.pack(pady=10)

    # Info label
    info_frame = tk.Frame(dialog, bg="white")
    info_frame.pack(fill="x", padx=20, pady=10)
    info_label = tk.Label(
        info_frame,
        text=f"Found {len(batches)} unfinished batch(es).\nSelect a batch to continue working on:",
        bg="white",
        font=("Segoe UI", 9),
        justify="left"
    )
    info_label.pack(anchor="w")

    # Batch list frame with scrollbar
    list_frame = tk.Frame(dialog, bg="white")
    list_frame.pack(fill="both", expand=True, padx=20, pady=10)

    scrollbar = tk.Scrollbar(list_frame)
    scrollbar.pack(side="right", fill="y")

    batch_listbox = tk.Listbox(
        list_frame,
        font=("Consolas", 9),
        height=10,
        yscrollcommand=scrollbar.set,
        selectmode="single"
    )
    batch_listbox.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=batch_listbox.yview)

    # Populate listbox with formatted batch info
    batch_map = {}  # Map display text to batch data
    for idx, batch in enumerate(batches):
        display_text = (
            f"{batch['batch_code']:<15} | "
            f"PO: {batch['po_num']:<10} | "
            f"Pallet: {batch['pallet_num']:<3} | "
            f"Units: {batch['unit_count']}"
        )
        batch_listbox.insert(tk.END, display_text)
        batch_map[idx] = batch

    # Button frame
    button_frame = tk.Frame(dialog, bg="white")
    button_frame.pack(fill="x", padx=20, pady=10)

    def on_select():
        selection = batch_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a batch from the list.")
            return
        
        selected_batch = batch_map[selection[0]]
        dialog.destroy()
        self._switch_to_batch(selected_batch)

    def on_cancel():
        dialog.destroy()

    # Select button
    select_btn = ttk.Button(
        button_frame,
        text="✓ Select Batch",
        command=on_select,
        style="Connect.TButton",
        width=15
    )
    select_btn.pack(side="left", padx=5)

    # Cancel button
    cancel_btn = ttk.Button(
        button_frame,
        text="✗ Cancel",
        command=on_cancel,
        style="Disconnect.TButton",
        width=15
    )
    cancel_btn.pack(side="left", padx=5)

    # Bind double-click to select
    batch_listbox.bind("<Double-Button-1>", lambda e: on_select())

    # Focus on listbox and select first item
    batch_listbox.focus_set()
    if len(batches) > 0:
        batch_listbox.selection_set(0)


def _switch_to_batch(self, batch_data):
    """Switch current pallet context to an existing unfinished batch."""
    batch_code = batch_data['batch_code']
    pallet_num = batch_data['pallet_num']
    unit_count = batch_data['unit_count']
    po_num = batch_data['po_num']
    
    # Confirm if current batch has units
    if self.unit_count > 0 and self.current_pallet_batch_code:
        result = messagebox.askyesno(
            "Switch Batch?",
            f"⚠️ Current batch has {self.unit_count} units!\n\n"
            f"Current Batch: {self.current_pallet_batch_code}\n"
            f"New Batch: {batch_code}\n\n"
            f"Switching will mark current pallet as incomplete.\n"
            f"Continue?"
        )
        if not result:
            return
        
        # Log the incomplete pallet
        self.log(
            f"🔄 Switched from Batch '{self.current_pallet_batch_code}' "
            f"(Pallet {self.pallet_count}, {self.unit_count} units - Incomplete)"
        )
    
    # Switch to new batch
    self.current_pallet_batch_code = batch_code
    self.pallet_count = pallet_num
    self.unit_count = unit_count
    self.po_num = po_num
    
    # Update UI
    self.batch_label.config(
        text=f"Pallet Batch Code: {batch_code}",
        foreground="green"
    )
    
    self.log(
        f"🔄 BATCH SWITCHED → '{batch_code}' "
        f"(Pallet {pallet_num}, {unit_count} units, PO: {po_num})"
    )
    
    # Update displays
    self.update_progress_display()
    self.update_batch_count_display(batch_code, po_num)
    
    messagebox.showinfo(
        "Batch Changed",
        f"✅ Successfully switched to batch!\n\n"
        f"Batch Code: {batch_code}\n"
        f"Pallet: {pallet_num}\n"
        f"Current Units: {unit_count}\n"
        f"PO Number: {po_num}"
    )

def _complete_pallet(self, batch_code):
    """Handle pallet complete: let user start new pallet or change batch."""
    result = messagebox.askyesnocancel(
        "Pallet Complete",
        f"Pallet {self.pallet_count} complete.\nBatch: {batch_code}\nUnits: {self.unit_count}\n\nYes=start new pallet\nNo=Change to existing unfinished batch\nCancel=do nothing"
    )
    if result is True:
        # start new pallet
        self.pallet_count += 1
        self.unit_count = 0
        self.current_pallet_batch_code = None
        self.batch_label.config(text="Batch Code: Not Set", foreground="orange")
        self.log(f"Started new pallet {self.pallet_count}")
        self.update_progress_display()
    elif result is False:
        # change to existing unfinished batch
        self._show_batch_selection_dialog()
    # else: cancel -> keep current state

# ...existing code...