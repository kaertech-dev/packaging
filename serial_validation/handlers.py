# PACKAGING/serial_validation/handlers.py
from tkinter import messagebox

def handle_success(validation_instance, serial_num, po_num):
    # Check if connected
    if not validation_instance.ui.connection or not validation_instance.ui.connection.is_open:
        messagebox.showerror("Connection Required", "Please connect first!")
        return
    
    # Pass connection WITHOUT closing it
    validation_instance.on_success_callback(
        validation_instance.root, 
        validation_instance.username, 
        serial_num, 
        po_num,
        validation_instance.ui.connection  # ✅ Pass connection
    )

def handle_cancel(validation_instance):
    """Handle logout/cancel"""
    from login_ui import build_login_ui
    validation_instance.ui.container.destroy()
    build_login_ui(
        validation_instance.root, 
        lambda r, u: validation_instance.__class__(r, u, validation_instance.on_success_callback)
    )