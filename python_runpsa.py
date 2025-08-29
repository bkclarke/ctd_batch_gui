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
LAST_USED_CONFIG_FILE = os.path.join(BASE_DIR, "last_used_config.json")
print(f"Using last used config file at: {LAST_USED_CONFIG_FILE}")

# Initialize the GUI
root = tk.Tk()

# Global variables for the configuration values
raw_files_var = tk.StringVar()
psa_dir_var = tk.StringVar()
executables_dir_var = tk.StringVar()
output_file_var = tk.StringVar()
executables = []
sbedataprocessing_exe = ""

# Create an empty list to store the frames for each PSA file
psa_frames = []
psa_files_frame = tk.Frame(root)  # Initialize psa_files_frame as a Tkinter frame

def update_psa_files():
    """
    Update all .psa files with the correct InstrumentPath, InputDir, and OutputDir.
    Resolves relative paths to absolute paths and escapes backslashes.
    """
    updated_files = []
    errors = []

    # Get raw files from GUI variable
    raw_files = raw_files_var.get().split(";")
    raw_files = [os.path.abspath(f.strip('"')) for f in raw_files if f]

    # Get PSA and output directories
    psa_dir = os.path.abspath(psa_dir_var.get())
    output_file_dir = os.path.abspath(output_file_var.get())

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
                psa_path = os.path.abspath(os.path.join(psa_dir, psa_file))

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
                input_dir = os.path.abspath(input_dir).replace("\\", "/")
                output_file_dir_clean = os.path.abspath(output_file_dir).replace("\\", "/")
                xmlcon_file = f"{base_name}.XMLCON"
                instrument_path = os.path.abspath(os.path.join(raw_dir, xmlcon_file)).replace("\\", "/")

                try:
                    with open(psa_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Update InputDir and OutputDir
                    content = re.sub(r'\s*<InputDir\s+value="[^"]*"\s*/>',
                                    f'  <InputDir value="{input_dir}" />',
                                    content, flags=re.IGNORECASE)

                    content = re.sub(r'\s*<OutputDir\s+value="[^"]*"\s*/>',
                                    f'  <OutputDir value="{output_file_dir_clean}" />',
                                    content, flags=re.IGNORECASE)
                    
                    # Update InstrumentPath only if it exists
                    if re.search(r'<InstrumentPath value=".*?" ?/>', content):
                        content = re.sub(r'<InstrumentPath value=".*?" ?/>',
                                        f'<InstrumentPath value="{instrument_path}" />', content)

                    with open(psa_path, "w", encoding="utf-8") as f:
                        f.write(content)

                    updated_files.append(psa_path)

                except Exception as e:
                    errors.append(f"{psa_path}: {e}")

    # Show updated files window
    if updated_files:
        show_updated_files_window(updated_files)

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
    raw_files = filedialog.askopenfilenames(
        title="Select Raw .hex File",
        filetypes=[("HEX files", "*.hex")]
    )
    if raw_files:
        # Join with a safe delimiter (semicolon won’t conflict with spaces in paths)
        raw_files_var.set(";".join(raw_files))
        print("Selected raw files:", raw_files)

# Function to select the directory containing .psa files
def select_psa_directory():
    print("browse clicked")
    dir_path = filedialog.askdirectory(title="Select Directory Containing .psa Files")
    if dir_path:
        psa_dir_var.set(dir_path)
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

    for psa_file, executable, _ in selected_psa_file:
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


def load_psa_files(psa_dir):
    global psa_dir_path  # Ensure we can check/set the path when necessary

    psa_dir_path = psa_dir  # Set the global PSA directory

    # Clear previous frames
    for frame in psa_frames:
        frame[0].destroy()  # Destroy only the frame widget (frame[0])

    psa_frames.clear()  # Clear the list of frames to avoid reusing old frames

    # List all .psa files in the selected directory
    psa_files = [f for f in os.listdir(psa_dir) if f.endswith('.psa')]

    if not psa_files:
        messagebox.showwarning("No Files Found", "No .psa files found in the selected directory.")
        return

    # Create a frame for each PSA file
    for idx, psa_file in enumerate(psa_files):
        psa_frame = tk.Frame(psa_files_frame)
        psa_frame.grid(row=idx, sticky="ew", pady=5)

        # PSA file name label
        psa_label = tk.Label(psa_frame, text=psa_file, width=30)
        psa_label.grid(row=0, column=0, padx=5)

        executable_dropdown = ttk.Combobox(psa_frame, values=["Select Executable Path"] + executables)
        executable_dropdown.grid(row=0, column=1, padx=5)

        # Order number entry (initially 1)
        order_entry = tk.Entry(psa_frame, width=5)
        order_entry.insert(0, str(idx + 1))  # Default order number is idx + 1
        order_entry.grid(row=0, column=2, padx=5)

        # Select/Deselect checkbox
        select_var = tk.BooleanVar(value=True)  # Default is selected
        select_checkbox = ttk.Checkbutton(psa_frame, text="Run", variable=select_var, style="TCheckbutton")
        select_checkbox.grid(row=0, column=3, padx=5)

        # Edit PSA Button to open the file in SBEDataprocessing
        edit_button = ttk.Button(psa_frame, text="Edit PSA", command=lambda psa_file=psa_file, psa_dir=psa_dir, executable_dropdown=executable_dropdown: open_in_sbedataprocessing(psa_dir, psa_file, executable_dropdown.get()))
        edit_button.grid(row=0, column=4, padx=5)

        # Store the widgets in a tuple for later use
        psa_frames.append((psa_frame, executable_dropdown, order_entry, select_var, select_checkbox, edit_button))

# Function to load the last used configuration (only at the start of the app)
def load_last_used_config():
    print(LAST_USED_CONFIG_FILE)
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
        print(f"Saved last used config file path: {file_path} to {LAST_USED_CONFIG_FILE}")
    except Exception as e:
        print(f"Error saving last used config: {e}")

def load_config_to_gui(config):
    # Update the GUI with values from the loaded configuration
    # Load list of raw files
    raw_files = config.get("raw_files", [])  # Make sure your saved config uses this key
    raw_file_var.clear()
    raw_file_var.extend(raw_files)

    # Update the label displaying selected files
    if raw_files:
        raw_file_display_label.config(text=", ".join(os.path.basename(f) for f in raw_files))
    else:
        raw_file_display_label.config(text="No files selected")
    
    psa_dir_var.set(config.get("psa_dir", ""))
    executables_dir_var.set(config.get("executables_dir", ""))
    output_file_var.set(config.get("output_file", ""))

    # Load executables list
    global executables
    executables = config.get("executables", [])

    # Load PSA files and their respective data
    load_psa_files(config["psa_dir"])

    # Update PSA file data from the config
    for psa_data in config["psa_files"]:
        for psa_frame, executable_dropdown, order_entry, select_var, select_checkbox, *_ in psa_frames:  # Update here
            # Check if the psa_frame has the correct PSA file
            if psa_frame.winfo_children()[0].cget("text") == psa_data["psa_file"]:
                # Update the executable dropdown
                executable = psa_data["executable"]
                executable_name = os.path.basename(executable) if executable else "Select Executable Path"
                executable_dropdown.set(executable_name)

                # Update the order entry
                order_entry.delete(0, tk.END)
                order_entry.insert(0, psa_data["order"])

                # Update the checkbox
                select_var.set(psa_data["selected"])  # Set the checkbox state

                # Update the Checkbutton state
                if select_var.get():
                    select_checkbox.state(["selected"])
                else:
                    select_checkbox.state(["!selected"])


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

# Function to save the current configuration to a user-selected config file
def save_config():
    # Ask the user for the file path where the configuration should be saved
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
    if not file_path:
        return  # If no file is selected, exit the function

    config = {
        "raw_files": raw_files_var.get().strip("{}").split(),
        "psa_dir": psa_dir_var.get(),
        "executables_dir": executables_dir_var.get(),
        "executables": executables,
        "output_file": output_file_var.get(),  # Add output file path
        "psa_files": []
    }

    for psa_frame, executable_dropdown, order_entry, select_var, select_checkbox, _ in psa_frames:
        psa_file = psa_frame.winfo_children()[0].cget("text")  # Get the actual string
        executable = executable_dropdown.get()
        order = order_entry.get()

        # Save the executable file path instead of just the name
        executable_path = ""
        if executable != "Select Executable Path":
            executable_path = os.path.join(executables_dir_var.get(), executable)

        selected = select_var.get()

        config["psa_files"].append({
            "psa_file": psa_file,
            "executable": executable_path,
            "order": order,
            "selected": selected
        })

    try:
        with open(file_path, "w") as f:
            json.dump(config, f, indent=4)
        messagebox.showinfo("Configuration Saved", "Your configuration has been saved successfully!")

        # Save the path of the saved config as the new "last used config file"
        print(file_path)
        save_last_used_config(file_path)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to save configuration: {e}")
        

# Main processing function
def process_data():
    print(f"raw_file_var = {raw_file_var}")
    raw_files = raw_files_var.get().split(";")
    raw_files = [os.path.normpath(f.strip('"')) for f in raw_files if f]
    print("Normalized raw files:", raw_files)
    psa_dir = psa_dir_var.get()
    output_file_dir = output_file_var.get()

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
    for psa_frame, executable_dropdown, order_entry, select_var, *_ in psa_frames:
        if select_var.get():
            selected_executable = executable_dropdown.get()

            psa_file = psa_frame.winfo_children()[0].cget("text")

            if selected_executable == "Select Executable Path":
                messagebox.showerror("Error", f"Please select an executable for {psa_file}.")
                return
            try:
                order = int(order_entry.get())
            except ValueError:
                messagebox.showerror("Error", f"Invalid order number for {psa_file}. Please enter a valid integer.")
                return
            
            executable_path = os.path.join(executables_dir_var.get(), selected_executable) if selected_executable != "Select Executable Path" else ""
            selected_psa_files.append((psa_file, executable_path, order))

    if not selected_psa_files:
        messagebox.showerror("Error", "Please select at least one .psa file to process.")
        return

    selected_psa_files.sort(key=lambda x: x[2])

    for raw_file in raw_files:
        base_name = os.path.splitext(os.path.basename(raw_file))[0]
        output_file = f"{base_name}.cnv"

        for psa_file, executable, _ in selected_psa_files:
            psa_file_path = os.path.join(psa_dir, psa_file)
            print(f"Running {executable} for {psa_file} with raw file {raw_file}")

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

def select_raw_files():
    files = filedialog.askopenfilenames(title="Select Raw .hex Files", filetypes=[("HEX files", "*.hex")])
    if files:
        # Update the StringVar for processing
        raw_files_var.set(";".join(files))

        # Update display label
        raw_file_display_label.config(
            text=", ".join(os.path.basename(f) for f in files)
        )

        print("Selected raw files:", files)

# Layout (unchanged, just for reference)
tk.Label(root, text="Select Raw .hex File:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
raw_file_display_label = tk.Label(root, text="No files selected", anchor="w", bg="#2b2b2b", fg="white")
raw_file_display_label.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
ttk.Button(root, text="Browse", command=select_raw_files).grid(row=0, column=2, padx=10, pady=5)

tk.Label(root, text="Select Directory Containing .psa Files:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
tk.Entry(root, textvariable=psa_dir_var, width=50).grid(row=1, column=1, padx=10, pady=5, sticky="ew")
ttk.Button(root, text="Browse", command=select_psa_directory).grid(row=1, column=2, padx=10, pady=5)

tk.Label(root, text="Select Directory Containing Executables:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
tk.Entry(root, textvariable=executables_dir_var, width=50).grid(row=2, column=1, padx=10, pady=5, sticky="ew")
ttk.Button(root, text="Browse", command=select_executables_directory).grid(row=2, column=2, padx=10, pady=5)

tk.Label(root, text="Select Output File Directory:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
tk.Entry(root, textvariable=output_file_var, width=50).grid(row=3, column=1, padx=10, pady=5, sticky="ew")
ttk.Button(root, text="Browse", command=lambda: output_file_var.set(filedialog.askdirectory(title="Select Output Directory"))).grid(row=3, column=2, padx=10, pady=5)

ttk.Button(root, text="Update PSA Files", command=update_psa_files).grid(row=4, column=2, padx=10, pady=10, sticky="ew")

# Frame to hold PSA entries
psa_files_frame = tk.Frame(root)
psa_files_frame.grid(row=5, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

# Process Data Button
ttk.Button(root, text="Process Data", command=process_data).grid(row=6, column=1, padx=10, pady=20)

# Save Configuration Button
ttk.Button(root, text="Save Configuration", command=save_config).grid(row=7, column=0, padx=10, pady=20)

# Load Configuration Button
ttk.Button(root, text="Load Configuration", command=load_config).grid(row=7, column=2, padx=10, pady=20)


sv_ttk.set_theme("dark")

# Ensure the load_last_used_config function is called when the app starts
def start_application():
    load_last_used_config()  # Try loading the last used config on startup

    # After loading the config, start the main event loop
    root.mainloop()

# Main entry point
if __name__ == "__main__":
    start_application()



