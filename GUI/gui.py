"""Main GUI module"""
VERSION = 0.7

import logging
import os
import tkinter as tk
import tkinter.messagebox as msgbox
from tkinter import ttk
from tkinter.filedialog import askdirectory

from handlers import InfoHandler, FileHandler
from helpers import QUALITIES

ROOT_DIRECTORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG = {
  "ckpt_processing_dir": None,
  "lora_processing_dir": None,
  "ckpt_png_dir": None,
  "lora_png_dir": None,
  "ckpt_model_dir": None,
  "lora_model_dir": None,
  "output_dir": None
}

DEBUG = False
logger = logging.getLogger(__name__)

class StableOrganizerApp:
    """GUI for Model and Output Organization"""
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(f"StableOrganizer v{VERSION}")
        self.root.geometry("1920x1080")

        self.config_path = os.path.join(ROOT_DIRECTORY, "config.json")
        self.config_data = self.load_config()

        self.info_handler = InfoHandler(self.config_data)
        self.file_handler = FileHandler(self.config_data)

        self.file_handler.initialize_lora_png_directories()
        self.file_handler.initialize_lora_model_directories()

        self.built_png_dict = self.info_handler.build_png_dictionary()
        self.built_lora_dict = self.info_handler.build_lora_dictionary()

        self.create_menu()
        self.create_context_menu()
        self.create_tree()
        self.set_keybinds()
        self.populate_tree(self.built_lora_dict, self.built_png_dict)


#============================================================================================================================================
    #region                                                         Configuration                                                           =
#============================================================================================================================================

    def get_setting(self, setting) -> str:
        return self.config_data.get(setting)


    def load_config(self) -> dict:
        """
        Load configuration settings.

        Returns:
            dict: Settings dictionary.
        """
        if os.path.exists(self.config_path):
            config = FileHandler.load_json_file(self.config_path, default={}, relative_path=False)
        else:
            config = DEFAULT_CONFIG
            self.save_config(config)
        return config


    def save_config(self, config: dict) -> None:
        """
        Save configuration settings.

        Args:
            config (dict): Settings dictionary
        """
        self.file_handler.save_json_file(self.config_path, config, relative_path=False)


    #endregion Configuration


#============================================================================================================================================
    #region                                                         Setup Functions                                                         #
