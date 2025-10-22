# PACKAGINS/main.py
import tkinter as tk
from operator_login import OperatorLogin

if __name__ == "__main__":
    root = tk.Tk()
    app = OperatorLogin(root)
    
    # Set the close protocol BEFORE mainloop
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start the main event loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass  # silently ignore manual stop