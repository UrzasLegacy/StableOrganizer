import logging
logger = logging.getLogger(__name__)

import tkinter as tk
import tkinter.messagebox as msgbox
from tkinter import ttk

from helpers import *
from handlers import InfoHandler, ActionHandler

ROOT_DIRECTORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = 1.0

default_config = {
    "ckpt_processing_dir": r"X:\SD_X\models\checkpoints\_IN",
    "lora_processing_dir": r"S:\SD_Archive\models\Lora\PONY\__LoraStaging",
    "lora_png_dir": r"X:\CardArchive\LoraCards\_ProcessingPNGs",

    "png_dir": r"X:\CardArchive",
    "ckpt_dir": r"X:\SD_X\models\checkpoints",
    "lora_dir": r"S:\SD_Archive\models\Lora\PONY",
    "output_dir": r"S:\LoraIntermediary",
}

#region StableOrganizerApp
class StableOrganizerApp:
    """GUI for Model and Output Organization"""
    def __init__(self, root: tk.Tk):      
        self.root = root
        self.root.title(f"StableOrganizer v{VERSION}")
        self.root.geometry("1920x1080")
        
        self.config_data = self.setup_config()

        self.info_handler = InfoHandler(self.config_data)
        self.action_handler = ActionHandler(self.config_data)

        self.built_png_dict = self.info_handler.build_png_dictionary()
        self.built_lora_dict = self.info_handler.build_lora_dictionary()


        self.create_menu()
        self.create_context_menu()
        self.create_tree()
        self.set_keybinds()
        self.populate_tree(self.built_lora_dict, self.built_png_dict)


    #region Configuration
    def initialize_config(self) -> dict:
        self.save_config(default_config)
        return default_config

    def get_setting(self, setting):
        return self.config_data.get(setting)
    
    def load_config(self) -> dict:
        if os.path.exists(self.config_path):
            config = load_json_file(self.config_path, default={}, relative_path=False)
        else:
            config = self.initialize_config()
        print(config)
        return config


    def save_config(self, config: dict) -> None:
        save_json_file(self.config_path, config, relative_path=False)
    #endregion Configuration


    #region Setup Functions
    def setup_config(self):
        self.config_path = os.path.join(ROOT_DIRECTORY, "config.json")
        return self.load_config()


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
        self.tree.tag_configure("cyan", background="lightcyan")

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
                    if lora_path and png_dir_path:
                        self.tree.insert(quality_id, "end", text=lora[0], values=(lora_definitions.get(lora[0], None), lora_path, png_dir_path), tags=("cyan",))  # Insert Lora name
                    else:
                        self.tree.insert(quality_id, "end", text=lora[0], values=(lora_definitions.get(lora[0], None), lora_path, png_dir_path))  # Insert Lora name


    def create_menu(self):
        """Create a File menu at the top of the window."""
        menubar = tk.Menu(self.root)

        # Create the File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Repopulate Tree", command=self.repopulate_tree)
        file_menu.add_command(label="Log Dicts", command=self.log_dicts)
        file_menu.add_command(label="Config", command=self.change_config)

        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Add the File menu to the menubar
        menubar.add_cascade(label="File", menu=file_menu)

        # Display the menubar
        self.root.config(menu=menubar)   

    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Open Lora Parent Folder", command=self.open_lora_parent_directory)
        self.context_menu.add_command(label="Open PNG Directory", command=self.open_png_directory)
        self.context_menu.add_separator()
        for quality in QUALITIES:
            self.context_menu.add_command(label=f"Move to {quality}", command=lambda q=quality: self.move_to_quality_directory(q))

        # Create a submenu
        # submenu = tk.Menu(self.context_menu, tearoff=0)
        # submenu.add_command(label="Submenu Item 1", command=lambda x: x)
        # submenu.add_command(label="Submenu Item 2", command=lambda x: x)

        # Add the submenu to the context menu
        # self.context_menu.add_cascade(label="Move To", menu=submenu)


    def set_keybinds(self):
        # Root binds
        self.root.bind("<Control-f>", self.on_ctrl_f)
        self.root.bind("<Escape>", self.on_escape)

        # Tree binds
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Alt-Double-1>", self.on_alt_double_click)
        self.tree.bind("<Button-3>", self.on_right_click)
    #endregion Setup Functions


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
    #endregion Keybinds


    #region Menu Callbacks
    def repopulate_tree(self):
        self.populate_tree(self.built_lora_dict, self.built_png_dict)


    def log_dicts(self):
        self.action_handler.log_dicts(self.built_lora_dict, self.built_png_dict)
    #endregion Menu Callbacks





    #region Context Callbacks
    def show_context_menu(self, event):
        """Display the right-click context menu."""
        # Get the selected item on right-click
        item_id = self.tree.identify_row(event.y)
        if item_id:
            self.tree.selection_set(item_id)
            self.context_menu.post(event.x_root, event.y_root)


    def change_config(self):
        pass



    def move_to_quality_directory(self, quality):
        selected_item = self.tree.selection()
        selected_path = self.get_full_path(selected_item[0])

        category, current_quality, lora_name = selected_path.split('\\')

        item_text = self.tree.item(selected_item, "text")
        item_values = list(self.tree.item(selected_item, "values"))


        current_lora_path = item_values[1]
        current_png_path = item_values[2]

        lora_parent_path = self.get_setting("lora_dir")
        lora_png_parent_path = self.get_setting("lora_png_dir")

        lora_target_path = os.path.join(lora_parent_path, f"{category}_{quality}")
        lora_png_target_path = os.path.join(lora_png_parent_path, f"{category}_{quality}")

        if item_text:
            if current_lora_path != "None":
                self.action_handler.move(current_lora_path, lora_target_path)
                self.built_lora_dict = self.info_handler.build_lora_dictionary()
                item_values[1] = lora_target_path
            if current_png_path != "None":
                print("M:", current_png_path, lora_png_target_path)
                self.action_handler.move(current_png_path, lora_png_target_path)
                self.built_png_dict = self.info_handler.build_png_dictionary()
                item_values[2] = lora_png_target_path
            new_parent = self.find_category_quality_node(category, quality)
            self.move_and_update_item(new_parent, tuple(item_values))
            self.sort_children(new_parent)

    def find_category_quality_node(self, category, quality):
        # Iterate over the tree to find the node corresponding to the target category and quality; create it if necessary
        for _category in self.tree.get_children():  # Get top-level items
            if self.tree.item(_category, 'text') == category:
                for _quality in self.tree.get_children(_category):
                    if self.tree.item(_quality, 'text') == quality:
                        return _quality
                new_quality = self.tree.insert(_category, text=quality)
                return new_quality
        return None

    def sort_children(self, parent_node, reverse=False):
        # Get all children of the parent_node
        children = self.tree.get_children(parent_node)

        # Retrieve (item_id, sort_value) pairs
        children_with_values = [(child, self.tree.item(child, "text")) for child in children]

        # Sort the list of children based on the sort value (alphabetical or numeric)
        children_with_values.sort(key=lambda x: x[1], reverse=reverse)

        # Re-insert the sorted children
        for child_id, _ in children_with_values:
            # Get the item's text and values
            item_text = self.tree.item(child_id, "text")
            item_values = self.tree.item(child_id, "values")
            item_tags = self.tree.item(child_id,"tags")
            # Remove the item
            self.tree.delete(child_id)

            # Re-insert it back under the same parent node in sorted order
            self.tree.insert(parent_node, "end", text=item_text, values=item_values, tags=item_tags)


    def move_and_update_item(self, new_parent, new_values):
        # Get the selected item
        selected_item = self.tree.selection()
        if not selected_item:
            print("No item selected")
            return

        selected_item_id = selected_item[0]

        # Get the current item's text and values
        item_text = self.tree.item(selected_item_id, 'text')  # The item's label/text
        item_values = self.tree.item(selected_item_id, 'values')  # The item's associated values

        # Delete the selected item from the current position
        self.tree.delete(selected_item_id)

        # Modify the values if needed (based on new_values parameter)
        updated_values = tuple(new_values) if new_values else item_values
        _, lora_path, png_path = updated_values 
        # Insert the item into a new parent with updated fields
        if lora_path and png_path:
            self.tree.insert(new_parent, 'end', text=item_text, values=updated_values, tags=("cyan",))
        else:
            self.tree.insert(new_parent, 'end', text=item_text, values=updated_values)

        print(f"Item moved to {new_parent} and updated with new values: {updated_values}")


    def get_full_path(self, item_id):
        """Recursively retrieve the full path for a given Treeview item."""
        parent_id = self.tree.parent(item_id)
        if parent_id:
            parent_text = self.tree.item(parent_id, 'text')
            current_text = self.tree.item(item_id, 'text')
            return os.path.join(self.get_full_path(parent_id), current_text)
        else:
            # If no parent, this is the root or base directory
            return self.tree.item(item_id, 'text')    

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


    def search_and_highlight(self, search_query):
        """Searches for Lora names and highlights matching items."""
        matches = []
        for item in self.tree.get_children():
            self.search_tree(item, search_query.lower(), matches)
        if matches:
            self.tree.selection_set(matches)
            self.tree.focus_set()
            self.tree.see(matches[0])
        else:
            msgbox.showinfo("No Matches", "No matching Lora names found.", parent=self.root)

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
    #endregion Search Callbacks


    #region Misc Callbacks
    def open_png_directory(self):
        selected_item = self.tree.selection()

        item_text = self.tree.item(selected_item, "text")
        file_path = self.tree.item(selected_item, "values")[2] if self.tree.item(selected_item, "values") else None

        if item_text and file_path:
            if not open_to_file(file_path):
                msgbox.showinfo("Failed", f"No PNG directory exists for: {item_text}", parent=self.root)


    def open_lora_parent_directory(self):
        # Get the selected item
        selected_item = self.tree.selection()

        # Get the item's text
        item_text = self.tree.item(selected_item, "text")
        file_path = self.tree.item(selected_item, "values")[1] if self.tree.item(selected_item, "values") else None

        if item_text and file_path:
            if not open_to_file(file_path):
                msgbox.showinfo("Failed", f"No file exists for: {item_text}", parent=self.root)
    #endregion Misc Callbacks