# PACKAGING/zpl_preview.py
import requests
from PIL import Image, ImageTk
from io import BytesIO
from zpl_codes import zpl_code

ZEBRA_API = "https://api.labelary.com/v1/printers/24dpmm/labels/4x6/0/"

def generate_zpl(sku, barcode, quantity, lot):
    """Return ZPL code string with inserted values"""
    return zpl_code.format(sku=sku, barcode=barcode, quantity=quantity, lot=lot)

def render_preview(sku_entry, barcode_entry, qty_entry, lot_entry, preview_label, status_var):
    """Fetch ZPL preview from Labelary and display"""
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
