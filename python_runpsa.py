import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import subprocess
import json
import sv_ttk
import re
import pywinstyles, sys

def get_base_dir():
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle
        base_dir = os.path.dirname(sys.executable)  # folder where exe lives
    else:
        # Running in normal Python environment
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return base_dir

BASE_DIR = get_base_dir()
LAST_USED_CONFIG_FILE = os.path.join(BASE_DIR, "settings.json")
print(f"Using last used config file at: {LAST_USED_CONFIG_FILE}")

# Initialize the GUI
root = tk.Tk()

# Global variables for the configuration values
raw_files_var = []
psa_dir_var = tk.StringVar()
executables_dir_var = tk.StringVar()
output_file_var = tk.StringVar()
executables = []
sbedataprocessing_exe = ""

# Create an empty list to store the frames for each PSA file
psa_frames = []
psa_files_frame = tk.Frame(root)  # Initialize psa_files_frame as a Tkinter frame

def resolve_path(path):
    """Convert stored config paths (absolute or relative) to absolute FS paths."""
    if not path:
        return path

    # If it's already absolute, return it
    if os.path.isabs(path):
        return os.path.normpath(path)

    # If it's relative, resolve relative to BASE_DIR
    return os.path.normpath(os.path.join(BASE_DIR, path))

def update_psa_files():
    """
    Update all .psa files with the correct InstrumentPath, InputDir, and OutputDir.
    Resolves relative paths to absolute paths and escapes backslashes.
    """
    updated_files = []
    errors = []

    #print(raw_files_var)

    raw_files = [resolve_path(f.strip('"')) for f in raw_files_var if f]
    psa_dir = resolve_path(psa_dir_var.get())
    output_file_dir = resolve_path(output_file_var.get())

    if not psa_dir or not os.path.isdir(psa_dir):
        messagebox.showerror("PSA Update Error", "No valid PSA directory selected.")
        return
    if not raw_files:
        messagebox.showerror("PSA Update Error", "No raw files selected.")
        return

    # Find all PSA files in the directory
    psa_files = [f for f in os.listdir(psa_dir) if f.lower().endswith(".psa")]
    if not psa_files:
        messagebox.showinfo("PSA Update", "No PSA files found in the PSA directory.")
        return

    for raw_file in raw_files:
            base_name = os.path.splitext(os.path.basename(raw_file))[0]
            raw_dir = os.path.dirname(raw_file)

            for psa_file in psa_files:
                psa_path = resolve_path(os.path.join(psa_dir, psa_file))

                # Match executable type
                exe_basename = ""
                for exe in executables:
                    if exe.lower() in psa_file.lower():
                        exe_basename = exe.lower()
                        break

                # Determine InputDir
                if "datcnvw" in exe_basename:
                    input_dir = raw_dir
                elif "bottlesumw" in exe_basename:
                    ros_file = f"{base_name}.ros"
                    input_dir = os.path.join(output_file_dir, ros_file)
                else:
                    input_dir = output_file_dir

                # Convert all paths to forward slashes to avoid \U errors
                input_dir = resolve_path(input_dir).replace("\\", "/")
                output_file_dir_clean = resolve_path(output_file_dir).replace("\\", "/")
                xmlcon_file = f"{base_name}.XMLCON"
                instrument_path = resolve_path(os.path.join(raw_dir, xmlcon_file)).replace("\\", "/")

                try:
                    with open(psa_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    new_content = content

                    # Only replace if the value is different
                    match_input = re.search(r'<InputDir\s+value="([^"]*)"', content, re.IGNORECASE)
                    if not match_input or match_input.group(1) != input_dir:
                        new_content = re.sub(
                            r'\s*<InputDir\s+value="[^"]*"\s*/>',
                            f'  <InputDir value="{input_dir}" />',
                            new_content, flags=re.IGNORECASE
                        )

                    match_output = re.search(r'<OutputDir\s+value="([^"]*)"', content, re.IGNORECASE)
                    if not match_output or match_output.group(1) != output_file_dir_clean:
                        new_content = re.sub(
                            r'\s*<OutputDir\s+value="[^"]*"\s*/>',
                            f'  <OutputDir value="{output_file_dir_clean}" />',
                            new_content, flags=re.IGNORECASE
                        )

                    match_instr = re.search(r'<InstrumentPath\s+value="([^"]*)"', content, re.IGNORECASE)
                    if match_instr and match_instr.group(1) != instrument_path:
                        new_content = re.sub(
                            r'<InstrumentPath\s+value=".*?" ?/>',
                            f'<InstrumentPath value="{instrument_path}" />',
                            new_content
                        )

                    # Check <InstrumentMatch> and set value="0" if different
                    match_instrument = re.search(r'<InstrumentMatch\s+value="([^"]*)"', content, re.IGNORECASE)
                    if match_instrument and match_instrument.group(1) != "0":
                        new_content = re.sub(
                            r'<InstrumentMatch\s+value="[^"]*"\s*/>',
                            '<InstrumentMatch value="0" />',
                            new_content, flags=re.IGNORECASE
                        )

                    # Only write if something actually changed
                    if new_content != content:
                        with open(psa_path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        updated_files.append(psa_path)

                except Exception as e:
                    errors.append(f"{psa_path}: {e}")

    # Show updated files window
    #if updated_files:
    #    show_updated_files_window(updated_files)

    # Show errors window if any
    if errors:
        show_errors_window(errors)


# Popup window for updated PSA files
def show_updated_files_window(file_list):
    window = tk.Toplevel(root)
    window.title("Updated PSA Files")
    window.geometry("500x400")

    label = tk.Label(window, text="The following PSA files were updated:", font=("Arial", 12))
    label.pack(pady=10)

    listbox = tk.Listbox(window, width=80, height=20)
    listbox.pack(padx=10, pady=5, fill="both", expand=True)

    scrollbar = tk.Scrollbar(listbox, orient="vertical")
    scrollbar.pack(side="right", fill="y")
    listbox.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=listbox.yview)

    for file_path in file_list:
        listbox.insert("end", file_path)

    ttk.Button(window, text="Close", command=window.destroy).pack(pady=10)

# Popup window for errors
def show_errors_window(error_list):
    window = tk.Toplevel(root)
    window.title("Errors Updating PSA Files")
    window.geometry("500x400")

    label = tk.Label(window, text="The following errors occurred:", font=("Arial", 12), fg="red")
    label.pack(pady=10)

    text = tk.Text(window, width=80, height=20)
    text.pack(padx=10, pady=5, fill="both", expand=True)

    scrollbar = tk.Scrollbar(text, orient="vertical")
    scrollbar.pack(side="right", fill="y")
    text.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=text.yview)

    for err in error_list:
        text.insert("end", err + "\n")

    text.config(state="disabled")  # make read-only
    ttk.Button(window, text="Close", command=window.destroy).pack(pady=10)

