from abc import ABC, abstractmethod
import os
import shutil
import logging

logger = logging.getLogger(__name__)

#region Stack
class Stack:
    """A stack to manage commands, enabling undo functionality."""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Stack, cls).__new__(cls, *args, **kwargs)
            cls._instance.commands = []
        return cls._instance

    def __init__(self):
        self.commands = []

    def push(self, command):
        """Adds a command to the stack."""
        self.commands.append(command)

    def pop(self):
        """Removes and returns the most recent command."""
        if not self.commands:
            raise IndexError("No commands to undo")
        return self.commands.pop()

    def undo(self):
        """Performs the undo operation for the most recent command."""
        if not self.commands:
            print("Nothing to undo")
            return
        command = self.pop()
        command.undo()


stack = Stack()


#region Commands
class Command(ABC):
    @abstractmethod
    def do(self):
        pass

    @abstractmethod
    def undo(self):
        pass


class FileMoveCommand(Command):
    """
    Move a file and store previous state.

    Parameters:
        src_file: Source path of file.
        dest_file: Destination path of file.
    """
    def __init__(self, src_file, dest_file):
        """Initialize the command with source and destination paths."""
        self.src_file = src_file
        self.dest_file = dest_file

    def do(self):
        """Executes the move operation (moves the file from src to dest)."""
        if os.path.exists(self.src):
            print(f"Moving {self.src} to {self.dest}")
            shutil.move(self.src, self.dest)
        else:
            raise FileNotFoundError(f"Source file not found: {self.src}")

    def undo(self):
        """Reverses the move operation (moves the file back from dest to src)."""
        if os.path.exists(self.dest):
            print(f"Undoing move: Moving {self.dest} back to {self.src}")
            shutil.move(self.dest, self.src)
        else:
            raise FileNotFoundError(f"Destination file not found: {self.dest}")


class TreeMoveCommand(Command):
    """
    Initialize the command with treeview, item ID, and new location details.

    Parameters:
        tree: The Treeview widget where the operation takes place.
        item_id: The ID of the item to move.
        new_parent: The new parent ID (or '' for the root).
        new_index: The new position index under the new parent.
    """

    def __init__(self, tree, item_id, new_parent, new_index):
        self.tree = tree
        self.item_id = item_id
        self.new_parent = new_parent
        self.new_index = new_index
        self.old_parent = tree.parent(item_id)
        self.old_index = tree.index(item_id)

    def do(self):
        """Executes the move operation (moves the Treeview item to a new location)."""
        print(f"Moving item {self.item_id} to parent {self.new_parent} at index {self.new_index}")
        self.tree.move(self.item_id, self.new_parent, self.new_index)

    def undo(self):
        """Reverses the move operation (moves the Treeview item back to its original location)."""
        # Move the item back to its original location
        print(f"Undoing move: Moving item {self.item_id} back to parent {self.old_parent} at index {self.old_index}")
        self.tree.move(self.item_id, self.old_parent, self.old_index)



