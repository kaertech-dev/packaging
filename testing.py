import tkinter as tk
from tkinter import messagebox, ttk
import re
import mysql.connector

class OperatorLoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Operator Login")
        self.root.geometry("450x350")
        self.root.resizable(False, False)

        self.login_frame = tk.Frame(root)
        self.scan_frame = tk.Frame(root)

        # 🔹 Keep track of scanned serial numbers to prevent duplicates
        self.scanned_serials = set()

        self.build_login_ui()

    def build_login_ui(self):
        """Builds the operator login interface."""
        self.clear_frame()
        self.login_frame.pack(pady=40)

        tk.Label(self.login_frame, text="Operator Login", font=("Arial", 16, "bold")).pack(pady=10)
        tk.Label(self.login_frame, text="Enter Operator ID (e.g., KE0412 or LL0412):").pack()

        self.operator_id_entry = ttk.Entry(self.login_frame, width=20, font=("Arial", 12))
        self.operator_id_entry.pack(pady=5)
        self.operator_id_entry.focus()

        # 🔹 Shift selection dropdown
        tk.Label(self.login_frame, text="Select Shift:").pack(pady=5)
        self.shift_var = tk.StringVar()
        self.shift_combo = ttk.Combobox(self.login_frame, textvariable=self.shift_var, state="readonly", width=10, font=("Arial", 12))
        self.shift_combo["values"] = ("A", "B")
        self.shift_combo.pack()

        login_btn = ttk.Button(self.login_frame, text="Login", command=self.validate_login)
        login_btn.pack(pady=15)

        # 🔹 Press Enter to login
        self.operator_id_entry.bind("<Return>", lambda event: self.validate_login())
        self.shift_combo.bind("<Return>", lambda event: self.validate_login())

    def validate_login(self):
        """Validates operator ID and shift."""
        operator_id = self.operator_id_entry.get().strip().upper()
        shift = self.shift_var.get()
        pattern = r'^(KE|LL)\d{4}$'

        if not re.match(pattern, operator_id):
            messagebox.showerror("Invalid ID", "Please enter a valid ID (KE0000 or LL0000 format).")
            return

        if not shift:
            messagebox.showerror("Missing Shift", "Please select your shift (A or B).")
            return

        messagebox.showinfo("Login Successful", f"Welcome, {operator_id} (Shift {shift})!")
        self.build_scan_ui(operator_id, shift)

    def build_scan_ui(self, operator_id, shift):
        """Builds the barcode scanning interface."""
        self.clear_frame()
        self.scan_frame.pack(pady=20, fill="both", expand=True)

        # 🔹 Reset scanned serials for each login session
        self.scanned_serials.clear()

        tk.Label(self.scan_frame, text=f"Logged in as: {operator_id} (Shift {shift})", font=("Arial", 12, "bold")).pack(pady=5)
        tk.Label(self.scan_frame, text="Scan Serial Number:", font=("Arial", 14, "bold")).pack(pady=10)

        self.barcode_entry = ttk.Entry(self.scan_frame, width=25, font=("Arial", 12))
        self.barcode_entry.pack(pady=5)
        self.barcode_entry.focus()

        ttk.Button(self.scan_frame, text="Check Database", command=self.check_serial_in_db).pack(pady=5)

        self.result_list = tk.Listbox(self.scan_frame, width=50, height=8, font=("Arial", 11))
        self.result_list.pack(pady=10)

        ttk.Button(self.scan_frame, text="Logout", command=self.build_login_ui).pack(pady=5)

        # 🔹 Press Enter to check database
        self.barcode_entry.bind("<Return>", lambda event: self.check_serial_in_db())

    def check_serial_in_db(self):
        """Checks if scanned serial number exists in the database."""
        serial_num = self.barcode_entry.get().strip()

        if not serial_num:
            messagebox.showwarning("Empty", "Please scan or enter a serial number.")
            return

        # 🔹 Check for duplicate scans within this session
        if serial_num in self.scanned_serials:
            messagebox.showwarning("Duplicate Entry", f"Serial number '{serial_num}' already scanned.")
            self.barcode_entry.delete(0, tk.END)
            self.barcode_entry.focus()
            return

        try:
            # 🔹 Connect to MySQL
            db = mysql.connector.connect(
                host='localhost',
                user='root',
                password='',
                database='my_database'   # Change if needed
            )
            cursor = db.cursor()

            # 🔹 Query to check serial number
            query = "SELECT batch_code FROM faceware_assembly1 WHERE serial_num = %s"
            cursor.execute(query, (serial_num,))
            result = cursor.fetchone()

            if result:
                batch_code = result[0]
                self.result_list.insert(tk.END, f"Serial: {serial_num} → Batch Code: {batch_code}")
                # Add to scanned serials to prevent duplicates
                self.scanned_serials.add(serial_num)
            else:
                messagebox.showerror("Not Found", f"Serial number '{serial_num}' not found in database.")

            cursor.close()
            db.close()

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")

        # Clear input for next scan
        self.barcode_entry.delete(0, tk.END)
        self.barcode_entry.focus()

    def clear_frame(self):
        """Clears all frames."""
        for widget in self.root.winfo_children():
            widget.pack_forget()


# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = OperatorLoginApp(root)
    root.mainloop()
