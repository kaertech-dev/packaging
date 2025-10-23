from tkinter import ttk, messagebox
import tkinter as tk
def show_ship_mode_dialog(self, username, shift, shift_mode):
    self.username = username,
    self.shift = shift,
    self.shift_mode = shift_mode
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
