# PACKAGIN/database.py
import mysql.connector
from mysql.connector import Error
import tkinter as tk
from tkinter import messagebox, ttk

class DatabaseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("User Data Entry")
        self.root.geometry("400x300")

        # Database connection parameters
        self.db_config = {
            'host': '127.0.0.1',
            'user': 'root',
            'password': '',  # Update if you set a password
            'database': 'my_database',
            'port': 3306  # Use 3307 if you changed the port
        }

        # GUI elements for main window
        tk.Label(root, text="Name:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.name_entry = tk.Entry(root, width=30)
        self.name_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(root, text="Email:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.email_entry = tk.Entry(root, width=30)
        self.email_entry.grid(row=1, column=1, padx=10, pady=10)

        tk.Button(root, text="Submit", command=self.submit_data).grid(row=2, column=0, columnspan=2, pady=20)
        tk.Button(root, text="Clear", command=self.clear_fields).grid(row=3, column=0, columnspan=2, pady=10)
        tk.Button(root, text="View Data", command=self.view_data).grid(row=4, column=0, columnspan=2, pady=10)

    def submit_data(self):
        name = self.name_entry.get().strip()
        email = self.email_entry.get().strip()

        if not name or not email:
            messagebox.showerror("Error", "Please fill in all fields.")
            return
        if "@" not in email or "." not in email:
            messagebox.showerror("Error", "Invalid email format.")
            return

        try:
            connection = mysql.connector.connect(**self.db_config)
            if connection.is_connected():
                cursor = connection.cursor()
                # Check for duplicate email
                cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    messagebox.showerror("Error", "Email already exists!")
                    cursor.close()
                    connection.close()
                    return

                insert_query = "INSERT INTO users (name, email) VALUES (%s, %s)"
                cursor.execute(insert_query, (name, email))
                connection.commit()
                messagebox.showinfo("Success", f"Record inserted: {name}, {email}")
                self.clear_fields()
        except Error as e:
            messagebox.showerror("Database Error", f"Error: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def clear_fields(self):
        self.name_entry.delete(0, tk.END)
        self.email_entry.delete(0, tk.END)

    def view_data(self):
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()

            # Create new window for data display
            view_window = tk.Toplevel(self.root)
            view_window.title("User Data")
            view_window.geometry("500x400")

            # Listbox to display data
            listbox = tk.Listbox(view_window, width=50, height=10)
            listbox.pack(padx=10, pady=10)

            # Store records for deletion
            self.records = []
            for row in rows:
                record = f"ID: {row[0]}, Name: {row[1]}, Email: {row[2]}"
                listbox.insert(tk.END, record)
                self.records.append((row[0], row[1], row[2]))

            # Delete button
            tk.Button(view_window, text="Delete Selected", command=lambda: self.delete_data(listbox, view_window)).pack(pady=10)

            cursor.close()
            connection.close()
        except Error as e:
            messagebox.showerror("Database Error", f"Error: {e}")

    def delete_data(self, listbox, view_window):
        connection = None  # Initialize connection to None
        cursor = None      # Initialize cursor to None
        try:
            # Get selected item index
            selection = listbox.curselection()
            if not selection:
                messagebox.showerror("Error", "Please select a record to delete.")
                return

            # Get ID of selected record
            index = selection[0]
            record_id = self.records[index][0]

            # Connect to database and delete
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()
            cursor.execute("DELETE FROM users WHERE id = %s", (record_id,))
            connection.commit()

            # Update Listbox
            listbox.delete(index)
            self.records.pop(index)
            messagebox.showinfo("Success", "Record deleted successfully!")
        except Error as e:
            messagebox.showerror("Database Error", f"Error: {e}")
        finally:
            # Check if connection and cursor exist and are valid
            if cursor is not None:
                cursor.close()
            if connection is not None and connection.is_connected():
                connection.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = DatabaseApp(root)
    root.mainloop()