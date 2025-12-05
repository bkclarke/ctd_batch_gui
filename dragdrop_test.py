import tkinter as tk


class DraggableList(tk.Frame):
    def __init__(self, master, items):
        super().__init__(master)
        self.pack(fill="both", expand=True)

        self.rows = []          # List of row frames in current order
        self.drag_widget = None
        self.placeholder = None
        self.offset_y = 0

        for text in items:
            self.add_row(text)

    def add_row(self, text):
        frame = tk.Frame(self, bd=1, relief="ridge", bg="#e0e0e0", padx=10, pady=5)
        label = tk.Label(frame, text=text, bg="#e0e0e0")
        label.pack()

        frame.pack(fill="x", pady=3)

        # Bind to frame and label
        for widget in (frame, label):
            widget.bind("<ButtonPress-1>", self.on_press)
            widget.bind("<B1-Motion>", self.on_drag)
            widget.bind("<ButtonRelease-1>", self.on_release)

        self.rows.append(frame)

    def on_press(self, event):
        # Normalize: always drag the frame
        self.drag_widget = event.widget
        while not isinstance(self.drag_widget, tk.Frame):
            self.drag_widget = self.drag_widget.master

        # Create placeholder where widget was
        self.placeholder = tk.Frame(self, height=self.drag_widget.winfo_height())
        self.placeholder.pack(fill="x", pady=3)

        # Move dragged widget to top-level overlay
        self.drag_widget.lift()
        self.drag_widget.update_idletasks()
        self.drag_width = self.drag_widget.winfo_width()
        self.drag_height = self.drag_widget.winfo_height()
        self.drag_widget.place(
            in_=self,
            x=0,
            y=self.drag_widget.winfo_y(),
            width=self.drag_width,
            height=self.drag_height
        )

        self.offset_y = event.y  # Pointer offset inside frame

    def on_drag(self, event):
        if not self.drag_widget:
            return

        # Move widget under pointer
        new_y = event.y_root - self.winfo_rooty() - self.offset_y
        self.drag_widget.place_configure(y=new_y)

        self.update_placeholder(new_y)

    def update_placeholder(self, widget_y):
        positions = []

        for row in self.rows:
            if row is self.drag_widget:
                continue
            
            # Skip destroyed widgets to avoid TclError
            if not row.winfo_exists():
                continue

            try:
                y = row.winfo_y()
            except tk.TclError:
                continue  # Window path invalid → skip safely

            positions.append((row, y))

        # Determine where to put the placeholder
        for row, y in positions:
            if widget_y < y:
                self.placeholder.pack_forget()
                self.placeholder.pack(before=row, fill="x", pady=3)
                return

        # If not inserted before anything, place at the end
        self.placeholder.pack_forget()
        self.placeholder.pack(fill="x", pady=3)

    def on_release(self, event):
        if not self.drag_widget:
            return

        # Remove from overlay
        self.drag_widget.place_forget()

        # Insert back into correct position
        self.drag_widget.pack_forget()
        self.drag_widget.pack(before=self.placeholder, fill="x", pady=3)

        # Update internal row order
        self.update_row_order()

        # Remove placeholder
        self.placeholder.destroy()
        self.placeholder = None

        self.drag_widget = None

    def update_row_order(self):
        """Rebuild self.rows in the visual order."""
        ordered = []
        for child in self.winfo_children():
            if isinstance(child, tk.Frame):  # ignore placeholder
                ordered.append(child)
        self.rows = ordered


# ---------------- DEMO ----------------
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("300x300")
    root.title("Draggable Rows Demo")

    items = ["PSA File A", "PSA File B", "PSA File C", "PSA File D"]
    DraggableList(root, items)

    root.mainloop()


