import tkinter as tk
from tkinter import ttk, messagebox
import requests
from PIL import Image, ImageTk
from io import BytesIO
from zpl_code import zpl_code
import re

ZEBRA_API = "https://api.labelary.com/v1/printers/24dpmm/labels/4x6/0/"

# ------------------- ZPL PREVIEW LOGIC -------------------
def generate_zpl(sku, barcode, quantity, lot):
    """Return ZPL code string with inserted values"""
    return zpl_code.format(sku=sku, barcode=barcode, quantity=quantity, lot=lot)

def render_preview(*args):
    """Fetch ZPL preview from Labelary and show it"""
    sku = sku_entry.get().strip()
    barcode = barcode_entry.get().strip()
    qty = qty_entry.get().strip()
    lot = lot_entry.get().strip()
    status_var.set("Generating preview...")

    zpl = generate_zpl(sku, barcode, qty, lot)
    try:
        response = requests.post(ZEBRA_API, data=zpl.encode("utf-8"), headers={"Accept": "image/png"})
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        image = image.resize((480, 640))
        img_tk = ImageTk.PhotoImage(image)
        preview_label.config(image=img_tk, text="")
        preview_label.image = img_tk
        status_var.set("✅ Preview updated successfully")
    except Exception as e:
        preview_label.config(text="Error loading preview", image="")
        status_var.set(f"❌ Error: {e}")

# ------------------- LOGIN FUNCTIONALITY -------------------
def check_login():
    username = username_entry.get().strip()
    #password = password_entry.get().strip()

    # Allow only usernames like KE0001, KE0412, etc.
    if re.match(r"^KE\d{4}$", username):
        messagebox.showinfo("Login Successful", f"Welcome, {username}!")
        login_frame.pack_forget()
        build_main_ui()
    else:
        messagebox.showerror("Login Failed", "❌ Invalid ID format.\nUse format like KE0001 or KE0412.")

# ------------------- MAIN APP WINDOW -------------------
root = tk.Tk()
root.title("🧾 ZPL Label Live Preview Editor")
root.geometry("1100x750")
root.configure(bg="#16213e")

style = ttk.Style()
style.theme_use("clam")

style.configure("TLabel", font=("Segoe UI", 11), background="#f4f5f7")
style.configure("TButton", font=("Segoe UI", 11, "bold"), padding=6)
style.configure("TEntry", font=("Segoe UI", 11))
style.configure("TLabelframe", background="#f4f5f7", font=("Segoe UI", 12, "bold"))
style.configure("TLabelframe.Label", background="#f4f5f7")

# ------------------- LOGIN FRAME -------------------
login_frame = ttk.Frame(root, padding=40)
login_frame.place(relx=0.5, rely=0.5, anchor="center")

ttk.Label(login_frame, text="🔒 Login to ZPL Editor", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=20)

ttk.Label(login_frame, text="ID:").grid(row=1, column=0, sticky="e", pady=10)
username_entry = ttk.Entry(login_frame, width=30)
username_entry.grid(row=1, column=1, pady=10)

#ttk.Label(login_frame, text="Password:").grid(row=2, column=0, sticky="e", pady=10)
#password_entry = ttk.Entry(login_frame, width=30, show="*")
#password_entry.grid(row=2, column=1, pady=10)

login_btn = ttk.Button(login_frame, text="Login", command=check_login)
login_btn.grid(row=3, column=0, columnspan=2, pady=20)

# ------------------- MAIN UI BUILDER -------------------
def build_main_ui():
    global sku_entry, barcode_entry, qty_entry, lot_entry, preview_label, status_var

    # --- Left input panel ---
    frame = ttk.LabelFrame(root, text=" Label Information ", padding=20)
    frame.pack(side="left", fill="y", padx=25, pady=20)

    fields = [
        ("SKU LABEL:", "43000166102"),
        ("BARCODE:", "4341C4300016611002"),
        ("Quantity (pcs):", "2"),
        ("LOT CODE:", "4341C")
    ]

    entries = {}
    for i, (label_text, default) in enumerate(fields):
        ttk.Label(frame, text=label_text).grid(row=i, column=0, sticky="w", pady=10)
        entry = ttk.Entry(frame, width=35)
        entry.insert(0, default)
        entry.grid(row=i, column=1, pady=10, padx=10)
        entries[label_text] = entry

    sku_entry = entries["SKU LABEL:"]
    barcode_entry = entries["BARCODE:"]
    qty_entry = entries["Quantity (pcs):"]
    lot_entry = entries["LOT CODE:"]

    # Live preview updates on typing
    for entry in [sku_entry, barcode_entry, qty_entry, lot_entry]:
        entry.bind("<KeyRelease>", render_preview)

    # Manual refresh button
    refresh_btn = ttk.Button(frame, text="🔄 Refresh Preview", command=render_preview)
    refresh_btn.grid(row=len(fields), column=0, columnspan=2, pady=20)

    # --- Right preview area ---
    preview_frame = ttk.Frame(root, padding=10)
    preview_frame.pack(side="right", expand=True, fill="both", padx=25, pady=20)

    preview_label = ttk.Label(
        preview_frame,
        text="🖼️ Preview will appear here",
        anchor="center",
        background="#ffffff",
        relief="solid",
        borderwidth=2,
        width=50,
        padding=10
    )
    preview_label.pack(expand=True, fill="both")

    # --- Status bar ---
    status_var = tk.StringVar(value="Ready.")
    status_bar = ttk.Label(root, textvariable=status_var, anchor="w", relief="sunken", padding=5)
    status_bar.pack(side="bottom", fill="x")

    # Initial preview
    render_preview()

root.mainloop()
