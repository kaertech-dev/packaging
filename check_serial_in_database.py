from tkinter import messagebox
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

    # 3️⃣ Check printer connections BEFORE doing anything else
    if not self.printer.is_inner_connected() and not self.printer.is_outer_connected():
        messagebox.showwarning(
            "Printers Not Connected", 
            "⚠️ Please connect to printers before scanning.\n\n"
            "No data will be recorded until printers are connected."
        )
        self.serial_entry.delete(0, tk.END)
        self.serial_entry.focus()
        return

    # 4️⃣ Validate serial number in database
    batch_code, po_num = self.db.get_batch_and_po(serial_num)

    if not batch_code or not po_num:
        msg = f"❌ Serial '{serial_num}' not found in faceware_assembly1.\n"
        self.write_to_result_box(msg)
        self.log(msg)
        self.serial_entry.delete(0, tk.END)
        self.serial_entry.focus()
        return

    # 5️⃣ Check batch code consistency
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

    # 6️⃣ Display validation success
    msg = f"✅ Serial: {serial_num}\n→ Batch Code: {batch_code}\n→ PO Number: {po_num}\n"
    self.write_to_result_box(msg)
    self.log(msg)
    
    # 7️⃣ Calculate box numbers
    next_unit = self.unit_count + 1
    current_innerbox = ((next_unit - 1) // self.units_per_innerbox) + 1
    current_outerbox = ((current_innerbox - 1) // self.innerboxes_per_outerbox) + 1
    
    # 8️⃣ NOW record to database (after all validations passed)
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
        self.log("❌ Failed to record to database")
        self.serial_entry.delete(0, tk.END)
        self.serial_entry.focus()
        return
    
    # 9️⃣ Update unit count
    self.unit_count += 1
    self.update_progress_display()

    # 🔟 Print innerbox label when needed
    innerbox_printed = False
    if self.unit_count % self.units_per_innerbox == 0:
        if not self.printer.is_inner_connected():
            messagebox.showwarning(
                "Inner Printer Not Connected", 
                "⚠️ Inner box printer is not connected.\n"
                "Label will NOT be printed!"
            )
            self.log(f"⚠️ INNERBOX #{current_innerbox} label NOT printed - printer disconnected")
        else:
            from zpl_codes import inner_zpl
            sku = "43000166102"
            barcode = f"{batch_code}-IB{current_innerbox:03d}"
            quantity = self.units_per_innerbox
            lot = batch_code
            innerbox_zpl = inner_zpl(sku, barcode, quantity, lot)
            
            if self.printer.send_to_inner_printer(innerbox_zpl):
                innerbox_printed = True
                self.log(f"📦 INNERBOX #{current_innerbox} label printed (Outerbox {current_outerbox})")
            else:
                self.log(f"❌ Failed to print INNERBOX #{current_innerbox} label")
    
    # 1️⃣1️⃣ Print outerbox label when needed
    outerbox_printed = False
    if self.unit_count % (self.units_per_innerbox * self.innerboxes_per_outerbox) == 0:
        if not self.printer.is_outer_connected():
            messagebox.showwarning(
                "Outer Printer Not Connected", 
                "⚠️ Outer box printer is not connected.\n"
                "Label will NOT be printed!"
            )
            self.log(f"⚠️ OUTERBOX #{current_outerbox} label NOT printed - printer disconnected")
        else:
            from zpl_codes import outer_zpl
            sku = "43000166102"
            lot_code = batch_code
            quantity = self.innerboxes_per_outerbox * self.units_per_innerbox
            outerbox_zpl_data = outer_zpl(sku, lot_code, quantity, current_outerbox)
            
            if self.printer.send_to_outer_printer(outerbox_zpl_data):
                outerbox_printed = True
                self.log(f"📦📦 OUTERBOX #{current_outerbox} label printed")
            else:
                self.log(f"❌ Failed to print OUTERBOX #{current_outerbox} label")

    # 1️⃣2️⃣ ✅ NEW: Update database status after successful processing
    # Update faceware_main.packaging = 1 and faceware_packaging.status = 1
    db_update_success = self.insert_db.update_packaging_status(serial_num, po_num, batch_code)
    
    if db_update_success:
        self.log(f"✅ Database updated: packaging=1 for serial {serial_num}")
    else:
        self.log(f"⚠️ Warning: Failed to update packaging status in database")

    # 1️⃣3️⃣ Check if pallet is complete
    if self.unit_count >= self.total_units_per_pallet:
        messagebox.showinfo(
            "Pallet Complete", 
            f"🎉 Pallet {self.pallet_count} is complete!\n"
            f"Batch Code: {self.current_pallet_batch_code}\n"
            f"Total units: {self.unit_count}\n"
            f"Starting new pallet..."
        )
        self.pallet_count += 1
        self.unit_count = 0
        self.current_pallet_batch_code = None
        self.batch_label.config(
            text="Batch Code: Not Set",
            foreground="orange"
        )
        self.update_progress_display()
    
    # 1️⃣4️⃣ Clear entry and refocus
    self.serial_entry.delete(0, tk.END)
    self.serial_entry.focus()