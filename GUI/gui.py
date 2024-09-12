import logging
logger = logging.getLogger(__name__)

import tkinter as tk
import tkinter.messagebox as msgbox
from tkinter import ttk

from helpers import *
from handler import *

ROOT_DIRECTORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = 1.0

default_config = {
    "lora_dir": r"S:\SD_Archive\models\Lora\PONY",
    "pngs_dir": r"X:\CardArchive\LoraCards\_ProcessingPNGs",
    "output_dir": r"S:\LoraIntermediary"
}

#region LoraOrganizerApp
class ModelOrganizerApp:
    """GUI for Lora Organization"""
    def __init__(self, root: tk.Tk):      
        self.root = root
        self.root.title(f"Model Organizer v{VERSION}")
        self.root.geometry("1920x1080")
        self.config_path = os.path.join(ROOT_DIRECTORY, "config.json")
        self.config = self.load_config()
        self.lora_dir = self.config.get("lora_dir", None)
        self.pngs_dir = self.config.get("pngs_dir", None)
        self.output_dir = self.config.get("output_dir", None)

        info_handler = INFO(self.lora_dir, self.pngs_dir, self.output_dir)

        self.built_png_dict = info_handler.build_png_dictionary()
        self.built_lora_dict = info_handler.build_lora_dictionary()

        self.create_menu()
        self.create_context_menu()
        self.create_tree()
        self.set_keybinds()
        self.populate_tree(self.built_lora_dict, self.built_png_dict)





    #region Configuration
    def initialize_config(self) -> dict:
        self.save_config(default_config)
        return default_config
        
    def load_config(self) -> dict:
        if os.path.exists(self.config_path):
            config = load_json_file(self.config_path, default={}, relative_path=False)
        else:
            config = self.initialize_config()

        return config

    def save_config(self, config: dict) -> None:
        save_json_file(self.config_path, config, relative_path=False)

    #endregion


    #region Setup Functions
    def create_tree(self):
        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True)

        vertical_scrollbar = ttk.Scrollbar(frame, orient="vertical")
        vertical_scrollbar.pack(side="right", fill="y")

        self.tree = ttk.Treeview(frame, columns=("definition", "lora_path", "png_path"), show="tree headings", yscrollcommand=vertical_scrollbar.set)

        # Define column properties (widths and stretchable behavior)
        self.tree.column("#0", width=300, stretch=False)  # Main column (Lora name)
        self.tree.column("definition", width=1920, stretch=True)  # PNG directory path
        self.tree.column("lora_path", width=100, stretch=True)  # Lora file path
        self.tree.column("png_path", width=100, stretch=True)  # PNG directory path
        
        # Set headings (this is optional, but useful for understanding columns)
        self.tree.heading("#0", text="Lora Name", anchor="w")
        self.tree.heading("lora_path", text="Lora Path", anchor="w")
        self.tree.heading("png_path", text="PNG Path", anchor="w")
        self.tree.heading("definition", text="Lora Definition", anchor="w")

        self.tree.pack(side="left", fill="both", expand=True)

        vertical_scrollbar.config(command=self.tree.yview)

    def populate_tree(self, built_lora_dict, built_png_dict):
        """Populate the treeview with categories, qualities, and Lora names."""
        full_definitions = load_json_file("./AliDictionaries.json")
        lora_definitions = full_definitions.get("lora_dictionary",{})
        self.tree.delete(*self.tree.get_children())

        for category, qualities in built_lora_dict.items():
            category_id = self.tree.insert("", "end", text=category)  # Insert category node
            for quality, loras in qualities.items():
                quality_id = self.tree.insert(category_id, "end", text=quality)  # Insert quality node
                for lora in loras:
                    lora_path = lora[1]
                    png_dir_path = get_path_by_lora_name(built_png_dict, lora[0])
                    self.tree.insert(quality_id, "end", text=lora[0], values=(lora_definitions.get(lora[0], None), lora_path, png_dir_path))  # Insert Lora name

    def create_menu(self):
        """Create a File menu at the top of the window."""
        menubar = tk.Menu(self.root)

        # Create the File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Repopulate Tree", command=self.repopulate_tree)
        file_menu.add_command(label="Log Dicts", command=self.log_dicts)

        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Add the File menu to the menubar
        menubar.add_cascade(label="File", menu=file_menu)

        # Display the menubar
        self.root.config(menu=menubar)   

    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Open Lora File", command=self.open_lora_parent_directory)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Open PNG Directory", command=self.open_png_directory)

    def set_keybinds(self):
        # Root binds
        self.root.bind("<Control-f>", self.on_ctrl_f)
        self.root.bind("<Escape>", self.on_escape)

        # Tree binds
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Alt-Double-1>", self.on_alt_double_click)
        self.tree.bind("<Button-3>", self.on_right_click)
    #endregion



    #region Keybinds


    def on_double_click(self, event):
        self.open_lora_parent_directory()

    def on_alt_double_click(self, event):
        self.open_png_directory()

    def on_right_click(self, event):
        self.show_context_menu(event)

    def on_ctrl_f(self, event):
        self.open_search_dialog()

    def on_escape(self, event):
        self.root.quit()

    #endregion



    #region Menu Callbacks
    def repopulate_tree(self):
        self.populate_tree(self.built_lora_dict, self.built_png_dict)

    def log_dicts(self):
        actor = ACT("LogDicts",{"data": [self.built_lora_dict, self.built_png_dict]})
        actor.act()
    #endregion





    #region Context Callbacks
    def show_context_menu(self, event):
        """Display the right-click context menu."""
        # Get the selected item on right-click
        item_id = self.tree.identify_row(event.y)
        if item_id:
            self.tree.selection_set(item_id)
            self.context_menu.post(event.x_root, event.y_root)

    #endregion





    #region Search Callbacks
    def open_search_dialog(self, event=None):
        """Open a search dialog when Ctrl+F is pressed."""
        # Create a Toplevel window (popup)
        search_window = tk.Toplevel(self.root)
        search_window.title("Search")
        search_window.geometry("150x100")

        # Label and Entry for the search query
        tk.Label(search_window, text="Search Lora Name:").pack(pady=5)
        search_entry = tk.Entry(search_window)
        search_entry.pack(pady=5)
        search_entry.focus_set()

        search_entry.bind("<Return>", lambda event: self.search_and_redraw(search_entry.get()))
        # Search button
        tk.Button(search_window, text="Search", command=lambda: self.search_and_redraw(search_entry.get())).pack(pady=5)

    def search_and_redraw(self, search_query):
        """Search for the query and redraw the Treeview with only the matches."""
        # Filter the built_lora_dict to only include matching Lora names
        filtered_lora_dict = {}
        # Clear any existing items from the Treeview
        self.tree.delete(*self.tree.get_children())
        for category, qualities in self.built_lora_dict.items():
            matching_qualities = {}
            for quality, loras in qualities.items():
                matching_loras = [lora for lora in loras if search_query.lower() in lora[0].lower()]
                if matching_loras:
                    matching_qualities[quality] = matching_loras
            if matching_qualities:
                filtered_lora_dict[category] = matching_qualities

        # Repopulate the Treeview with the filtered data
        self.populate_tree(filtered_lora_dict, self.built_png_dict)

    def search_in_tree(self, search_query):
        """Search for the query in the Treeview and highlight the matching items."""
        # Clear existing selection
        self.tree.selection_remove(self.tree.selection())
        
        # Traverse all items in the Treeview
        for item in self.tree.get_children():
            self.search_in_subtree(item, search_query)

    def search_in_subtree(self, parent, search_query):
        """Recursively search in the subtree rooted at 'parent'."""
        # Check if the parent's text matches the search query
        if search_query.lower() in self.tree.item(parent, "text").lower():
            self.tree.selection_add(parent)  # Highlight the matching item
            self.tree.see(parent)  # Make sure it's visible
        
        # Recursively search all children of this parent
        for child in self.tree.get_children(parent):
            self.search_in_subtree(child, search_query)
    #endregion





    #region Misc Callbacks
    def open_png_directory(self):
        selected_item = self.tree.selection()

        item_text = self.tree.item(selected_item, "text")
        file_path = self.tree.item(selected_item, "values")[2] if self.tree.item(selected_item, "values") else None

        if item_text and file_path:
            if not open_to_file(file_path):
                msgbox.showinfo("Failed", f"No PNG directory exists for: {item_text}")

    def open_lora_parent_directory(self):
        # Get the selected item
        selected_item = self.tree.selection()

        # Get the item's text
        item_text = self.tree.item(selected_item, "text")
        file_path = self.tree.item(selected_item, "values")[1] if self.tree.item(selected_item, "values") else None

        if item_text and file_path:
            if not open_to_file(file_path):
                msgbox.showinfo("Failed", f"No file exists for: {item_text}")

    #endregion