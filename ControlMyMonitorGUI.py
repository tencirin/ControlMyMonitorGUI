import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os

# --- Configuration ---
# IMPORTANT: Set the path to the ControlMyMonitor.exe file
CMM_PATH = "ControlMyMonitor.exe" 

# Define monitor identifiers. Use "Primary", "Secondary" or a specific string 
MONITORS = {
    "Primary Monitor": "Primary",
    "Secondary Monitor": "Secondary"
}

# Define common VCP Features (Name, VCP Code, Min Value, Max Value)
VCP_FEATURES = {
    "Brightness (0-100)": ("10", 0, 100),
    "Contrast (0-100)": ("12", 0, 100),
    "Volume (0-100)": ("62", 0, 100),
    "Input Select": ("60", 1, 20),
    "Power Mode": ("D6", 1, 5),
    "OSD Language": ("CC", 1, 10),
    "Restore Factory Defaults": ("04", 1, 1),
}

# Define 5 Theme Presets (Brightness, Contrast, Background Color, Foreground Color)
# Background colors range from light gray (lightest) to dark gray/near-black (darkest)
THEMES = {
    "Lightest": (80, 70, "#f0f0f0", "black"),  # B80, C70, Very Light BG, Black Text
    "Light":    (65, 58, "#cccccc", "black"),  # B65, C58, Light Gray BG, Black Text
    "Medium":   (50, 45, "#888888", "white"),  # B50, C45, Medium Gray BG, White Text
    "Dark":     (35, 33, "#444444", "white"),  # B35, C33, Dark Gray BG, White Text
    "Darkest":  (20, 20, "#1a1a1a", "white"),  # B20, C20, Very Dark BG, White Text
}

BRIGHTNESS_VCP = VCP_FEATURES["Brightness (0-100)"][0] # '10'
CONTRAST_VCP = VCP_FEATURES["Contrast (0-100)"][0]     # '12'

# --- Application Logic (Functions remain the same for CLI interaction) ---

def get_vcp_value(monitor_string, vcp_code):
    """Executes ControlMyMonitor.exe /GetValue and retrieves the value from the exit code."""
    command = [
        CMM_PATH, 
        "/GetValue", 
        monitor_string, 
        vcp_code
    ]
    
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        
        if result.returncode > 255 or result.returncode < 0:
            status_var.set(f"Error fetching value (Code {result.returncode}): {result.stderr.strip()}")
            return None
        
        return result.returncode
        
    except FileNotFoundError:
        status_var.set(f"Error: {CMM_PATH} not found.")
        return None
    except Exception as e:
        status_var.set(f"An unexpected error occurred: {e}")
        return None

