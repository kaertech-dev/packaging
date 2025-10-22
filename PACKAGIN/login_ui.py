# PACKAGING/login_ui.py
import re
from tkinter import ttk, messagebox, Frame
#from serial_validation import show_serial_validation
from serial_validation.main import SerialValidation

def build_login_ui(root, on_success):
    """Enhanced login UI with modern design and validation"""
    # Root background
    root.configure(bg="#16213e")

    # --- Main container frame ---
    container = Frame(root, bg="#16213e")
    container.place(relx=0.5, rely=0.5, anchor="center")

    # --- Card frame (white box with padding) ---
    card = Frame(container, bg="#f4f5f7", bd=0, relief="flat")
    card.grid(row=0, column=0, padx=20, pady=20, ipadx=30, ipady=20)

    # --- Title ---
    ttk.Label(
        card,
        text="🔒 Login KE NO.",
        font=("Segoe UI", 18, "bold"),
        background="#f4f5f7",
        foreground="#16213e"
    ).grid(row=0, column=0, columnspan=2, pady=(10, 25))

    # --- ID Label ---
    ttk.Label(
        card,
        text="User ID:",
        font=("Segoe UI", 11, "bold"),
        background="#f4f5f7"
    ).grid(row=1, column=0, sticky="e", padx=(10, 5), pady=10)

    # --- ID Entry ---
    username_entry = ttk.Entry(card, width=28, font=("Segoe UI", 11))
    username_entry.grid(row=1, column=1, pady=10, padx=(0, 10))
    username_entry.focus()

    # --- Login button ---
    login_btn = ttk.Button(
        card,
        text="Login",
        command=lambda: check_login(),
        style="Login.TButton"
    )
    login_btn.grid(row=3, column=0, columnspan=2, pady=(20, 10), ipadx=10)

    # --- Style customization ---
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Login.TButton",
        font=("Segoe UI", 11, "bold"),
        foreground="white",
        background="#0f3460",
        padding=8
    )
    style.map(
        "Login.TButton",
        background=[("active", "#1a508b")],
        relief=[("pressed", "sunken")]
    )

    style.configure("TEntry", padding=5)

    # --- Validation logic ---
    def check_login():
        username = username_entry.get().strip()

        if not username:
            messagebox.showerror("Login Failed", "❌ ID cannot be empty.")
        elif re.match(r"^KE\d{4}$", username) or re.match(r"^LL\d{4}$", username):
            messagebox.showinfo("Login Successful", f"Welcome, {username}!")
            container.destroy()
            root.unbind("<Return>")
            # Show serial validation instead of directly calling on_success
            SerialValidation(root, username, on_success)
        else:
            messagebox.showerror(
                "Login Failed",
                "❌ Invalid ID format.\nUse KE0001, KE0412, or LL0001."
            )

    # Allow pressing Enter to trigger login
    root.bind("<Return>", lambda e: check_login())