#============================================================================================================================================

    def create_tree(self) -> None:
        """Set up tkinter tree in GUI."""
        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True)

        vertical_scrollbar = ttk.Scrollbar(frame, orient="vertical")
        vertical_scrollbar.pack(side="right", fill="y")

        self.tree = ttk.Treeview(frame, columns=("definition", "lora_path", "png_path"), show="tree headings", yscrollcommand=vertical_scrollbar.set)

        # Define column properties (widths and stretchable behavior)
        self.tree.column("#0", width=300, stretch=False)  # Main column (Lora name)
        self.tree.column("definition", width=500, stretch=True)  # PNG directory path
        self.tree.column("lora_path", width=100, stretch=True)  # Lora file path
        self.tree.column("png_path", width=100, stretch=True)  # PNG directory path

        # Set headings (this is optional, but useful for understanding columns)
        self.tree.heading("#0", text="Lora Name", anchor="w", command=lambda _col="#0": self.sort_hierarchy_column(_col, False))
        self.tree.heading("lora_path", text="Lora Path", anchor="w", command=lambda _col="lora_path": self.sort_hierarchy_column(_col, False))
        self.tree.heading("png_path", text="PNG Path", anchor="w", command=lambda _col="png_path": self.sort_hierarchy_column(_col, False))
        self.tree.heading("definition", text="Lora Definition", anchor="w", command=lambda _col="definition": self.sort_hierarchy_column(_col, False))

        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.tag_configure("has_imgs", background="light cyan")
        self.tree.tag_configure("no_imgs", background="light yellow")
        self.tree.tag_configure("dir_mismatch", background="sienna3")
        #self.tree.tag_configure("dir_mismatch", background="orange red")

        vertical_scrollbar.config(command=self.tree.yview)


    def populate_tree(self, built_lora_dict, built_png_dict) -> None:
        """Populate the treeview with categories, qualities, and Lora names from the built dictionaries."""
        full_definitions = self.file_handler.load_json_file("AliDictionaries.json")
        lora_definitions = full_definitions.get("lora", {})
        self.tree.delete(*self.tree.get_children())

        for category, qualities in built_lora_dict.items():
            category_id = self.tree.insert("", "end", text=category)  # Insert category node
            for quality, loras in qualities.items():
                quality_id = self.tree.insert(category_id, "end", text=quality)  # Insert quality node
                for lora in loras:
                    lora_path = lora[1]
                    png_dir_path = self.info_handler.get_path_by_lora_name(built_png_dict, lora[0])
                    lora_dir_path = self.info_handler.get_path_by_lora_name(built_lora_dict, lora[0])
                    if png_dir_path and png_dir_path != "None":
                        tags = ["has_imgs"]
                        if self.info_handler.get_quality_from_filepath(png_dir_path) != self.info_handler.get_quality_from_filepath(lora_dir_path):
                            tags = ["dir_mismatch"]
                    else:
                        tags = ["no_imgs"]
                    self.tree.insert(quality_id, "end", text=lora[0], values=(lora_definitions.get(lora[0], "None"), lora_path, png_dir_path), tags=tuple(tags))  # Insert Lora name


    def create_menu(self) -> None:
        """Create a File menu at the top of the window."""
        menubar = tk.Menu(self.root)

        # Create the File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Repopulate Tree", command=self.repopulate_tree)
        file_menu.add_command(label="Log Dicts", command=self.log_dicts)
        file_menu.add_command(label="HashSlingingSlasher", command=self.user_directory)
        file_menu.add_command(label="Config", command=self.change_config)

        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Add the File menu to the menubar
        menubar.add_cascade(label="File", menu=file_menu)

        # Display the menubar
        self.root.config(menu=menubar)


    def create_context_menu(self) -> None:
        """Create a context menu."""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Search with Everything", command=self.search_with_everything)
        self.context_menu.add_command(label="Open Lora Parent Folder", command=self.open_lora_parent_directory)
        self.context_menu.add_command(label="Open PNG Directory", command=self.open_png_directory)
        self.context_menu.add_separator()
        for quality in QUALITIES:
            self.context_menu.add_command(label=f"Move to {quality}", command=lambda q=quality: self.move_to_quality_directory(q))

        # Create a submenu
        # submenu = tk.Menu(self.context_menu, tearoff=0)
        # submenu.add_command(label="Submenu Item 1", command=lambda x: x)
        # submenu.add_command(label="Submenu Item 2", command=lambda x: x)

        # # Add the submenu to the context menu
        # self.context_menu.add_cascade(label="Move To", menu=submenu)


    def set_keybinds(self) -> None:
        """Set global keybinds."""
        # Root binds
        self.root.bind("<Control-f>", self.on_ctrl_f)
        self.root.bind("<Escape>", self.on_escape)

        # Tree binds
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Alt-Double-1>", self.on_alt_double_click)
        self.tree.bind("<Button-3>", self.on_right_click)


    #endregion Setup Functions


#============================================================================================================================================
    #region                                                         Keybinds                                                                #
#============================================================================================================================================

    def on_double_click(self, event) -> None:
        self.open_lora_parent_directory()


    def on_alt_double_click(self, event) -> None:
        self.open_png_directory()


    def on_right_click(self, event) -> None:
        self.show_context_menu(event)


    def on_ctrl_f(self, event) -> None:
        self.open_search_dialog()


    def on_escape(self, event) -> None:
        self.root.quit()


    #endregion Keybinds

#============================================================================================================================================
    #region                                                        Menu Callbacks                                                           #
#============================================================================================================================================

    def repopulate_tree(self) -> None:
        self.built_png_dict = self.info_handler.build_png_dictionary()
        self.built_lora_dict = self.info_handler.build_lora_dictionary()
        self.populate_tree(self.built_lora_dict, self.built_png_dict)


    def log_dicts(self) -> None:
        """Write dictionaries to file for review."""
        self.file_handler.log_dicts(self.built_lora_dict, self.built_png_dict)


    def user_directory(self) -> str:
        """Ask for a directory, and return the file name"""
        return askdirectory()


    #endregion Menu Callbacks

#============================================================================================================================================
    #region                                                       Context Callbacks                                                         #
