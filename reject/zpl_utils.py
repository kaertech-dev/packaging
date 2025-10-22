# PACKAGIN/zpl_utils.py
import os
import re
from tkinter import messagebox

# Import functions from other modules
from printer_utils import detect_printer_dpi

def read_prn_as_zpl(file_path):
    """Read PRN file and try to extract or convert ZPL text."""
    print(f"[DEBUG] Attempting to read: {file_path}")
    
    if not os.path.exists(file_path):
        messagebox.showerror("File Error", f"File not found:\n{file_path}")
        print(f"[ERROR] File not found: {file_path}")
        return None

    try:
        # Try reading as binary first
        with open(file_path, 'rb') as f:
            content = f.read()
        
        print(f"[DEBUG] File size: {len(content)} bytes")

        # Try UTF-8 decoding
        try:
            text = content.decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"[DEBUG] UTF-8 decode failed: {e}, trying latin-1")
            text = content.decode('latin-1', errors='ignore')

        # Check if it contains ZPL commands
        if '^XA' in text or '^XZ' in text:
            print("[SUCCESS] ZPL format detected in PRN file.")
            
            # Clean up any control characters but keep ZPL structure
            cleaned = text.replace('\x00', '').replace('\r', '')
            
            # Show first 200 chars for debugging
            print(f"[DEBUG] First 200 chars: {cleaned[:200]}")
            
            return cleaned

        # Try to extract printable ASCII that might contain ZPL
        possible_zpl = ''.join(
            ch if 32 <= ord(ch) <= 126 or ch in '\n\r\t' else ''
            for ch in text
        )

        if '^XA' in possible_zpl:
            print("[SUCCESS] Cleaned ZPL extracted from PRN file.")
            return possible_zpl

        # If no ZPL found, show warning
        print("[WARNING] No ZPL commands found in file")
        messagebox.showwarning(
            "Unsupported PRN",
            "The selected .PRN file doesn't appear to contain ZPL commands.\n"
            "Expected commands: ^XA, ^XZ, ^FO, etc.\n\n"
            f"First 100 chars: {text[:100]}"
        )
        return None
        
    except Exception as e:
        print(f"[ERROR] Exception reading file: {e}")
        messagebox.showerror("Read Error", f"Error reading PRN file:\n{e}")
        return None

def extract_label_size(zpl_text):
    """Detect label dimensions (^PW or ^LL). Fallback 4x6 inches, clamp ≤15."""
    width, height = 4, 6
    pw_match = re.search(r"\^PW(\d+)", zpl_text)
    ll_match = re.search(r"\^LL(\d+)", zpl_text)

    dpi = detect_printer_dpi()
    if pw_match:
        width = round(int(pw_match.group(1)) / dpi, 2)
    if ll_match:
        height = round(int(ll_match.group(1)) / dpi, 2)

    width = max(0.5, min(width, 15.0))
    height = max(0.5, min(height, 15.0))
    
    print(f"[DEBUG] Detected label size: {width}x{height} inches (DPI: {dpi})")
    return width, height