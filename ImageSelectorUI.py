import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel, Label
from tkinter.ttk import Progressbar
from PIL import Image
from PIL import ImageDraw
import os

class WellPlateSelector:
    def __init__(self, root):
        self.root = root
        self.root.title("96 Well Plate Image Collage Maker")

        self.directory_path = tk.StringVar()
        self.selected_channel = tk.StringVar(value="CH1")
        self.well_vars = {}
        self.use_filler_tile = tk.BooleanVar(value=True)  # Default to "on"


        # Configure grid layout for even spacing
        for i in range(14):  # Configuring 14 columns for even spacing
            root.columnconfigure(i, weight=1)

        # Directory input
        tk.Label(root, text="Image Directory:").grid(row=0, column=1, columnspan=2, sticky="e")
        tk.Entry(root, textvariable=self.directory_path, width=50).grid(row=0, column=3, columnspan=8, sticky="we")
        tk.Button(root, text="Browse", command=self.browse_directory).grid(row=0, column=11, columnspan=2, sticky="w")

        # Channel selection
        tk.Label(root, text="Select Channel:").grid(row=1, column=1, columnspan=2, sticky="e")
        channels = ["CH1", "CH2", "CH3", "Overlay"]
        tk.OptionMenu(root, self.selected_channel, *channels).grid(row=1, column=3, columnspan=8, sticky="we")

        # Select All Wells button
        tk.Button(root, text="Select All Wells", command=self.toggle_all_wells).grid(row=3, column=1, columnspan=1,
                                                                                     sticky="ew", padx=5, pady=5)

        # Filler Tiles toggle
        tk.Checkbutton(root, text="Use Filler Tile for Missing Images", variable=self.use_filler_tile).grid(row=2,
                                                                                                            column=2,
                                                                                                            columnspan=10,
                                                                                                            sticky="ew",
                                                                                                            padx=5,
                                                                                                            pady=5)
        # Row selection buttons
        for row in range(8):
            tk.Button(root, text=f"Select Row {chr(65 + row)}", command=lambda r=row: self.toggle_row(r)).grid(row=row+4, column=1, columnspan=2, sticky="ew", padx=5, pady=5)

        # Column selection buttons
        for col in range(12):
            tk.Button(root, text=f"Select Col {col+1:02}", command=lambda c=col: self.toggle_column(c)).grid(row=3, column=col+3, sticky="ew", padx=2, pady=2)

        # Well selector grid
        for row in range(8):
            for col in range(12):
                well_id = f"{chr(65 + row)}{col + 1:02}"
                var = tk.BooleanVar()
                self.well_vars[well_id] = var
                tk.Checkbutton(root, text=well_id, variable=var).grid(row=row+4, column=col+3, padx=2, pady=2)

        # Action buttons
        tk.Button(root, text="Create Collage", command=self.create_collage).grid(row=12, column=0, columnspan=14, sticky="ew", padx=5, pady=10)

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.directory_path.set(os.path.abspath(directory))

    def well_to_xy_mapping(self, well):
        row = ord(well[0].upper()) - ord('A')
        col = int(well[1:]) - 1
        well_number = row * 12 + col + 1
        return f"XY{well_number:02}"

    def create_collage(self):
        # Show the popup window
        popup = Toplevel(self.root)
        popup.title("Creating Collage")
        Label(popup, text="Creating the collage... This may take a few moments! -Alex C.").pack(padx=20, pady=10)

        # Progress bar
        progress = Progressbar(popup, orient="horizontal", length=300, mode="determinate")
        progress.pack(padx=20, pady=10)

        # Label to show current processing image
        status_label = Label(popup, text="")
        status_label.pack(padx=20, pady=10)

        selected_wells = [well for well, var in self.well_vars.items() if var.get()]
        if not selected_wells:
            popup.destroy()  # Close the popup if no wells are selected
            messagebox.showwarning("No Wells Selected", "Please select at least one well.")
            return

        directory = self.directory_path.get()
        if not directory:
            popup.destroy()  # Close the popup if no directory is selected
            messagebox.showerror("No Directory", "Please specify the directory where the images are stored.")
            return

        selected_channel = self.selected_channel.get()
        images = {}
        max_width = 0
        max_height = 0

        # Determine selected rows and columns
        selected_rows = sorted(set(well[0] for well in selected_wells))
        selected_cols = sorted(set(int(well[1:]) for well in selected_wells))

        try:
            progress["maximum"] = len(selected_wells)  # Set progress bar maximum
            for i, well in enumerate(selected_wells):
                xy_folder = self.well_to_xy_mapping(well)
                img_dir = os.path.join(directory, xy_folder)
                img_found = False
                if os.path.exists(img_dir):
                    for img_file in os.listdir(img_dir):
                        if selected_channel in img_file:
                            img_path = os.path.join(img_dir, img_file)
                            img = Image.open(img_path)
                            images[well] = img
                            max_width = max(max_width, img.width)
                            max_height = max(max_height, img.height)
                            img_found = True
                            break

                if not img_found and self.use_filler_tile.get():
                    # Placeholder for filler image to be created later
                    images[well] = None

                # Update status label with the current file being processed and progress percentage
                percent_complete = int((i + 1) / len(selected_wells) * 100)
                status_label.config(text=f"Processing {well} ({percent_complete}%)")
                progress["value"] = i + 1  # Update progress bar
                popup.update()  # Update the popup to reflect progress

            # Create filler images with correct dimensions
            for well in selected_wells:
                if images[well] is None:
                    filler_img = Image.new('RGB', (max_width, max_height), color='black')
                    draw = ImageDraw.Draw(filler_img)
                    text = "Missing Image File"
                    text_width, text_height = draw.textsize(text)
                    text_x = (max_width - text_width) // 2
                    text_y = (max_height - text_height) // 2
                    draw.text((text_x, text_y), text, fill="white")
                    images[well] = filler_img

            if not images:
                popup.destroy()  # Close the popup if no images found
                messagebox.showerror("No Images Found", "No images found for the selected wells and channel.")
                return

            # Collage creation logic
            grid_rows = len(selected_rows)
            grid_cols = len(selected_cols)
            collage_width = grid_cols * max_width
            collage_height = grid_rows * max_height
            collage = Image.new('RGB', (collage_width, collage_height))

            # Sort wells for placement
            sorted_wells = sorted(selected_wells, key=lambda w: (ord(w[0]), int(w[1:])))

            for well in sorted_wells:
                row_index = selected_rows.index(well[0])  # Get the row index in selected rows
                col_index = selected_cols.index(int(well[1:]))  # Get the column index in selected columns
                x_offset = col_index * max_width
                y_offset = row_index * max_height
                collage.paste(images[well], (x_offset, y_offset))

            # Update the popup message once the collage is completed
            status_label.config(text="Collage Completed! It will appear on your screen in just a moment 😄 - Alex C.")
            progress["value"] = len(selected_wells)
            popup.update()

            popup.after(1000, popup.destroy)  # Close the popup after 1 second
            collage.show()

        except Exception as e:
            popup.destroy()  # Ensure popup is closed in case of error
            messagebox.showerror("Error", f"An error occurred: {e}")


    def toggle_row(self, row):
        row_state = all(self.well_vars[f"{chr(65 + row)}{col + 1:02}"].get() for col in range(12))
        for col in range(12):
            well_id = f"{chr(65 + row)}{col + 1:02}"
            self.well_vars[well_id].set(not row_state)

    def toggle_column(self, col):
        col_state = all(self.well_vars[f"{chr(65 + row)}{col + 1:02}"].get() for row in range(8))
        for row in range(8):
            well_id = f"{chr(65 + row)}{col + 1:02}"
            self.well_vars[well_id].set(not col_state)

    def toggle_all_wells(self):
        all_selected = all(var.get() for var in self.well_vars.values())
        for var in self.well_vars.values():
            var.set(not all_selected)

if __name__ == "__main__":
    root = tk.Tk()
    app = WellPlateSelector(root)
    root.mainloop()