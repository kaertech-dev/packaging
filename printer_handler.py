import serial
import serial.tools.list_ports
import atexit

class PrinterHandler:
    def __init__(self):
        self.ser = None
        # Automatically close port on program exit
        atexit.register(self.safe_cleanup)

    def list_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect(self, port, baud):
        # Before connecting, ensure any old connection is closed
        self.safe_cleanup()

        try:
            self.ser = serial.Serial(port, baudrate=baud, timeout=1)
            return True
        except serial.SerialException as e:
            print(f"[ERROR] Could not connect to {port}: {e}")
            return False

    def disconnect(self):
        """Manually close the port if open."""
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
                print("[INFO] Serial port closed safely.")
            except Exception as e:
                print(f"[WARNING] Failed to close serial port: {e}")
            finally:
                self.ser = None

    def safe_cleanup(self):
        """Ensure the port is closed before reconnecting or exiting."""
        if self.ser:
            if self.ser.is_open:
                try:
                    self.ser.close()
                    print("[CLEANUP] Serial port safely released.")
                except Exception as e:
                    print(f"[CLEANUP WARNING] Error closing port: {e}")
            self.ser = None

    def is_connected(self):
        return self.ser and self.ser.is_open

    def send_to_printer(self, zpl_data):
        if self.is_connected():
            try:
                self.ser.write(zpl_data.encode("utf-8"))
                print("[INFO] Data sent to printer.")
            except serial.SerialException as e:
                print(f"[ERROR] Failed to send data: {e}")
                self.safe_cleanup()
        else:
            print("[WARNING] No printer connected.")
