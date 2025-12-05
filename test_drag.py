import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("Reorder PSA Files by Dragging")

psa_files_frame = tk.Frame(root)
psa_files_frame.pack(fill="both", expand=True, padx=10, pady=10)

psa_frames = []

def on_drag_start(event):
    widget = event.widget
    widget.lift()
    widget.start_y = event.y_root

def on_drag_motion(event):
    widget = event.widget
    dy = event.y_root - widget.start_y
    widget.place_configure(y=widget.winfo_y() + dy)
    widget.start_y = event.y_root

    # Check overlap with other frames
    for other in psa_frames:
        if other is widget:
            continue
        if abs(widget.winfo_y() - other.winfo_y()) < 20:
            i = psa_frames.index(widget)
            j = psa_frames.index(other)
            psa_frames[i], psa_frames[j] = psa_frames[j], psa_frames[i]
            rebuild_frames()
            break

def on_drag_stop(event):
    rebuild_frames()

def rebuild_frames():
    for i, frame in enumerate(psa_frames):
        frame.place_forget()
        frame.place(relx=0, rely=0, relwidth=1, y=i * 40, height=40)

# Create example PSA frames
for i in range(5):
    frame = tk.Frame(psa_files_frame, relief="raised", bd=2, bg="#444")
    label = tk.Label(frame, text=f"PSA File {i+1}", fg="white", bg="#444")
    label.pack(side="left", padx=5)

    dropdown = ttk.Combobox(frame, values=["Exec1", "Exec2"], width=15)
    dropdown.set("Select Executable Path")
    dropdown.pack(side="left", padx=5)

    chk = tk.Checkbutton(frame, text="Select", bg="#444", fg="white")
    chk.pack(side="left", padx=5)

    frame.bind("<Button-1>", on_drag_start)
    frame.bind("<B1-Motion>", on_drag_motion)
    frame.bind("<ButtonRelease-1>", on_drag_stop)

    psa_frames.append(frame)

rebuild_frames()

root.geometry("400x300")
root.mainloop()