def set_vcp_value(monitor_string, vcp_code, value, feature_name="Setting"):
    """Executes ControlMyMonitor.exe /SetValue."""
    command = [
        CMM_PATH, 
        "/SetValue", 
        monitor_string, 
        vcp_code, 
        str(value)
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        # Only log the error to status bar, don't show a full popup
        status_var.set(f"Command Error (Exit Code {e.returncode}): Failed to set {feature_name}. Monitor/VCP Code may not be supported.")
        return False
    except FileNotFoundError:
        status_var.set(f"Error: {CMM_PATH} not found.")
        return False
    except Exception as e:
        status_var.set(f"An unexpected error occurred: {e}")
        return False

def apply_theme(theme_name):
    """Applies a predefined Brightness and Contrast theme to the selected monitor."""
    monitor_name = monitor_var.get()
    monitor_string = MONITORS.get(monitor_name)
    
    if not monitor_string:
        status_var.set("Error: Please select a monitor first.")
        return

    brightness_val, contrast_val, _, _ = THEMES[theme_name]
    
    # Set Brightness
    set_b = set_vcp_value(monitor_string, BRIGHTNESS_VCP, brightness_val, "Brightness")
    
    # Set Contrast
    set_c = set_vcp_value(monitor_string, CONTRAST_VCP, contrast_val, "Contrast")
    
    if set_b and set_c:
        # Update the manual controls to reflect the contrast value (arbitrarily chosen to be visible)
        feature_var.set("Contrast (0-100)")
        current_value_var.set(contrast_val)
        value_slider.set(contrast_val)
        update_ui_for_feature()
        
        status_var.set(f"SUCCESS: Applied '{theme_name}' Theme (B:{brightness_val}, C:{contrast_val}) to {monitor_name}")

# --- UI Update Handlers (for manual controls) ---

def update_ui_for_feature(event=None):
    """Updates the UI elements when a new VCP feature is selected."""
    selected_feature = feature_var.get()
    
    if selected_feature:
        vcp_code, min_val, max_val = VCP_FEATURES[selected_feature]
        
        value_slider.config(from_=min_val, to=max_val)
        vcp_code_label.config(text=f"VCP Code: {vcp_code} (Range: {min_val}-{max_val})")
        current_value_var.set(min_val)
        
        status_var.set(f"Selected: {selected_feature}. Press 'Get Current Value' to check status.")

def on_get_value_click():
    """Handler for the 'Get Current Value' button."""
    monitor_name = monitor_var.get()
    monitor_string = MONITORS.get(monitor_name)
    selected_feature = feature_var.get()
    vcp_code, _, _ = VCP_FEATURES[selected_feature]
    
    if monitor_string and vcp_code:
        current_val = get_vcp_value(monitor_string, vcp_code)
        if current_val is not None:
            current_value_var.set(current_val)
            value_slider.set(current_val)
            status_var.set(f"Current Value for {selected_feature}: {current_val}")

def on_set_value_click():
    """Handler for the 'Set New Value' button."""
    monitor_name = monitor_var.get()
    monitor_string = MONITORS.get(monitor_name)
    selected_feature = feature_var.get()
    vcp_code, _, _ = VCP_FEATURES[selected_feature]
    
    try:
        new_value = int(current_value_var.get())
    except ValueError:
        status_var.set("Error: Value must be an integer.")
        return
    
    if monitor_string and vcp_code:
        set_vcp_value(monitor_string, vcp_code, new_value, selected_feature.split(' ')[0])


# --- GUI Setup ---
root = tk.Tk()
root.title("ControlMyMonitor Python CLI GUI")
root.geometry("600x400") # Wider window for the sidebar
root.resizable(False, False)

main_frame = ttk.Frame(root, padding="10")
main_frame.pack(fill='both', expand=True)

# Define two sub-frames for layout: one for controls (left) and one for themes (right)
control_frame = ttk.Frame(main_frame, padding="5")
control_frame.grid(row=0, column=0, sticky='nsew')
theme_frame = ttk.LabelFrame(main_frame, text="Preset Themes", padding="10")
theme_frame.grid(row=0, column=1, sticky='ns', padx=(10, 0))

# Configure grid weights to ensure the control frame expands horizontally
main_frame.grid_columnconfigure(0, weight=1)
main_frame.grid_columnconfigure(1, weight=0)

# --- Theme Buttons (Right Side) ---
theme_order = list(THEMES.keys())
for i, theme_name in enumerate(theme_order):
    b_val, c_val, bg_color, fg_color = THEMES[theme_name]
    
    # Use tk.Button for custom colors
    btn = tk.Button(
        theme_frame, 
        text=f"⭐ {theme_name}\n(B{b_val}, C{c_val})", 
        command=lambda name=theme_name: apply_theme(name),
        bg=bg_color,
        fg=fg_color,
        activebackground=bg_color,
        activeforeground=fg_color,
        width=15,
        height=2
    )
    # List buttons from top (Lightest) to bottom (Darkest)
    btn.grid(row=i, column=0, sticky='ew', pady=5)


# --- Control Elements (Left Side) ---

# 1. Monitor Selection
monitor_label = ttk.Label(control_frame, text="1. Select Monitor:")
monitor_label.grid(row=0, column=0, sticky='w', pady=5)

monitor_var = tk.StringVar(root)
monitor_var.set(list(MONITORS.keys())[0])

monitor_dropdown = ttk.OptionMenu(
    control_frame, 
    monitor_var, 
    monitor_var.get(), 
    *MONITORS.keys()
)
monitor_dropdown.grid(row=0, column=1, sticky='we', padx=5)
control_frame.grid_columnconfigure(1, weight=1) # Make dropdown expand

# Separator
ttk.Separator(control_frame, orient='horizontal').grid(row=1, column=0, columnspan=2, sticky='we', pady=5)


# 2. VCP Feature Selection
feature_label = ttk.Label(control_frame, text="2. Select VCP Feature:")
feature_label.grid(row=2, column=0, sticky='w', pady=5)

feature_var = tk.StringVar(root)
feature_var.set(list(VCP_FEATURES.keys())[0])

feature_dropdown = ttk.OptionMenu(
    control_frame, 
    feature_var, 
    feature_var.get(), 
    *VCP_FEATURES.keys(),
    command=update_ui_for_feature
)
feature_dropdown.grid(row=2, column=1, sticky='we', padx=5)

# VCP Code and Range Info
vcp_code_label = ttk.Label(control_frame, text="")
vcp_code_label.grid(row=3, column=0, columnspan=2, sticky='w', pady=(0, 10))


# 3. Get Current Value Button
get_value_button = ttk.Button(control_frame, text="Get Current Value", command=on_get_value_click)
get_value_button.grid(row=4, column=0, columnspan=2, sticky='we', pady=5)

# Separator
ttk.Separator(control_frame, orient='horizontal').grid(row=5, column=0, columnspan=2, sticky='we', pady=10)


# 4. Set New Value Controls
set_value_label = ttk.Label(control_frame, text="3. Set New Value:")
set_value_label.grid(row=6, column=0, sticky='w', pady=5)

# Value Entry and Slider
current_value_var = tk.StringVar(root, value=50) 
value_entry = ttk.Entry(control_frame, textvariable=current_value_var, width=5)
value_entry.grid(row=6, column=1, sticky='e', padx=5)

def update_entry_from_slider(value):
    """Update the entry box when the slider moves."""
    current_value_var.set(int(float(value)))

value_slider = ttk.Scale(
    control_frame,
    from_=0, 
    to=100, 
    orient='horizontal', 
    command=update_entry_from_slider
)
value_slider.grid(row=7, column=0, columnspan=2, sticky='we', pady=5)

set_value_button = ttk.Button(control_frame, text="Set New Value", command=on_set_value_click)
set_value_button.grid(row=8, column=0, columnspan=2, sticky='we', pady=10)

# 5. Status Bar
status_var = tk.StringVar(root)
status_var.set("Ready. Select monitor and feature, or use a theme preset.")
status_label = ttk.Label(root, textvariable=status_var, relief=tk.SUNKEN, anchor='w')
status_label.pack(side=tk.BOTTOM, fill='x')

# Initialize UI with default feature's settings
update_ui_for_feature()

root.mainloop()