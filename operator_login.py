# PACKAGINS/operator_login.py
import tkinter as tk
from tkinter import ttk, messagebox
import re
from datetime import datetime
from gui_main import ZPLPrinterGUI  # your main printing GUI
from widget_design import apply_widget_styles, create_green_header


class OperatorLogin:
    def __init__(self, root):
        self.root = root
        self.root.title("Operator Login")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # Center the window on screen
        self.center_window(400, 300)

        self.username_var = tk.StringVar()
        self.shift_var = tk.StringVar()
        self.ship_mode_var = tk.StringVar()

        self.serial_num = ""  # optional
        self.po_num = ""      # optional

        self.create_login_ui()
        apply_widget_styles()

    def center_window(self, width, height):
        """Center the window on the screen"""
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate position
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # Set geometry with position
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    # ---------------- Login Page ----------------
    def create_login_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        # 🟩 Green Header with Image
        create_green_header(
            self.root,
            text="Operator Login",
            image_path=r"C:\Users\production\Desktop\updated_packaging\packagins\kaertech_logo512.png",  # 👈 your image path
            img_size=(40, 40)
        )
        #tk.Label(self.root, text="Operator Login", font=("Arial", 16, "bold")).pack(pady=10)
        tk.Label(self.root, text="Enter Operator ID (KE0000 or LL0000):").pack()

        username_entry = ttk.Entry(self.root, textvariable=self.username_var, font=("Arial", 12))
        username_entry.pack(pady=8)
        username_entry.focus()

        # 🔹 Shift Selection
        tk.Label(self.root, text="Select Shift:").pack(pady=(10, 0))
        shift_dropdown = ttk.Combobox(
            self.root,
            textvariable=self.shift_var,
            values=["---Select Shift---", "A", "B", "C"],
            state="readonly",
            font=("Arial", 11),
            width=15
        )
        shift_dropdown.pack(pady=5)
        shift_dropdown.current(0)

        login_button = ttk.Button(self.root, text="Login", command=self.login, style="Login.TButton")
        login_button.pack(pady=15)

        # Allow Enter key to trigger login
        self.root.bind('<Return>', lambda event: self.login())

    # ---------------- Login Validation ----------------
    def login(self):
        username = self.username_var.get().strip()
        shift = self.shift_var.get()

        # Initialize warning counter if it doesn't exist yet
        if not hasattr(self, "shift_warning_count"):
            self.shift_warning_count = 0
            
        if not re.match(r"^(KE|LL)\d{4}$", username):
            messagebox.showerror(
                "Invalid Format",
                "Invalid Operator ID.\nUse uppercase KE0000 or LL0000 only (e.g., KE0412)."
            )
            return

        # Check if shift is not selected
        if shift == "---Select Shift---" or not shift:
            self.shift_warning_count += 1  # increase count each time

            if self.shift_warning_count >= 2:
                messagebox.showerror("Ang kulit!", "Ang kulit, Select Shift nga MUNA!!")
            else:
                messagebox.showwarning("Missing Shift", "Please select a shift (A or B or C).")

            return

        # Reset the warning counter when a valid shift is selected
        self.shift_warning_count = 0

        # Proceed to ship mode selection
        self.select_ship_mode(username, shift)

    # ---------------- Shipping Mode Selection ----------------
    def select_ship_mode(self, username, shift):
        for widget in self.root.winfo_children():
            widget.destroy()

        # 🟩 Header with logo
        create_green_header(
            self.root,
            text="Shipping Mode Selection",
            image_path=r"C:\Users\ai\Documents\packaging\packaging\kaertech_logo512.png",
            img_size=(40, 40)
        )

        # 🟩 Compact Welcome Box (1 row)
        from widget_design import create_bordered_box
        create_bordered_box(self.root, username)

        # 🔹 Shift label
        tk.Label(self.root, text=f"Shift: {shift}", font=("Arial", 12)).pack(pady=3)
        tk.Label(self.root, text="Select Shipping Mode:", font=("Arial", 12, "bold")).pack(pady=(10, 5))

        # 🔹 Dropdown for shipping mode
        ship_dropdown = ttk.Combobox(
            self.root,
            textvariable=self.ship_mode_var,
            values=["---Select Mode---", "SEA", "AIR"],
            state="readonly",
            font=("Arial", 11),
            width=15
        )
        ship_dropdown.pack(pady=5)
        ship_dropdown.current(0)

        # 🔹 Confirm button
        confirm_button = ttk.Button(
            self.root,
            text="Confirm & Continue",
            command=lambda: self.confirm_ship_mode(username, shift)
        )
        confirm_button.pack(pady=20)

    def confirm_ship_mode(self, username, shift):
        ship_mode = self.ship_mode_var.get()
        if ship_mode == "---Select Mode---" or not ship_mode:
            messagebox.showwarning("Missing Ship Mode", "Please select a shipping mode (SEA or AIR).")
            return

        messagebox.showinfo("Login Successful", f"Welcome, {username} ({shift}) - {ship_mode} Mode")

        # Launch main GUI with logout callback
        self.launch_main_ui(username, shift, ship_mode)

    # ---------------- Launch Main GUI ----------------
    def launch_main_ui(self, username, shift, ship_mode):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Pass logout callback to main GUI
        ZPLPrinterGUI(
            self.root, 
            username, 
            self.serial_num, 
            self.po_num, 
            shift, 
            ship_mode,
            logout_callback=self.handle_logout
        )

    def handle_logout(self):
        """Called when user logs out from main GUI"""
        # Reset variables
        self.username_var.set("")
        self.shift_var.set("")
        self.ship_mode_var.set("")
        
        # Return to login screen
        self.create_login_ui()
        
        # Re-center window for login screen
        self.center_window(400, 300)

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you really want to exit?"):
            self.root.destroy()

# ---------------- Run App ----------------
if __name__ == "__main__":
    root = tk.Tk()
    app = OperatorLogin(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()