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

    # 🆕 Check if serial already exists in packaging database
    existing_data = self.insert_db.check_existing_packaging(serial_num, po_num, batch_code)
    
    if existing_data:
        # Serial already packaged - offer reprint option
        innerbox_num = existing_data['innerbox']
        outerbox_num = existing_data['outerbox']
        pallet_num = existing_data['pallet_num']
        
        msg = (f"ℹ️ Serial '{serial_num}' is already packaged!\n"
            f"→ Batch Code: {batch_code}\n"
            f"→ Innerbox: {innerbox_num}\n"
            f"→ Outerbox: {outerbox_num}\n"
            f"→ Pallet: {pallet_num}\n")
        self.write_to_result_box(msg)
        self.log(msg)
        
        # Ask user what they want to reprint
        reprint_choice = messagebox.askquestion(
            "Already Packaged - Reprint Options",
            f"📦 Serial '{serial_num}' is already in the database!\n\n"
            f"Details:\n"
            f"• Batch Code: {batch_code}\n"
            f"• Innerbox: {innerbox_num}\n"
            f"• Outerbox: {outerbox_num}\n"
            f"• Pallet: {pallet_num}\n\n"
            f"Do you want to reprint labels?\n\n"
            f"YES = Inner Label Only\n"
            f"NO = Show More Options",
            icon='question'
        )
        
        if reprint_choice == 'yes':
            # Reprint inner label only
            if not self.printer.is_inner_connected():
                messagebox.showwarning(
                    "Inner Printer Not Connected",
                    "⚠️ Cannot reprint - inner printer is not connected!"
                )
                self.log(f"⚠️ Inner reprint failed - printer not connected")
            else:
                from zpl_codes import inner_zpl
                sku = "43000166102"
                barcode = f"{batch_code}-IB{innerbox_num:03d}"
                quantity = self.units_per_innerbox
                lot = batch_code
                innerbox_zpl = inner_zpl(sku, barcode, quantity, lot)
                
                if self.printer.send_to_inner_printer(innerbox_zpl):
                    self.log(f"✅ REPRINT SUCCESS: Innerbox #{innerbox_num} label reprinted")
                    messagebox.showinfo(
                        "Reprint Success",
                        f"✅ Inner label reprinted successfully!\n\n"
                        f"Innerbox: {innerbox_num}\n"
                        f"Batch Code: {batch_code}"
                    )
                else:
                    self.log(f"❌ REPRINT FAILED: Could not reprint innerbox #{innerbox_num}")
                    messagebox.showerror("Reprint Failed", "❌ Failed to send label to printer.")
        
        else:
            # Show additional reprint options
            reprint_outer = messagebox.askquestion(
                "Reprint Options",
                f"Choose what to reprint:\n\n"
                f"YES = Outer Label (Box #{outerbox_num})\n"
                f"NO = Both Inner & Outer Labels",
                icon='question'
            )
            
            if reprint_outer == 'yes':
                # Reprint outer label only
                if not self.printer.is_outer_connected():
                    messagebox.showwarning(
                        "Outer Printer Not Connected",
                        "⚠️ Cannot reprint - outer printer is not connected!"
                    )
                    self.log(f"⚠️ Outer reprint failed - printer not connected")
                else:
                    from zpl_codes import outer_zpl
                    sku = "43000166102"
                    lot_code = batch_code
                    quantity = self.innerboxes_per_outerbox * self.units_per_innerbox
                    
                    outerbox_zpl_data = outer_zpl(sku, lot_code, quantity)
                    
                    # Print 2 copies of outer label
                    self.log(f"🖨️ Reprinting outer label (2 copies) for box #{outerbox_num}...")
                    first_copy = self.printer.send_to_outer_printer(outerbox_zpl_data)
                    second_copy = self.printer.send_to_outer_printer(outerbox_zpl_data)
                    
                    if first_copy and second_copy:
                        self.log(f"✅ REPRINT SUCCESS: Outerbox #{outerbox_num} - 2 labels reprinted")
                        messagebox.showinfo(
                            "Reprint Success",
                            f"✅ Outer labels reprinted successfully!\n\n"
                            f"Outerbox: {outerbox_num}\n"
                            f"Batch Code: {batch_code}\n"
                            f"Copies: 2"
                        )
                    elif first_copy or second_copy:
                        self.log(f"⚠️ PARTIAL SUCCESS: Only 1 outer label printed for box #{outerbox_num}")
                        messagebox.showwarning(
                            "Partial Success",
                            f"⚠️ Only 1 outer label was printed.\n\n"
                            f"Please check printer and try again if needed."
                        )
                    else:
                        self.log(f"❌ REPRINT FAILED: Could not reprint outerbox #{outerbox_num}")
                        messagebox.showerror("Reprint Failed", "❌ Failed to send labels to printer.")
            
            else:
                # Reprint both inner and outer labels
                inner_printed = False
                outer_printed = False
                
                # Print inner label
                if not self.printer.is_inner_connected():
                    messagebox.showwarning(
                        "Inner Printer Not Connected",
                        "⚠️ Inner printer is not connected!\n"
                        "Will attempt to print outer label only."
                    )
                    self.log(f"⚠️ Inner reprint skipped - printer not connected")
                else:
                    from zpl_codes import inner_zpl
                    sku = "43000166102"
                    barcode = f"{batch_code}-IB{innerbox_num:03d}"
                    quantity = self.units_per_innerbox
                    lot = batch_code
                    innerbox_zpl = inner_zpl(sku, barcode, quantity, lot)
                    
                    if self.printer.send_to_inner_printer(innerbox_zpl):
                        inner_printed = True
                        self.log(f"✅ REPRINT SUCCESS: Innerbox #{innerbox_num} label reprinted")
                    else:
                        self.log(f"❌ Inner reprint failed for box #{innerbox_num}")
                
                # Print outer label
                if not self.printer.is_outer_connected():
                    messagebox.showwarning(
                        "Outer Printer Not Connected",
                        "⚠️ Outer printer is not connected!\n"
                        f"Inner label: {'✅ Printed' if inner_printed else '❌ Failed'}"
                    )
                    self.log(f"⚠️ Outer reprint skipped - printer not connected")
                else:
                    from zpl_codes import outer_zpl
                    sku = "43000166102"
                    lot_code = batch_code
                    quantity = self.innerboxes_per_outerbox * self.units_per_innerbox
                    
                    outerbox_zpl_data = outer_zpl(sku, lot_code, quantity)
                    
                    # Print 2 copies
                    self.log(f"🖨️ Reprinting outer label (2 copies) for box #{outerbox_num}...")
                    first_copy = self.printer.send_to_outer_printer(outerbox_zpl_data)
                    second_copy = self.printer.send_to_outer_printer(outerbox_zpl_data)
                    
                    if first_copy and second_copy:
                        outer_printed = True
                        self.log(f"✅ REPRINT SUCCESS: Outerbox #{outerbox_num} - 2 labels reprinted")
                    elif first_copy or second_copy:
                        outer_printed = True
                        self.log(f"⚠️ PARTIAL: Only 1 outer label printed for box #{outerbox_num}")
                    else:
                        self.log(f"❌ Outer reprint failed for box #{outerbox_num}")
                
                # Show final result
                if inner_printed and outer_printed:
                    messagebox.showinfo(
                        "Reprint Success",
                        f"✅ Both labels reprinted successfully!\n\n"
                        f"Innerbox: {innerbox_num}\n"
                        f"Outerbox: {outerbox_num}\n"
                        f"Batch Code: {batch_code}"
                    )
                elif inner_printed or outer_printed:
                    messagebox.showwarning(
                        "Partial Success",
                        f"⚠️ Reprint partially successful:\n\n"
                        f"Inner Label: {'✅ Printed' if inner_printed else '❌ Failed'}\n"
                        f"Outer Label: {'✅ Printed' if outer_printed else '❌ Failed'}\n\n"
                        f"Check printer connections and try again if needed."
                    )
                else:
                    messagebox.showerror(
                        "Reprint Failed",
                        "❌ Failed to reprint both labels.\n\n"
                        "Please check printer connections and try again."
                    )
        
        # Clear entry and refocus
        self.serial_entry.delete(0, tk.END)
        self.serial_entry.focus()
        return  # Exit here - don't process as new item

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
    
    # 🆕 7️⃣ FETCH EXISTING COUNT FROM DATABASE FOR THIS BATCH CODE
    # This prevents duplicate box numbering by checking how many units already packaged
    existing_count = self.insert_db.get_batch_unit_count(batch_code, po_num)
    self.log(f"📊 Database check: {existing_count} units already packaged for batch {batch_code}")
    
    # ✅ Update the GUI batch count display
    self.update_batch_count_display(batch_code, po_num)
    
    # Calculate the ACTUAL next unit position based on database count
    next_unit = existing_count + 1
    current_innerbox = ((next_unit - 1) // self.units_per_innerbox) + 1
    current_outerbox = ((current_innerbox - 1) // self.innerboxes_per_outerbox) + 1
    
    # 🔍 DEBUG: Log calculation details
    self.log(f"🔍 Box Calculation (Database-based):")
    self.log(f"   → Existing DB count: {existing_count}")
    self.log(f"   → Next unit position: {next_unit}")
    self.log(f"   → Calculated innerbox: {current_innerbox}")
    self.log(f"   → Calculated outerbox: {current_outerbox}")
    
    # 8️⃣ NOW record to database (after all validations passed)
    self.log(f"💾 Attempting database insert...")
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
        self.serial_entry.delete(0, tk.END)
        self.serial_entry.focus()
        return
    else:
        self.log(f"✅ Database record successful (innerbox={current_innerbox}, outerbox={current_outerbox})")
    
    # 9️⃣ Update unit count (local counter for progress bar)
    self.unit_count += 1
    self.log(f"📊 Local unit count updated: {self.unit_count}/{self.total_units_per_pallet}")
    self.update_progress_display()

    # 🔟 Print innerbox label when needed (based on DATABASE count, not local count)
    innerbox_printed = False
    self.log(f"🔍 Innerbox Check: {next_unit} % {self.units_per_innerbox} = {next_unit % self.units_per_innerbox}")
    
    if next_unit % self.units_per_innerbox == 0:
        self.log(f"✅ INNERBOX CONDITION MET - Attempting to print innerbox #{current_innerbox}")
        
        if not self.printer.is_inner_connected():
            messagebox.showwarning(
                "Inner Printer Not Connected", 
                "⚠️ Inner box printer is not connected.\n"
                "Label will NOT be printed!"
            )
            self.log(f"⚠️ INNERBOX #{current_innerbox} label NOT printed - printer disconnected")
        else:
            self.log(f"🖨️ Sending ZPL to inner printer...")
            from zpl_codes import inner_zpl
            sku = "43000166102"
            barcode = f"{batch_code}-IB{current_innerbox:03d}"
            quantity = self.units_per_innerbox
            lot = batch_code
            innerbox_zpl = inner_zpl(sku, barcode, quantity, lot)
            
            if self.printer.send_to_inner_printer(innerbox_zpl):
                innerbox_printed = True
                self.log(f"✅ INNERBOX #{current_innerbox} label printed successfully (Outerbox {current_outerbox})")
            else:
                self.log(f"❌ Failed to print INNERBOX #{current_innerbox} label")
    else:
        remaining = self.units_per_innerbox - (next_unit % self.units_per_innerbox)
        self.log(f"ℹ️ Not time for innerbox yet (need {remaining} more units)")
    
    # 1️⃣1️⃣ Print outerbox label when needed (based on DATABASE count)
    outerbox_printed = False
    units_per_outerbox = self.units_per_innerbox * self.innerboxes_per_outerbox
    
    # Debug logging for outerbox
    self.log(f"")
    self.log(f"🔍 ========== OUTERBOX CHECK ==========")
    self.log(f"   • Database unit count: {next_unit}")
    self.log(f"   • units_per_innerbox: {self.units_per_innerbox}")
    self.log(f"   • innerboxes_per_outerbox: {self.innerboxes_per_outerbox}")
    self.log(f"   • units_per_outerbox: {units_per_outerbox}")
    self.log(f"   • Modulo calculation: {next_unit} % {units_per_outerbox} = {next_unit % units_per_outerbox}")
    self.log(f"   • Should print outerbox: {next_unit % units_per_outerbox == 0}")
    self.log(f"   • Outer printer connected: {self.printer.is_outer_connected()}")
    self.log(f"   • Target outerbox number: {current_outerbox}")
    self.log(f"🔍 =====================================")
    self.log(f"")
    
    if next_unit % units_per_outerbox == 0:
        self.log(f"✅✅ OUTERBOX CONDITION MET! Attempting to print outerbox #{current_outerbox}")
        
        if not self.printer.is_outer_connected():
            messagebox.showwarning(
                "Outer Printer Not Connected", 
                "⚠️ Outer box printer is not connected.\n"
                "Label will NOT be printed!"
            )
            self.log(f"⚠️ OUTERBOX #{current_outerbox} label NOT printed - printer disconnected")
        else:
            self.log(f"🖨️ Sending ZPL to outer printer (2 copies)...")
            from zpl_codes import outer_zpl
            sku = "43000166102"
            lot_code = batch_code
            quantity = self.innerboxes_per_outerbox * self.units_per_innerbox
            
            self.log(f"📄 ZPL Parameters: SKU={sku}, Lot={lot_code}, Qty={quantity}, Box={current_outerbox}")
            
            outerbox_zpl_data = outer_zpl(sku, lot_code, quantity)
            
            # 🎯 PRINT FIRST COPY
            self.log(f"📤 Printing copy 1/2...")
            first_copy = self.printer.send_to_outer_printer(outerbox_zpl_data)
            
            # 🎯 PRINT SECOND COPY
            self.log(f"📤 Printing copy 2/2...")
            second_copy = self.printer.send_to_outer_printer(outerbox_zpl_data)
            
            # Check results
            if first_copy and second_copy:
                outerbox_printed = True
                self.log(f"✅✅ OUTERBOX #{current_outerbox} - 2 labels printed successfully!")
            elif first_copy or second_copy:
                outerbox_printed = True
                self.log(f"⚠️ OUTERBOX #{current_outerbox} - Only 1 label printed (partial success)")
            else:
                self.log(f"❌ Failed to print OUTERBOX #{current_outerbox} labels - both copies failed")
    else:
        remaining_units = units_per_outerbox - (next_unit % units_per_outerbox)
        self.log(f"ℹ️ Not time for outerbox yet (need {remaining_units} more units)")

    # 1️⃣2️⃣ Update database status after successful processing
    self.log(f"💾 Updating packaging status in database...")
    db_update_success = self.insert_db.update_packaging_status(serial_num, po_num, batch_code)
    
    if db_update_success:
        self.log(f"✅ Database updated: packaging=1, status=1 for serial {serial_num}")
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
        self.log(f"🎉 PALLET {self.pallet_count} COMPLETED - Starting new pallet")
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
    
    self.log(f"{'='*60}")