#============================================================================================================================================

    def show_context_menu(self, event) -> None:
        """Display the right-click context menu."""
        # Get the selected item on right-click
        item_id = self.tree.identify_row(event.y)
        if item_id:
            selected_items = self.tree.selection()
            if len(selected_items) == 1:
                self.tree.selection_set(item_id)
                selected_items = self.tree.selection()

            for selection in selected_items:
                if not self.tree.item(selection, "values"): # invalid row selection
                    self.tree.selection_remove(selection)

            self.context_menu.post(event.x_root, event.y_root)


    def change_config(self):
        pass


    def search_with_everything(self):
        selected_items = self.tree.selection()
        if len(selected_items):
            name = self.tree.item(selected_items[0],"text")
            if name:
                self.file_handler.search_with_everything(name)


    def move_to_quality_directory(self, target_quality) -> None:
        """Move selections to the target quality node within the appropriate category."""
        selected_items = self.tree.selection()
        parent_sort = set()
        for selection in selected_items:
            selected_path = self.get_full_path(selection)
            category, current_quality, lora_name = selected_path.split('\\')
            if not self.tree.item(selection, "values"): # invalid row selection
                continue
            item_values = list(self.tree.item(selection, "values"))
            current_lora_path = item_values[1]
            current_lora_name = os.path.basename(current_lora_path)
            if DEBUG:
                logger.debug(f"current_lora_name: {current_lora_path}")
            current_png_path = item_values[2]
            current_png_dir = os.path.basename(current_png_path)
            if DEBUG:
                logger.debug(f"cur_png_dir_path: {current_png_path}")
            lora_model_root_path = self.get_setting("lora_model_dir")
            lora_png_root_path = self.get_setting("lora_png_dir")
            lora_target_path = os.path.normpath(os.path.join(lora_model_root_path, f"{category}_{target_quality}", current_lora_name))
            lora_png_target_path = os.path.normpath(os.path.join(lora_png_root_path, f"{category}_{target_quality}", current_png_dir))

            update_flag = False
            if current_lora_path != "None" and current_lora_path != lora_target_path:
                update_flag = True
                if DEBUG:
                    logger.debug(f"Move Lora: {current_lora_path} =====> {lora_target_path}")
                self.file_handler.move(current_lora_path, lora_target_path, quiet=not DEBUG)
                self.built_lora_dict = self.info_handler.build_lora_dictionary() #TODO refactor to avoid rebuilding entire dictionary every update
                item_values[1] = lora_target_path
            if current_png_path != "None" and current_png_path != lora_png_target_path:
                update_flag = True
                if DEBUG:
                    logger.debug(f"Move PNGs: {current_png_path} =====> {lora_png_target_path}")
                self.file_handler.move(current_png_path, lora_png_target_path, quiet=not DEBUG)
                self.built_png_dict = self.info_handler.build_png_dictionary() #TODO refactor to avoid rebuilding entire dictionary every update
                item_values[2] = lora_png_target_path
            if update_flag:
                new_parent = self.find_category_quality_node(category, target_quality)
                self.move_and_update_row(selection, new_parent, tuple(item_values))
                parent_sort.add(new_parent)
        for parent in parent_sort:
            self.sort_children_simple(parent)


    def find_category_quality_node(self, category, quality) -> str | None:
        """Iterate over the tree to find the node corresponding to the target category and quality; create it if necessary"""
        for _category in self.tree.get_children():  # Get top-level items
            if self.tree.item(_category, 'text') == category:
                for _quality in self.tree.get_children(_category):
                    if self.tree.item(_quality, 'text') == quality:
                        if DEBUG:
                            logger.debug("Found treeview category node: %s", quality)
                        return _quality
                if DEBUG:
                    logger.debug("Creating treeview category: %s", category)
                new_quality = self.tree.insert(_category, 0, text=quality)
                if DEBUG:
                    logger.debug("Created treeview category node: %s", new_quality)
                return new_quality
        return None


    def move_and_update_row(self, selected_item_id, new_parent, new_values) -> None:
        """Move treeview entries and refresh their values."""
        if not selected_item_id:
            return
        item_text = self.tree.item(selected_item_id, 'text')  # The item's label/text
        item_values = self.tree.item(selected_item_id, 'values')  # The item's associated values
        self.tree.delete(selected_item_id)
        values = tuple(new_values) if new_values else item_values
        lora_definition, lora_path, png_path = values
        if png_path and png_path != "None":
            tags = ["dir_mismatch"] if self.quality_mismatch(lora_path, png_path) else ["has_imgs"]
        else:
            tags = ["no_imgs"]
        self.tree.insert(new_parent, 'end', text=item_text, values=values, tags=tuple(tags))
        if DEBUG:
            print(f"Item moved to {new_parent} and updated with new values: {values}")


    def quality_mismatch(self, model_path, png_path):
        return self.info_handler.get_quality_from_filepath(model_path) != self.info_handler.get_quality_from_filepath(png_path)


    def get_full_path(self, item_id) -> str:
        """Recursively retrieve the full tree path for a given Treeview item."""
        parent_id = self.tree.parent(item_id)
        if parent_id:
            #parent_text = self.tree.item(parent_id, 'text')
            current_text = self.tree.item(item_id, 'text')
            return os.path.join(self.get_full_path(parent_id), current_text)
        # If no parent, this is the root or base directory
        return self.tree.item(item_id, 'text')


    #endregion Context Callbacks

#============================================================================================================================================
    #region                                                         Sort Callbacks                                                         #
