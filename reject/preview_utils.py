#PACKAGIN/preview_utils.py
import requests
from io import BytesIO
from PIL import Image, ImageTk
from tkinter import messagebox, CENTER

# Import functions from other modules
from zpl_utils import extract_label_size
from printer_utils import detect_printer_dpi

def preview_zpl(zpl, canvas, darkness, speed):
    """Generate ZPL preview using Labelary API."""
    zpl = f"^XA\n^MD{darkness}\n^PR{speed}\n{zpl}\n^XZ"
    width_in, height_in = extract_label_size(zpl)

    try:
        dpmm = round(detect_printer_dpi() / 25.4)
        url = f"http://api.labelary.com/v1/printers/{dpmm}dpmm/labels/{width_in}x{height_in}/0/"
        response = requests.post(url, headers={'Accept': 'image/png'}, data=zpl.encode('utf-8'))

        if response.status_code != 200:
            messagebox.showerror(
                "Preview Error",
                f"Labelary returned {response.status_code}\nWidth={width_in} in, Height={height_in} in\n{response.text}"
            )
            return None

        img_data = BytesIO(response.content)
        img = Image.open(img_data)
        canvas_w, canvas_h = canvas.winfo_width(), canvas.winfo_height()
        img.thumbnail((canvas_w, canvas_h), Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)

        canvas.delete("all")
        canvas.create_image(canvas_w // 2, canvas_h // 2, anchor=CENTER, image=img_tk)
        canvas.image = img_tk  # Prevent GC

    except Exception as e:
        messagebox.showerror("Preview Error", f"Error generating preview:\n{e}")
