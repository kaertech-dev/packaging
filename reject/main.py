# PACKAGIN/main_with_overlay.py
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

# Import functions from other modules
from zpl_utils import read_prn_as_zpl
from printer_utils import send_zpl_to_printer
from preview_utils import preview_zpl
from config import DEFAULT_PRN_PATH

def main():
    root = tk.Tk()
    root.title("ZPL Label Editor with Text Overlay")
    root.geometry("1100x950")

    # Variables
    current_prn_path = tk.StringVar(value="No file loaded")
    darkness_var = tk.IntVar(value=10)
    speed_var = tk.IntVar(value=2)
    
    # Overlay variables
    overlay_x = tk.IntVar(value=300)
    overlay_y = tk.IntVar(value=500)
    overlay_text = tk.StringVar(value="")
    overlay_size = tk.IntVar(value=40)

    def load_prn_file():
        """Load PRN file and display path"""
        path = filedialog.askopenfilename(
            filetypes=[("PRN files", "*.prn"), ("All files", "*.*")],
            title="Select PRN File"
        )
        if path:
            current_prn_path.set(path)
            convert_btn.config(state='normal')
            status_label.config(text="PRN file loaded. Click 'Convert to ZPL' to edit.", fg="blue")

    def convert_to_zpl():
        """Convert loaded PRN to ZPL and populate editor"""
        path = current_prn_path.get()
        if path == "No file loaded":
            messagebox.showwarning("No File", "Please load a PRN file first.")
            return
        
        zpl = read_prn_as_zpl(path)
        if zpl:
            text_area.delete(1.0, tk.END)
            text_area.insert(tk.END, zpl)
            status_label.config(text="ZPL loaded. Use Overlay Tool to add text, or edit code directly.", fg="green")
            preview_btn.config(state='normal')
            print_btn.config(state='normal')
            overlay_frame.config(state='normal')

    def add_text_overlay():
        """Add text overlay to current ZPL"""
        text = overlay_text.get().strip()
        if not text:
            messagebox.showwarning("Empty Text", "Please enter text for the overlay.")
            return
        
        current_zpl = text_area.get(1.0, tk.END).strip()
        if not current_zpl:
            messagebox.showwarning("No ZPL", "Load a label first.")
            return
        
        # Find last ^XZ
        parts = current_zpl.rsplit('^XZ', 1)
        if len(parts) != 2:
            messagebox.showerror("Invalid ZPL", "Could not find ^XZ in the ZPL code.")
            return
        
        # Build overlay command
        x = overlay_x.get()
        y = overlay_y.get()
        size = overlay_size.get()
        
        overlay_cmd = f"^FO{x},{y}^A0N,{size},{size}^FD{text}^FS"
        
        # Insert before ^XZ
        modified_zpl = parts[0] + '\n' + overlay_cmd + '\n^XZ' + parts[1]
        
        # Update editor
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, modified_zpl)
        
        status_label.config(text=f"Text overlay added at ({x}, {y})", fg="green")
        messagebox.showinfo("Success", f"Text overlay added!\nPosition: ({x}, {y})\nPreview to see results.")

    def print_label():
        """Print the ZPL from editor"""
        zpl_body = text_area.get(1.0, tk.END).strip()
        if not zpl_body:
            messagebox.showwarning("Empty Label", "ZPL content is empty.")
            return
        zpl = f"^XA\n^MD{darkness_var.get()}\n^PR{speed_var.get()}\n{zpl_body}\n^XZ"
        send_zpl_to_printer(zpl)

    def preview():
        """Preview the ZPL from editor"""
        zpl_body = text_area.get(1.0, tk.END).strip()
        if not zpl_body:
            messagebox.showwarning("Empty Label", "ZPL content is empty.")
            return
        preview_zpl(zpl_body, preview_canvas, darkness_var.get(), speed_var.get())

    def clear_editor():
        """Clear the ZPL editor"""
        if messagebox.askyesno("Clear Editor", "Are you sure you want to clear the editor?"):
            text_area.delete(1.0, tk.END)
            status_label.config(text="Editor cleared.", fg="black")

    # Main container
    main_container = tk.Frame(root, padx=10, pady=10)
    main_container.pack(fill='both', expand=True)

    # === PRN CONVERTER FRAME ===
    converter_frame = tk.LabelFrame(main_container, text="Step 1: Load & Convert PRN", padx=10, pady=10)
    converter_frame.pack(fill='x', pady=(0, 10))

    file_row = tk.Frame(converter_frame)
    file_row.pack(fill='x', pady=5)
    
    tk.Button(file_row, text="Load PRN", command=load_prn_file, width=12).pack(side='left', padx=(0, 10))
    tk.Label(file_row, textvariable=current_prn_path, anchor='w', relief='sunken', bg='white').pack(side='left', fill='x', expand=True)

    convert_row = tk.Frame(converter_frame)
    convert_row.pack(fill='x', pady=5)
    
    convert_btn = tk.Button(convert_row, text="Convert to ZPL", command=convert_to_zpl, 
                           width=12, state='disabled', bg='#4CAF50', fg='white')
    convert_btn.pack(side='left', padx=(0, 10))
    
    status_label = tk.Label(convert_row, text="Load a PRN file to begin.", anchor='w', fg="gray")
    status_label.pack(side='left', fill='x')

    # === TEXT OVERLAY TOOL ===
    overlay_frame = tk.LabelFrame(main_container, text="Step 2: Add Text Overlay (Optional)", padx=10, pady=10)
    overlay_frame.pack(fill='x', pady=(0, 10))

    info_label = tk.Label(overlay_frame, 
                         text="💡 Graphics are encoded. Use this tool to add text on top of existing label.",
                         fg="blue", font=("Arial", 9, "italic"))
    info_label.pack(anchor='w', pady=(0, 5))

    overlay_controls = tk.Frame(overlay_frame)
    overlay_controls.pack(fill='x')

    tk.Label(overlay_controls, text="X:").grid(row=0, column=0, padx=5)
    tk.Entry(overlay_controls, textvariable=overlay_x, width=8).grid(row=0, column=1, padx=5)
    
    tk.Label(overlay_controls, text="Y:").grid(row=0, column=2, padx=5)
    tk.Entry(overlay_controls, textvariable=overlay_y, width=8).grid(row=0, column=3, padx=5)
    
    tk.Label(overlay_controls, text="Size:").grid(row=0, column=4, padx=5)
    tk.Entry(overlay_controls, textvariable=overlay_size, width=8).grid(row=0, column=5, padx=5)
    
    tk.Label(overlay_controls, text="Text:").grid(row=1, column=0, padx=5, pady=5)
    tk.Entry(overlay_controls, textvariable=overlay_text, width=40).grid(row=1, column=1, columnspan=4, padx=5, pady=5, sticky='ew')
    
    tk.Button(overlay_controls, text="Add Text Overlay", command=add_text_overlay, 
             bg='#2196F3', fg='white', width=15).grid(row=1, column=5, padx=5, pady=5)

    # === ZPL EDITOR ===
    editor_frame = tk.LabelFrame(main_container, text="Step 3: Review/Edit ZPL Code", padx=10, pady=10)
    editor_frame.pack(fill='both', expand=True, pady=(0, 10))

    editor_toolbar = tk.Frame(editor_frame)
    editor_toolbar.pack(fill='x', pady=(0, 5))
    
    tk.Button(editor_toolbar, text="Clear", command=clear_editor, width=10).pack(side='left', padx=(0, 5))
    tk.Label(editor_toolbar, text="⚠️ Graphics (^GFA) are encoded - text overlays recommended", 
            fg="orange", font=("Arial", 8)).pack(side='left')

    text_area = scrolledtext.ScrolledText(editor_frame, wrap=tk.WORD, font=("Courier", 9), height=12)
    text_area.pack(fill='both', expand=True)

    # === PRINTER SETTINGS ===
    settings_frame = tk.LabelFrame(main_container, text="Printer Settings", padx=10, pady=10)
    settings_frame.pack(fill='x', pady=(0, 10))

    settings_row = tk.Frame(settings_frame)
    settings_row.pack()
    
    tk.Label(settings_row, text="Darkness:").grid(row=0, column=0, padx=5)
    tk.Entry(settings_row, textvariable=darkness_var, width=8).grid(row=0, column=1, padx=5)
    
    tk.Label(settings_row, text="Speed:").grid(row=0, column=2, padx=5)
    tk.Entry(settings_row, textvariable=speed_var, width=8).grid(row=0, column=3, padx=5)

    # === ACTION BUTTONS ===
    action_frame = tk.Frame(main_container)
    action_frame.pack(fill='x', pady=(0, 10))

    preview_btn = tk.Button(action_frame, text="Preview Label", command=preview, 
                           width=20, state='disabled', bg='#2196F3', fg='white', font=('Arial', 10, 'bold'))
    preview_btn.pack(side='left', padx=5, expand=True, fill='x')

    print_btn = tk.Button(action_frame, text="Send to Printer", command=print_label, 
                         width=20, state='disabled', bg='#FF9800', fg='white', font=('Arial', 10, 'bold'))
    print_btn.pack(side='left', padx=5, expand=True, fill='x')

    # === PREVIEW CANVAS ===
    preview_frame = tk.LabelFrame(main_container, text="Step 4: Preview", padx=10, pady=10)
    preview_frame.pack(fill='both', expand=True)

    preview_canvas = tk.Canvas(preview_frame, bg="white", highlightthickness=1, highlightbackground="gray")
    preview_canvas.pack(fill='both', expand=True)

    # Load default file
    default_zpl = read_prn_as_zpl(DEFAULT_PRN_PATH)
    if default_zpl:
        text_area.insert(tk.END, default_zpl)
        current_prn_path.set(DEFAULT_PRN_PATH)
        status_label.config(text="Default PRN loaded. Use overlay tool or edit directly.", fg="green")
        preview_btn.config(state='normal')
        print_btn.config(state='normal')

    root.mainloop()

if __name__ == "__main__":
    main()