# Function to override sv_ttk checkbox style
def override_checkbox_style():
    # Override the style for Checkbuttons
    style = ttk.Style()

    # Modify the default style used by Checkbuttons
    style.configure('TCheckbutton',
                    background='#2c2c2c',  # Dark background for the checkbox (for dark theme)
                    foreground='#ffffff',  # White text for the checkbox label
                    font=('Arial', 10))  # Adjust font if necessary

    # Ensure the focus highlights are appropriate
    style.map('TCheckbutton', foreground=[('active', 'yellow')])

def select_raw_file():
    files = filedialog.askopenfilenames(
        title="Select Raw .hex File",
        filetypes=[("HEX files", "*.hex")]
    )
    if files:
        raw_files_var.clear()
        raw_files_var.extend(files)
        print("Selected raw files:", raw_files_var)

def select_psa_directory():
    dir_path = filedialog.askdirectory(title="Select Directory Containing .psa Files")
    if dir_path:
        psa_dir_var.set(dir_path)
        
        # If a config is loaded, pass it along to load_psa_files
        if 'config' in globals() and config is not None:
            load_psa_files(dir_path, config)
        else:
            # No config loaded, just load PSA files without config
            load_psa_files(dir_path)

def edit_xml_file():
    raw_file = raw_file_var.get()
    psa_dir = psa_dir_var.get()
    output_file_dir = output_file_var.get()

    if not os.path.isfile(raw_file):
        messagebox.showerror("Error", "Please select a valid raw .hex file.")
        return

    if not os.path.isdir(psa_dir):
        messagebox.showerror("Error", "Please select a valid directory containing .psa files.")
        return

    if not output_file_dir:
        messagebox.showerror("Error", "Please select an output file path.")
        return

    selected_psa_file = []
    for psa_frame, executable_dropdown, select_var, *_ in psa_frames:
        if select_var.get():
            selected_executable = executable_dropdown.get()

            psa_file = psa_frame.winfo_children()[0].cget("text")

            if selected_executable == "Select Executable Path":
                messagebox.showerror("Error", f"Please select an executable for {psa_file}.")
                return
            
            executable_path = os.path.join(executables_dir_var.get(), selected_executable) if selected_executable != "Select Executable Path" else ""
            selected_psa_file.append((psa_file, executable_path))

    for psa_file, executable in selected_psa_file:
        psa_file_path = os.path.join(psa_dir, psa_file)

        base_name = os.path.splitext(os.path.basename(raw_file))[0]
        output_file = f"{base_name}.cnv"

        if "DatCnvW" in os.path.basename(executable):
            input_file = raw_file
        else:
            input_file = os.path.normpath(os.path.join(output_file_dir, output_file))

        command = [
            executable,
            f"/i{input_file}",
            f"/o{output_file_dir}",
            f"/f{output_file}",
            f"/p{psa_file_path}",
        ]