#============================================================================================================================================

    def sort_hierarchy_column(self, col, reverse, key=None, parent=""):
        """Sort leaf nodes by column."""
        children = self.tree.get_children(parent)
        # Determine if we are sorting the special tree column (#0) or a regular column
        if col == "#0":
            leaf_nodes = [(self.tree.item(child, "text"), child) for child in children if self.tree.item(child, "values")]
        else:
            leaf_nodes = [(self.tree.set(child, col), child) for child in children if self.tree.item(child, "values")]
        leaf_nodes.sort(key=key, reverse=reverse)
        for index, (val, leaf) in enumerate(leaf_nodes):
            self.tree.move(leaf, parent, index)
        for child in children:
            if self.tree.get_children(child):  # Only recurse if the child has its own children
                self.sort_hierarchy_column(col, reverse, key, child)
        self.tree.heading(col, command=lambda _col=col: self.sort_hierarchy_column(_col, not reverse, key))


    def sort_children_simple(self, parent_node, reverse=False) -> None:
        """Sort children of the parent node."""
        children = self.tree.get_children(parent_node)
        children_with_values = [(child, name) for child in children if (name := self.tree.item(child, "text"))]
        children_with_values.sort(key=lambda x: x[1], reverse=reverse)
        for index, (child_id, _) in enumerate(children_with_values):
            self.tree.move(child_id, parent_node, index)


    #endregion Sort Callbacks

#============================================================================================================================================
    #region                                                         Search Callbacks                                                         #
#============================================================================================================================================

    def open_search_dialog(self, event=None) -> None:
        """Open a search dialog when Ctrl+F is pressed."""
        search_window = tk.Toplevel(self.root)
        search_window.title("Search")
        search_window.geometry("150x100")
        tk.Label(search_window, text="Search Lora Name:").pack(pady=5)
        search_entry = tk.Entry(search_window)
        search_entry.pack(pady=5)
        search_entry.focus_set()
        search_entry.bind("<Return>", lambda event: self.search_and_redraw(search_entry.get()))
        tk.Button(search_window, text="Search", command=lambda: self.search_and_redraw(search_entry.get())).pack(pady=5)


    def search_and_redraw(self, search_query:str) -> None:
        """Search for the query and redraw the Treeview with only the matches."""
        filtered_lora_dict = {}
        search_query = search_query.lower()
        self.tree.delete(*self.tree.get_children())
        for category, qualities in self.lora_dict.items():
            if category not in filtered_lora_dict:
                filtered_lora_dict[category] = {}
            for quality, loras in qualities.items():
                if quality not in filtered_lora_dict:
                    filtered_lora_dict[category][quality] = {}
                for lora_key, lora_paths in loras.items():
                    if search_query in lora_key.lower():
                        filtered_lora_dict[category][quality][lora_key] = lora_paths

        self.populate_tree(filtered_lora_dict)


    def search_and_highlight(self, search_query) -> None:
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


    def search_in_tree(self, search_query) -> None:
        """Search for the query in the Treeview and highlight the matching items."""
        self.tree.selection_remove(self.tree.selection()) # This starter function is just to remove selection first before recursing
        for item in self.tree.get_children():
            self.search_in_subtree(item, search_query)


    def search_in_subtree(self, parent, search_query):
        """Recursively search in the subtree rooted at 'parent'."""
        # Check if the parent's text matches the search query
        if search_query.lower() in self.tree.item(parent, "text").lower():
            self.tree.selection_add(parent)  # Highlight the matching item
            self.tree.see(parent)  # Make sure it's visible
        for child in self.tree.get_children(parent):
            self.search_in_subtree(child, search_query)


    #endregion Search Callbacks

#============================================================================================================================================
    #region                                                         Misc Callbacks                                                         #
#============================================================================================================================================

    def open_png_directory(self) -> None:
        """Open PNG directory."""
        selected_item = self.tree.selection()
        item_text = self.tree.item(selected_item, "text")
        values = self.tree.item(selected_item, "values")
        filepath = values[2] if values else None
        if item_text and filepath:
            if not self.file_handler.open_to_file(filepath):
                msgbox.showinfo("Failed", f"No PNG directory exists for: {item_text}", parent=self.root)


    def open_lora_parent_directory(self) -> None:
        """Open Lora Model directory."""
        selected_item = self.tree.selection()
        item_text = self.tree.item(selected_item, "text")
        values = self.tree.item(selected_item, "values")
        filepath = values[1] if values else None
        if item_text and filepath:
            if not self.file_handler.open_to_file(filepath):
                msgbox.showinfo("Failed", f"No file exists for: {item_text}", parent=self.root)


    #endregion Misc Callbacks
