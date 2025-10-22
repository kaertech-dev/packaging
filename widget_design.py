# PACKAGINS/widget_design.py
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

def apply_widget_styles():
    style = ttk.Style()

    # --- Refresh button ---
    style.configure(
        "Refresh.TButton",
        background="#E6F0FF",
        foreground="#004AAD",
        font=("Segoe UI", 9, "bold"),
        padding=6
    )
    style.map(
        "Refresh.TButton",
        background=[("active", "#CCE0FF")],
        foreground=[("active", "#002F7A")]
    )

    # --- Connect button ---
    style.configure(
        "Connect.TButton",
        background="#E8FBE8",
        foreground="#006400",
        font=("Segoe UI", 9, "bold"),
        padding=6
    )
    style.map(
        "Connect.TButton",
        background=[("active", "#BFFFBF")],
        foreground=[("active", "#004D00")]
    )

    # --- Disconnect button ---
    style.configure(
        "Disconnect.TButton",
        background="#FFE5E5",
        foreground="#B22222",
        font=("Segoe UI", 9, "bold"),
        padding=6
    )
    style.map(
        "Disconnect.TButton",
        background=[("active", "#FFCCCC")],
        foreground=[("active", "#8B0000")]
    )
    # Custom style for "Check Database" button
    style.configure(
        "CheckDB.TButton",
        background="#E6F7E6",     # light green background
        foreground="#006400",     # dark green text
        font=("Segoe UI", 9, "bold"),
        padding=(4,2)
    )
    style.map(
        "CheckDB.TButton",
        background=[("active", "#C2EABD")],  # lighter when hovered
        relief=[("pressed", "sunken")]
    )

    # --- Logout Button Style (Compact Red Design) ---
    style.configure(
        "Logout.TButton",
        background="#FFE6E6",     # soft red background
        foreground="#B30000",     # dark red text
        font=("Segoe UI", 9, "bold"),
        padding=(4, 2),           # compact like default
        borderwidth=1,
        relief="solid"
    )
    style.map(
        "Logout.TButton",
        background=[
            ("active", "#FFCCCC"),  # lighter red on hover
            ("pressed", "#FFB3B3")
        ],
        foreground=[
            ("active", "#800000")
        ]
    )

    # --- Refresh Button Style ---
    style.configure(
        "Refresh.TButton",
        background="#E6F0FF",
        foreground="#004AAD",
        font=("Segoe UI", 9, "bold"),
        padding=6
    )
    style.map(
        "Refresh.TButton",
        background=[("active", "#D0E3FF")],
        foreground=[("active", "#002C77")]
    )

    # --- Logout Button Style ---
    style.configure(
        "Logout.TButton",
        background="#FFEBEE",
        foreground="#B71C1C",
        font=("Segoe UI", 9, "bold"),
        padding=(8, 5)
    )
    style.map(
        "Logout.TButton",
        background=[("active", "#FFCDD2")],
        foreground=[("active", "#7F0000")]
    )

    # --- Login Button Style ---
    style.configure(
        "Login.TButton",
        font=("Segoe UI", 11, "bold"),
        foreground="black",
        background="#0078D7",      # blue
        padding=(10, 6),
        relief="flat"
    )
    style.map(
        "Login.TButton",
        background=[
            ("active", "#005A9E"),  # darker blue when hovered
            ("disabled", "#A0A0A0")
        ],
        relief=[("pressed", "groove")]
    )

# green table borde for Operator login header
def create_green_header(parent, text, image_path=None, img_size=(32, 32)):
    """Creates a green-bordered header with image (left) + text (right) side by side."""
    header_frame = tk.Frame(
        parent,
        bg="white",
        highlightbackground="#28a745",  # Green border
        highlightthickness=2,
        bd=0,
        relief="solid"
    )
    header_frame.pack(pady=10, fill="x", padx=20)

    # Inner frame to align image and text horizontally
    inner_frame = tk.Frame(header_frame, bg="white")
    inner_frame.pack(pady=6)

    # Optional image
    if image_path:
        try:
            img = Image.open(image_path)
            img = img.resize(img_size, Image.Resampling.LANCZOS)
            header_image = ImageTk.PhotoImage(img)
            image_label = tk.Label(inner_frame, image=header_image, bg="white")
            image_label.image = header_image  # prevent garbage collection
            image_label.pack(side="left", padx=(8, 10))
        except Exception as e:
            print(f"[Header Image Error] {e}")

    # Header text beside image
    header_label = tk.Label(
        inner_frame,
        text=text,
        bg="white",
        fg="black",
        font=("Segoe UI", 14, "bold")
    )
    header_label.pack(side="left")

    return header_frame

#green table border for welcome {username}
def create_bordered_box(parent, username):
    """Create a compact single-row bordered box with a welcome message."""
    box_frame = tk.Frame(
        parent,
        bg="white",
        highlightbackground="#28a745",  # green border
        highlightthickness=2,
        bd=0,
        relief="solid",
        padx=8,
        pady=1
    )
    box_frame.pack(pady=10, fill="x", padx=30)

    welcome_label = tk.Label(
        box_frame,
        text=f"Welcome {username}",
        bg="white",
        fg="black",
        font=("Segoe UI", 11, "bold")
    )
    welcome_label.pack(anchor="center", padx=10)

    return box_frame
def apply_widget_styles():
    style = ttk.Style()
    style.theme_use("clam")

    # --- Refresh Button ---
    style.configure(
        "Refresh.TButton",
        background="#E6F0FF",
        foreground="#004AAD",
        font=("Segoe UI", 9, "bold"),
        padding=6
    )
    style.map(
        "Refresh.TButton",
        background=[("active", "#CCE0FF")],
        foreground=[("active", "#002F7A")]
    )

    # --- Connect Button ---
    style.configure(
        "Connect.TButton",
        background="#E8FBE8",
        foreground="#006400",
        font=("Segoe UI", 9, "bold"),
        padding=6
    )
    style.map(
        "Connect.TButton",
        background=[("active", "#BFFFBF")],
        foreground=[("active", "#004D00")]
    )

    # --- Disconnect Button ---
    style.configure(
        "Disconnect.TButton",
        background="#FFE5E5",
        foreground="#B22222",
        font=("Segoe UI", 9, "bold"),
        padding=6
    )
    style.map(
        "Disconnect.TButton",
        background=[("active", "#FFCCCC")],
        foreground=[("active", "#8B0000")]
    )

    # --- User Info Label ---
    style.configure(
        "UserInfo.TLabel",
        font=("Segoe UI", 9, "bold"),
        padding=4
    )

def add_tooltip(widget, text):
    tip = tk.Toplevel(widget)
    tip.withdraw()
    tip.overrideredirect(True)
    label = tk.Label(tip, text=text, background="#FFFFE0", relief="solid", borderwidth=1, font=("Segoe UI", 8))
    label.pack()

    def enter(event):
        x, y, _, _ = widget.bbox("insert")
        x += widget.winfo_rootx() + 25
        y += widget.winfo_rooty() + 20
        tip.geometry(f"+{x}+{y}")
        tip.deiconify()

    def leave(event):
        tip.withdraw()

    widget.bind("<Enter>", enter)
    widget.bind("<Leave>", leave)
