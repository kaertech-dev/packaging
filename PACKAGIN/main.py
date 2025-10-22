# PACKAGIN/main.py
import tkinter as tk
from tkinter import ttk
from login_ui import build_login_ui
from label_ui import build_main_ui

# --- App initialization ---
root = tk.Tk()
root.title("🧾 ZPL Label Live Preview Editor")
root.geometry("1100x750")
root.configure(bg="#16213e")

# --- Global Style ---
style = ttk.Style()
style.theme_use("clam")
style.configure("TLabel", font=("Segoe UI", 11), background="#f4f5f7")
style.configure("TButton", font=("Segoe UI", 11, "bold"), padding=6)
style.configure("TEntry", font=("Segoe UI", 11))
style.configure("TLabelframe", background="#f4f5f7", font=("Segoe UI", 12, "bold"))
style.configure("TLabelframe.Label", background="#f4f5f7")

# --- Show login first ---
build_login_ui(root, build_main_ui)
#build_logout_ui(root, build_main_ui)

root.mainloop()
