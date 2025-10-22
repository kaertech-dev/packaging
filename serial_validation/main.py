# PACKAGING/serial_validation/main.py
from .ui import SerialValidationUI
from .database import validate_serial_number, record_operator_login
from .handlers import handle_success, handle_cancel

class SerialValidation:
    def __init__(self, root, username, on_success_callback):
        self.root = root
        self.username = username
        self.on_success_callback = on_success_callback
        
        # Single database configuration for my_database (contains all tables)
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'my_database'
        }

        # build UI
        self.ui = SerialValidationUI(root, username, self.validate_serial, lambda:handle_cancel(self)) #self.cancel)

    def validate_serial(self):
        serial_num = self.ui.serial_var.get().strip()
        if not serial_num:
            self.ui.set_status("❌ Please enter a serial number!", "red")
            return

        # Ensure a COM port is connected before validating
        if not self.ui.connection:
            self.ui.set_status("⚠️ Please connect to a COM port first!", "orange")
            return

        self.ui.set_status("⏳ Validating serial number and checking process status...", "orange")
        self.root.update()

        result = validate_serial_number(serial_num, self.db_config)
        
        if result["success"]:
            # All processes completed - record operator login
            po_num = result["data"]["po_num"]
            
            login_result = record_operator_login(serial_num, po_num, self.username, self.db_config)
            
            if login_result["success"]:
                # Get lot_code for display (you may need to add this to faceware_main or another table)
                lot_code = result["data"].get("batch_code", "N/A")
                self.ui.set_status(f"✅ Valid! PO: {po_num} | Login recorded", "green")
                self.root.after(800, lambda: handle_success(self, serial_num, po_num))
            else:
                self.ui.set_status(login_result["message"], "red")
        else:
            # Show which processes are incomplete
            self.ui.set_status(result["message"], "red")

    def cancel(self):
        handle_cancel(self)