# Global variable to store the selected PSA directory
psa_dir_path = ""  # Global variable to store the selected PSA directory

def open_in_sbedataprocessing(psa_dir, psa_file, executable_name):
    # Construct the full path to the executable based on the provided executable name
    sbedataprocessing_exe = os.path.join(executables_dir_var.get(), executable_name)
    print(executable_name)

    # Check if the executable exists
    if not os.path.isfile(sbedataprocessing_exe):
        messagebox.showerror("Error", f"Executable '{executable_name}' not found in the selected executables directory: {executables_dir_var.get()}")
        return

    # Construct the full path to the PSA file
    psa_file_path = os.path.join(psa_dir, psa_file)
    
    # Normalize the paths to ensure consistent separators
    psa_file_path = os.path.normpath(psa_file_path)

    # Check if the PSA file exists
    if not os.path.isfile(psa_file_path):
        messagebox.showerror("Error", f"The PSA file '{psa_file}' does not exist.")
        return

    # Wrap executable path and PSA file path in quotes to handle spaces
    psa_file_path = f'"{psa_file_path}"'

    # Log the command to check for issues
    print(f"Running: {executable_name} {psa_file_path}")

    # Launch the executable with the PSA file as an argument
    try:
        result = subprocess.run([executable_name, psa_file_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        print("Output:", result.stdout)
        print("Error:", result.stderr)
    except FileNotFoundError:
        messagebox.showerror("Error", f"Executable '{executable_name}' not found at: {executable_name}")
    except subprocess.CalledProcessError as e:
        # Capture and display any error output
        messagebox.showerror("Error", f"Failed to open PSA file with {executable_name}: {e.stderr}")


def load_psa_files(psa_dir, config=None):
    global psa_dir_path
    psa_dir_path = psa_dir

    # Clear previous frames
    for frame, *_ in psa_files_frame.psa_frames:
        frame.destroy()
    psa_files_frame.psa_frames.clear()

    # List all .psa files in the selected directory
    psa_files = [f for f in os.listdir(psa_dir) if f.endswith('.psa')]

    if not psa_files:
        messagebox.showwarning("No Files Found", "No .psa files found in the selected directory.")
        return

    # If config is available, use it to load PSA files, otherwise skip this part
    if config:
        for psa_file in psa_files:
            matching_psa_data = next((item for item in config.get("psa_files", []) if item.get("psa_file") == psa_file), None)
            executable = matching_psa_data.get("executable", "") if matching_psa_data else ""
            selected = matching_psa_data.get("selected", False) if matching_psa_data else False
            psa_files_frame.add_psa_file_row(psa_file, executables, executable, selected)
    else:
        # If no config, just add the PSA files without extra config data
        for psa_file in psa_files:
            psa_files_frame.add_psa_file_row(psa_file, executables)


# Function to load the last used configuration (only at the start of the app)
def load_last_used_config():
    #print(LAST_USED_CONFIG_FILE)
    if os.path.exists(LAST_USED_CONFIG_FILE):  # Check if the last used config file exists
        try:
            with open(LAST_USED_CONFIG_FILE, "r") as f:
                last_used_config = json.load(f)
                config_file_path = last_used_config.get("config_file_path")
                if config_file_path and os.path.exists(config_file_path):  # Ensure the config file exists
                    with open(config_file_path, "r") as config_file:
                        config = json.load(config_file)
                        load_config_to_gui(config)  # Update the GUI with the loaded config
                else:
                    messagebox.showinfo("Info", "Last used config file not found. Please select a new one.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration from last used file: {e}")
    else:
        messagebox.showinfo("Info", "No last used config file found. Please select a configuration file.")

# Function to load a configuration file (called by the "Load Configuration" button)
def load_config():
    # Prompt the user to select a configuration file
    config_file_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
    if not config_file_path:
        messagebox.showerror("Error", "No configuration file selected.")
        return

    try:
        with open(config_file_path, "r") as config_file:
            config = json.load(config_file)
            # Save the path of the selected config file as the new "last used config file"
            save_last_used_config(config_file_path)
            load_config_to_gui(config)  # Update the GUI with the loaded config
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load configuration: {e}")

def save_last_used_config(file_path):
    try:
        with open(LAST_USED_CONFIG_FILE, "w") as f:
            json.dump({"config_file_path": file_path}, f)
        #print(f"Saved last used config file path: {file_path} to {LAST_USED_CONFIG_FILE}")
    except Exception as e:
        print(f"Error saving last used config: {e}")

def load_config_to_gui(config):
    # Clear previous PSA UI
    psa_files_frame.psa_frames.clear()
    for child in psa_files_frame.scrollable_frame.winfo_children():
        child.destroy()

    # --- Raw files are session-only ---
    raw_files_var.clear()
    raw_file_display_label.config(text="No files selected")


    # --- Load directories ---
    psa_dir_var.set(config.get("psa_dir", ""))
    executables_dir_var.set(config.get("executables_dir", ""))
    output_file_var.set(config.get("output_file", ""))

    # --- Load executables list ---
    global executables
    executables = config.get("executables", [])

    # --- Load PSA file rows ---
    psa_list = config.get("psa_files", [])

    if not isinstance(psa_list, list):
        print("Invalid psa_files section in config:", psa_list)
        return  # do not crash

    for psa_data in psa_list:

        # Skip corrupted entries
        if not isinstance(psa_data, dict):
            print("Skipping bad PSA entry:", psa_data)
            continue
        
        psa_file_name = psa_data.get("psa_file", "")
        executable_path = psa_data.get("executable", "")
        selected = psa_data.get("selected", False)

        exe_name = os.path.basename(executable_path) if executable_path else ""

        psa_files_frame.add_psa_file_row(
            psa_file=psa_file_name,
            executables=executables,
            executable=exe_name,
            selected=selected
        )


# Function to select the directory containing executable files
def select_executables_directory():
    # Allow the user to select the directory containing executable files
    dir_path = filedialog.askdirectory(title="Select Directory Containing Executables")
    if dir_path:
        # List all executable files in the selected directory
        global executables
        executables = [f for f in os.listdir(dir_path) if f.endswith('.exe')]
        print(f"Available executables: {executables}")

        # Update dropdowns with the available executables
        for _, executable_dropdown, _, _ in psa_frames:
            executable_dropdown["values"] = ["Select Executable Path"] + executables
            executable_dropdown.set("Select Executable Path")

def save_config():
    # Ask the user for the file path where the configuration should be saved
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
    if not file_path:
        return  # If no file is selected, exit the function

    config = {
        "psa_dir": psa_dir_var.get(),
        "executables_dir": executables_dir_var.get(),
        "executables": executables,
        "output_file": output_file_var.get(),
        "psa_files": []
    }

    # Save PSA files in the actual visual order of the scrollable list
    print("\n--- Debug: Saving PSA Files Order ---")
    for idx, (frame, psa_file, executable_dropdown, select_var) in enumerate(psa_files_frame.psa_frames):
        executable = executable_dropdown.get()
        executable_path = ""
        if executable != "Select Executable Path":
            executable_path = os.path.join(executables_dir_var.get(), executable)
        selected = select_var.get()

        config["psa_files"].append({
            "psa_file": psa_file,
            "executable": executable_path,
            "selected": selected
        })
        print(f"Index {idx}: {psa_file}, Executable: {executable_path}, Selected: {selected}")
    print("--- End Debug ---\n")

    try:
        with open(file_path, "w") as f:
            json.dump(config, f, indent=4)
        messagebox.showinfo("Configuration Saved", "Your configuration has been saved successfully!")
        save_last_used_config(file_path)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save configuration: {e}")

# Main processing function
def process_data():
    
    raw_files = list(raw_files_var)


    if not raw_files:
        messagebox.showerror("Error", "No raw files selected.")
        return
    
    update_psa_files()
    
    psa_dir = resolve_path(psa_dir_var.get())
    print("Using PSA directory:", psa_dir)

    output_file_dir = resolve_path(output_file_var.get())

    if not raw_files or not all(os.path.isfile(f) for f in raw_files):
        messagebox.showerror("Error", "Please select one or more valid raw .hex files.")
        return

    if not os.path.isdir(psa_dir):
        messagebox.showerror("Error", "Please select a valid directory containing .psa files.")
        return

    if not output_file_dir:
        messagebox.showerror("Error", "Please select an output file path.")
        return

    selected_psa_files = []
    for frame, psa_file, executable_dropdown, select_var in psa_files_frame.psa_frames:
        if select_var.get():
            executable = executable_dropdown.get()
            if executable == "Select Executable Path":
                messagebox.showerror("Error", f"Please select an executable for {psa_file}")
                return
            selected_psa_files.append((psa_file, executable))

    for raw_file in raw_files:
        base_name = os.path.splitext(os.path.basename(raw_file))[0]
        output_file = f"{base_name}.cnv"

        for psa_file, executable in selected_psa_files:
            psa_file_path = os.path.join(psa_dir, psa_file)
            #print(f"Running {executable} for {psa_file} with raw file {raw_file}")

            exe_basename = os.path.basename(executable).lower()

            if "datcnvw" in exe_basename:
                input_file = raw_file
            elif "bottlesumw" in exe_basename:
                ros_file = f"{base_name}.ros"
                input_file = os.path.join(output_file_dir, ros_file)
            else:
                input_file = os.path.join(output_file_dir, output_file)


            command = [
                executable,
                f"/i{input_file}",
                f"/o{output_file_dir}",
                f"/f{output_file}",
                f"/p{psa_file_path}",
                "/s"
            ]

            # Append /c<XMLCON> only for DatCnvW, Derive, and bottlesum
            exe_basename = os.path.basename(executable).lower()
            if "datcnvw" in exe_basename or "derivew" in exe_basename or 'bottlesumw' in exe_basename:
                xmlcon_file = os.path.splitext(os.path.basename(raw_file))[0].upper() + ".xmlcon"
                xmlcon_path = os.path.join(os.path.dirname(raw_file), xmlcon_file)
                command.append(f"/c{xmlcon_path}")

            try:
                result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
                if result.returncode != 0:
                    messagebox.showerror("Error", f"Error running {executable} for {psa_file}: {result.stderr}")
                else:
                    print(f"{executable} ran successfully for {psa_file}: {result.stdout}")
            except FileNotFoundError:
                messagebox.showerror("Error", f"Executable not found at: {command[0]}")
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")

    messagebox.showinfo("Processing Complete", "Selected .psa files have been processed.")


def apply_theme_to_titlebar(root):
    version = sys.getwindowsversion()

    if version.major == 10 and version.build >= 22000:
        # Set the title bar color to the background color on Windows 11 for better appearance
        pywinstyles.change_header_color(root, "#242424" if sv_ttk.get_theme() == "dark" else "#fafafa")
    elif version.major == 10:
        pywinstyles.apply_style(root, "dark" if sv_ttk.get_theme() == "dark" else "normal")

        # A hacky way to update the title bar's color on Windows 10 (it doesn't update instantly like on Windows 11)
        root.wm_attributes("-alpha", 0.99)
        root.wm_attributes("-alpha", 1)

# First, apply the theme
sv_ttk.set_theme("dark")

# Call the override function to fix the checkbox behavior
override_checkbox_style()

# Then, apply the title bar theme
apply_theme_to_titlebar(root)

root.title("CTD Processor ")

# Set window icon
try:
    root.iconphoto(True, tk.PhotoImage(file=r"C:\Users\bonny\github\ctd_processing\icon.png"))  # Ensure the file path is correct
except Exception as e:
    print(f"Error setting icon: {e}")

# Set window size and background color
root.minsize(670, 300)

# Configure the grid layout
root.grid_rowconfigure(0, weight=0)
root.grid_rowconfigure(1, weight=0)
root.grid_rowconfigure(2, weight=0)
root.grid_rowconfigure(3, weight=0)
root.grid_rowconfigure(4, weight=1)
root.grid_rowconfigure(5, weight=0)
root.grid_rowconfigure(6, weight=0)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=0)

# Variables
raw_file_var = []
psa_dir_var = tk.StringVar()
executables_dir_var = tk.StringVar()
output_file_var = tk.StringVar()
psa_frames = []
executables = []

def select_raw_file():
    files = filedialog.askopenfilenames(
        title="Select Raw .hex File(s)",
        filetypes=[("HEX files", "*.hex")]
    )
    if files:
        raw_files_var.clear()
        raw_files_var.extend(os.path.normpath(os.path.abspath(f)) for f in files)
        raw_file_display_label.config(
            text=", ".join(os.path.basename(f) for f in raw_files_var)
        )
        print("Selected raw files:", raw_files_var)

# Layout (unchanged, just for reference)
tk.Label(root, text="Select Raw .hex File:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
raw_file_display_label = tk.Label(root, text="No files selected", anchor="w", bg="#2b2b2b", fg="white")
raw_file_display_label.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
ttk.Button(root, text="Browse", command=select_raw_file).grid(row=0, column=2, padx=10, pady=5)

tk.Label(root, text="Select Directory Containing .psa Files:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
tk.Entry(root, textvariable=psa_dir_var, width=50).grid(row=1, column=1, padx=10, pady=5, sticky="ew")
ttk.Button(root, text="Browse", command=select_psa_directory).grid(row=1, column=2, padx=10, pady=5)

tk.Label(root, text="Select Directory Containing Executables:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
tk.Entry(root, textvariable=executables_dir_var, width=50).grid(row=2, column=1, padx=10, pady=5, sticky="ew")
ttk.Button(root, text="Browse", command=select_executables_directory).grid(row=2, column=2, padx=10, pady=5)

tk.Label(root, text="Select Output File Directory:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
tk.Entry(root, textvariable=output_file_var, width=50).grid(row=3, column=1, padx=10, pady=5, sticky="ew")
ttk.Button(root, text="Browse", command=lambda: output_file_var.set(filedialog.askdirectory(title="Select Output Directory"))).grid(row=3, column=2, padx=10, pady=5)

def bind_mouse_scroll(widget, canvas):
    """Bind mouse wheel / touchpad scrolling to the canvas."""
    def on_mousewheel(event):
        # For Windows & MacOS
        if event.num == 5 or event.delta < 0:
            canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            canvas.yview_scroll(-1, "units")

    # Windows and MacOS
    widget.bind_all("<MouseWheel>", on_mousewheel)
    # Linux
    widget.bind_all("<Button-4>", on_mousewheel)
    widget.bind_all("<Button-5>", on_mousewheel)

def disable_combobox_scroll(combobox):
    """Prevent mouse wheel from changing the Combobox selection."""
    def stop_scroll(event):
        return "break"  # Stops event propagation

    combobox.bind("<MouseWheel>", stop_scroll)  # Windows / macOS
    combobox.bind("<Button-4>", stop_scroll)    # Linux scroll up
    combobox.bind("<Button-5>", stop_scroll)    # Linux scroll down

def allow_canvas_scroll_over_combobox(combobox, canvas):
    """Prevent Combobox from changing its value on scroll, but still scroll the canvas."""
    def on_mousewheel(event):
        # Forward the scroll to the canvas
        if event.num == 5 or event.delta < 0:
            canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            canvas.yview_scroll(-1, "units")
        return "break"  # Prevent the Combobox itself from scrolling

    # Bind for Windows/macOS
    combobox.bind("<MouseWheel>", on_mousewheel)
    # Bind for Linux
    combobox.bind("<Button-4>", on_mousewheel)
    combobox.bind("<Button-5>", on_mousewheel)

class ScrollablePSAList(tk.Frame):
    def __init__(self, parent, row_height=40, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.row_height = row_height
        self.psa_frames = []

        # Dragging helpers
        self.drag_widget = None
        self.placeholder = None
        self.offset_y = 0
        self.drag_width = None
        self.drag_height = None

        # Canvas + scrollbar
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Make rows always stretch to canvas width
        self.canvas.bind("<Configure>", self.on_canvas_resize)

    def on_canvas_resize(self, event):
        # Resize the scrollable_frame to match the canvas width
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        
        # Also resize each row to match the new width
        for frame, *_ in self.psa_frames:
            frame.configure(width=event.width)
        
        # Resize placeholder too
        if self.placeholder:
            self.placeholder.configure(width=event.width)

    # -------------------------- DRAG FUNCTIONS --------------------------

    def bind_drag_events(self, widget):
        widget.bind("<ButtonPress-1>", self.on_press)
        widget.bind("<B1-Motion>", self.on_drag)
        widget.bind("<ButtonRelease-1>", self.on_release)

    def get_frame_from_widget(self, widget):
        while widget and widget not in [f[0] for f in self.psa_frames]:
            widget = widget.master
        return widget

    def on_press(self, event):
        widget = self.get_frame_from_widget(event.widget)
        if not widget:
            return

        self.drag_widget = widget
        widget.update_idletasks()
        self.drag_width = widget.winfo_width()
        self.drag_height = widget.winfo_height()

        # Create placeholder
        self.placeholder = tk.Frame(self.scrollable_frame, height=self.drag_height)
        self.placeholder.pack(fill="x", pady=2)

        widget.lift()
        widget.place(
            in_=self.scrollable_frame,
            x=0,
            y=widget.winfo_y(),
            width=self.drag_width,
            height=self.drag_height
        )

        self.offset_y = event.y

    def on_drag(self, event):
        if not self.drag_widget:
            return

        canvas_y = self.canvas.canvasy(event.y_root - self.winfo_rooty())
        new_y = canvas_y - self.offset_y

        self.drag_widget.place_configure(y=new_y)
        self.update_placeholder(new_y)

        # Auto-scroll while dragging
        if event.y < 30:
            self.canvas.yview_scroll(-1, "units")
        elif event.y > self.winfo_height() - 30:
            self.canvas.yview_scroll(1, "units")


    def on_release(self, event):
        if not self.drag_widget:
            return

        # Remove from place geometry
        self.drag_widget.place_forget()

        # Find index of dragged widget in internal list
        dragged_index = next((i for i, f in enumerate(self.psa_frames) if f[0] is self.drag_widget), None)
        if dragged_index is None:
            return

        # Determine sibling frame to pack before (if not at the end)
        if dragged_index < len(self.psa_frames) - 1:
            sibling_frame = self.psa_frames[dragged_index + 1][0]
            self.drag_widget.pack(before=sibling_frame, fill="x", pady=2)
        else:
            self.drag_widget.pack(fill="x", pady=2)

        # Destroy placeholder
        if self.placeholder:
            self.placeholder.destroy()
            self.placeholder = None

        self.drag_widget = None


    def update_placeholder(self, widget_y):
        positions = []

        for frame, *_ in self.psa_frames:
            if frame is self.drag_widget:
                continue
            if not frame.winfo_exists():
                continue
            try:
                y = frame.winfo_y()
            except tk.TclError:
                continue
            positions.append((frame, y))

        # Default: insert at the end
        insert_index = len(positions)

        for idx, (frame, y) in enumerate(positions):
            if widget_y < y:
                insert_index = idx
                break

        # Stretch placeholder width
        if self.placeholder:
            self.placeholder.pack_forget()
            if insert_index < len(positions):
                self.placeholder.pack(before=positions[insert_index][0], fill="x", pady=2)
            else:
                self.placeholder.pack(fill="x", pady=2)
            self.placeholder.configure(width=self.canvas.winfo_width())

        # Update internal order list to reflect new position of dragged frame
        dragged_tuple = next(f for f in self.psa_frames if f[0] is self.drag_widget)
        self.psa_frames = [f for f in self.psa_frames if f[0] is not self.drag_widget]
        self.psa_frames.insert(insert_index, dragged_tuple)


    def update_internal_order(self):
        """Keeps psa_frames list synchronized with visual order, ignoring placeholder."""
        ordered = []
        for child in self.scrollable_frame.winfo_children():
            if child is self.placeholder:  # skip placeholder
                continue
            for f in self.psa_frames:
                if f[0] is child:
                    ordered.append(f)
                    break
        self.psa_frames = ordered


    # -------------------------- ROW CREATION --------------------------

    def add_psa_file_row(self, psa_file, executables, executable="", selected=False):
        frame = ttk.Frame(self.scrollable_frame)
        frame.pack(fill="x", expand=True, pady=2)

        # Drag handle
        drag_label = ttk.Label(frame, text="≡", cursor="hand2")
        drag_label.grid(row=0, column=0, padx=5)
        self.bind_drag_events(drag_label)

        # Checkbox
        select_var = tk.BooleanVar(value=selected)
        chk = ttk.Checkbutton(frame, variable=select_var)
        chk.grid(row=0, column=1, padx=5)

        # File label
        lbl = ttk.Label(frame, text=psa_file, anchor="w")
        lbl.grid(row=0, column=2, padx=5, sticky="ew")

        # Dropdown
        executable_dropdown = ttk.Combobox(
            frame,
            values=["Select Executable Path"] + executables,
            width=25
        )
        executable_dropdown.set(executable if executable else "Select Executable Path")
        executable_dropdown.grid(row=0, column=3, padx=5)

        # Disable scrolling on dropdown
        disable_combobox_scroll(executable_dropdown)

        #allow scrolling over combox
        allow_canvas_scroll_over_combobox(executable_dropdown, self.canvas)

        # Bind drag to entire row (handle + label)
        for w in (frame, lbl):
            self.bind_drag_events(w)

        # Make columns scale properly
        frame.grid_columnconfigure(2, weight=5)
        frame.grid_columnconfigure(3, weight=0)
        frame.grid_columnconfigure(0, weight=0)
        frame.grid_columnconfigure(1, weight=0)

        self.psa_frames.append((frame, psa_file, executable_dropdown, select_var))


    def rebuild_frames(self):
        for frame, *_ in self.psa_frames:
            frame.tkraise()


psa_files_frame = ScrollablePSAList(root)

# Input/output section (rows 0-3) stays the same
root.grid_columnconfigure(0, weight=0)  # labels
root.grid_columnconfigure(1, weight=1)  # entries

# ---------------- Scrollable box section ----------------
# Create a container frame that spans all columns
psa_container = ttk.Frame(root)
psa_container.grid(row=4, column=0, columnspan=3, sticky="nsew", pady=10)
root.grid_rowconfigure(4, weight=1)

# Center the scrollable box inside the container using pack
psa_files_frame = ScrollablePSAList(psa_container)
psa_files_frame.pack(padx=20, pady=5, fill="both", expand=True)  # Set expand=True here
psa_files_frame.config(width=600)

# Enable mouse/touchpad scrolling
bind_mouse_scroll(psa_files_frame.scrollable_frame, psa_files_frame.canvas)

# ---------------- Buttons section ----------------
# Place buttons in the grid, centered in row 5
root.grid_rowconfigure(5, weight=0)  # Make sure the button row doesn't expand

# Save Configuration Button
ttk.Button(root, text="Save Configuration", command=save_config).grid(row=5, column=0, padx=10, pady=20)

# Process Data Button
ttk.Button(root, text="Process Data", command=process_data).grid(row=5, column=1, padx=10, pady=20)

# Load Configuration Button
ttk.Button(root, text="Load Configuration", command=load_config).grid(row=5, column=2, padx=10, pady=20)

# Center the buttons horizontally in column 1 by setting their columnspan

sv_ttk.set_theme("dark")

# Ensure the load_last_used_config function is called when the app starts
def start_application():
    load_last_used_config()  # Try loading the last used config on startup

    # After loading the config, start the main event loop
    root.mainloop()

# Main entry point
if __name__ == "__main__":
    start_application()



