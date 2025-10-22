from tkinter import ttk
import tkinter as tk
"""
Modern Windows 11-style UI configuration
Add this as PACKAGING/styles.py
"""

# Color Palette - Windows 11 inspired
COLORS = {
    'bg_primary': '#F3F3F3',
    'bg_secondary': '#FFFFFF',
    'bg_tertiary': '#FAFAFA',
    'accent_blue': '#0067C0',
    'accent_blue_hover': '#005A9E',
    'accent_green': '#107C10',
    'accent_green_hover': '#0E6B0E',
    'accent_red': '#D13438',
    'text_primary': '#1F1F1F',
    'text_secondary': '#605E5C',
    'border': '#E1DFDD',
    'shadow': '#00000015',
    'progress_bg': '#E1DFDD',
    'progress_fill': '#0067C0'
}

# Modern button style
def apply_modern_button_style(button, bg_color=None, hover_color=None, text_color='white'):
    """Apply modern flat button styling with hover effects"""
    bg = bg_color or COLORS['accent_blue']
    hover = hover_color or COLORS['accent_blue_hover']
    
    button.configure(
        style='Modern.TButton',
        cursor='hand2'
    )
    
    # Bind hover effects
    def on_enter(e):
        button.configure(style='ModernHover.TButton')
    
    def on_leave(e):
        button.configure(style='Modern.TButton')
    
    button.bind('<Enter>', on_enter)
    button.bind('<Leave>', on_leave)

def configure_modern_theme(root):
    """Configure ttk styles for modern Windows 11 look"""
    style = ttk.Style()
    
    # Main window background
    root.configure(bg=COLORS['bg_primary'])
    
    # Configure TFrame with modern styling
    style.configure('Modern.TFrame',
                   background=COLORS['bg_secondary'],
                   relief='flat')
    
    style.configure('Card.TFrame',
                   background=COLORS['bg_secondary'],
                   relief='flat',
                   borderwidth=0)
    
    # Modern LabelFrame
    style.configure('Modern.TLabelframe',
                   background=COLORS['bg_secondary'],
                   relief='flat',
                   borderwidth=0)
    
    style.configure('Modern.TLabelframe.Label',
                   background=COLORS['bg_secondary'],
                   foreground=COLORS['text_primary'],
                   font=('Segoe UI', 11, 'bold'))
    
    # Modern Labels
    style.configure('Modern.TLabel',
                   background=COLORS['bg_secondary'],
                   foreground=COLORS['text_primary'],
                   font=('Segoe UI', 10))
    
    style.configure('Heading.TLabel',
                   background=COLORS['bg_secondary'],
                   foreground=COLORS['text_primary'],
                   font=('Segoe UI', 14, 'bold'))
    
    style.configure('Status.TLabel',
                   background=COLORS['bg_secondary'],
                   font=('Segoe UI', 10))
    
    # Modern Buttons
    style.configure('Modern.TButton',
                   font=('Segoe UI', 10),
                   relief='flat',
                   borderwidth=0,
                   padding=(20, 10))
    
    style.map('Modern.TButton',
             background=[('active', COLORS['accent_blue_hover']),
                        ('!active', COLORS['accent_blue'])],
             foreground=[('active', 'white'), ('!active', 'white')])
    
    style.configure('ModernHover.TButton',
                   font=('Segoe UI', 10),
                   relief='flat',
                   borderwidth=0,
                   padding=(20, 10))
    
    style.map('ModernHover.TButton',
             background=[('active', COLORS['accent_blue_hover']),
                        ('!active', COLORS['accent_blue_hover'])],
             foreground=[('active', 'white'), ('!active', 'white')])
    
    # Success button variant
    style.configure('Success.TButton',
                   font=('Segoe UI', 10),
                   relief='flat',
                   borderwidth=0,
                   padding=(20, 10))
    
    style.map('Success.TButton',
             background=[('active', COLORS['accent_green_hover']),
                        ('!active', COLORS['accent_green'])],
             foreground=[('active', 'white'), ('!active', 'white')])
    
    # Modern Combobox
    style.configure('Modern.TCombobox',
                   relief='flat',
                   borderwidth=1,
                   padding=8)
    
    # Modern Progressbar
    style.configure('Modern.Horizontal.TProgressbar',
                   troughcolor=COLORS['progress_bg'],
                   background=COLORS['progress_fill'],
                   borderwidth=0,
                   relief='flat',
                   thickness=8)
    
    return style

def create_card_frame(parent, **kwargs):
    """Create a modern card-style frame with shadow effect"""
    # Outer frame for shadow effect
    outer_frame = tk.Frame(parent, bg=COLORS['bg_primary'], **kwargs)
    
    # Inner frame (the actual card)
    inner_frame = tk.Frame(outer_frame, 
                          bg=COLORS['bg_secondary'],
                          relief='flat',
                          borderwidth=0,
                          highlightthickness=1,
                          highlightbackground=COLORS['border'],
                          highlightcolor=COLORS['border'])
    inner_frame.pack(padx=2, pady=2, fill='both', expand=True)
    
    return outer_frame, inner_frame

def style_entry(entry_widget):
    """Apply modern styling to Entry widgets"""
    entry_widget.configure(
        font=('Segoe UI', 11),
        relief='solid',
        borderwidth=1,
        highlightthickness=2,
        highlightcolor=COLORS['accent_blue'],
        highlightbackground=COLORS['border']
    )

def style_text_widget(text_widget):
    """Apply modern styling to Text/ScrolledText widgets"""
    text_widget.configure(
        font=('Segoe UI', 10),
        relief='flat',
        borderwidth=1,
        highlightthickness=1,
        highlightcolor=COLORS['border'],
        highlightbackground=COLORS['border'],
        bg=COLORS['bg_tertiary'],
        fg=COLORS['text_primary'],
        insertbackground=COLORS['accent_blue']
    )