# PACKAGINS/printer_handler.py
import serial
import serial.tools.list_ports
import atexit

class PrinterHandler:
    def __init__(self):
        self.inner_printer = None
        self.outer_printer = None
        # Automatically close ports on program exit
        atexit.register(self.safe_cleanup)

    def list_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect_inner(self, port, baud):
        """Connect to inner box label printer"""
        # Close any existing inner printer connection
        if self.inner_printer and self.inner_printer.is_open:
            try:
                self.inner_printer.close()
            except Exception as e:
                print(f"[WARNING] Failed to close inner printer: {e}")

        try:
            self.inner_printer = serial.Serial(port, baudrate=baud, timeout=1)
            print(f"[INFO] Inner printer connected to {port}")
            return True
        except serial.SerialException as e:
            print(f"[ERROR] Could not connect inner printer to {port}: {e}")
            return False

    def connect_outer(self, port, baud):
        """Connect to outer box label printer"""
        # Close any existing outer printer connection
        if self.outer_printer and self.outer_printer.is_open:
            try:
                self.outer_printer.close()
            except Exception as e:
                print(f"[WARNING] Failed to close outer printer: {e}")

        try:
            self.outer_printer = serial.Serial(port, baudrate=baud, timeout=1)
            print(f"[INFO] Outer printer connected to {port}")
            return True
        except serial.SerialException as e:
            print(f"[ERROR] Could not connect outer printer to {port}: {e}")
            return False

    def disconnect_inner(self):
        """Manually close the inner printer port if open."""
        if self.inner_printer and self.inner_printer.is_open:
            try:
                self.inner_printer.close()
                print("[INFO] Inner printer port closed safely.")
            except Exception as e:
                print(f"[WARNING] Failed to close inner printer port: {e}")
            finally:
                self.inner_printer = None

    def disconnect_outer(self):
        """Manually close the outer printer port if open."""
        if self.outer_printer and self.outer_printer.is_open:
            try:
                self.outer_printer.close()
                print("[INFO] Outer printer port closed safely.")
            except Exception as e:
                print(f"[WARNING] Failed to close outer printer port: {e}")
            finally:
                self.outer_printer = None

    def disconnect_all(self):
        """Disconnect both printers"""
        self.disconnect_inner()
        self.disconnect_outer()

    def safe_cleanup(self):
        """Ensure all ports are closed before exiting."""
        if self.inner_printer:
            if self.inner_printer.is_open:
                try:
                    self.inner_printer.close()
                    print("[CLEANUP] Inner printer port safely released.")
                except Exception as e:
                    print(f"[CLEANUP WARNING] Error closing inner printer port: {e}")
            self.inner_printer = None
        
        if self.outer_printer:
            if self.outer_printer.is_open:
                try:
                    self.outer_printer.close()
                    print("[CLEANUP] Outer printer port safely released.")
                except Exception as e:
                    print(f"[CLEANUP WARNING] Error closing outer printer port: {e}")
            self.outer_printer = None

    def is_inner_connected(self):
        return self.inner_printer and self.inner_printer.is_open

    def is_outer_connected(self):
        return self.outer_printer and self.outer_printer.is_open

    def is_all_connected(self):
        """Check if both printers are connected"""
        return self.is_inner_connected() and self.is_outer_connected()

    def send_to_inner_printer(self, zpl_data):
        """Send ZPL data to inner box printer"""
        if self.is_inner_connected():
            try:
                self.inner_printer.write(zpl_data.encode("utf-8"))
                print("[INFO] Data sent to inner printer.")
                return True
            except serial.SerialException as e:
                print(f"[ERROR] Failed to send data to inner printer: {e}")
                self.disconnect_inner()
                return False
        else:
            print("[WARNING] Inner printer not connected.")
            return False

    def send_to_outer_printer(self, zpl_data):
        """Send ZPL data to outer box printer"""
        if self.is_outer_connected():
            try:
                self.outer_printer.write(zpl_data.encode("utf-8"))
                print("[INFO] Data sent to outer printer.")
                return True
            except serial.SerialException as e:
                print(f"[ERROR] Failed to send data to outer printer: {e}")
                self.disconnect_outer()
                return False
        else:
            print("[WARNING] Outer printer not connected.")
            return False