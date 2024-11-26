"""Actions that use the stack go here"""

import os
import shutil
import logging
import threading

from abc import ABC, abstractmethod

from helpers import CAT_QUAL_PATTERN

ROOT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(ROOT_DIRECTORY, "debugging.log")

logger = logging.getLogger(__name__)


# region Stack
class Stack:
    """A stack to manage commands, enabling undo functionality."""

    def __init__(self):
        self.command_history = []
        self.command_queue = []
        self.lock = threading.Lock()

    def push(self, command):
        """Adds a command to the stack."""
        print("beep")
        with self.lock:
            self.command_history.append(command)

    def pop(self):
        """Removes and returns the most recent command."""
        with self.lock:
            if not self.command_history:
                raise IndexError("No commands to undo")
            return self.command_history.pop()

    def undo(self):
        """Performs the undo operation for the most recent command."""
        with self.lock:
            if not self.command_history:
                print("Nothing to undo")
                return
            command = self.pop()
            command.undo()

    def queue_command(self, cmd):
        """Adds command to a queue for later processing."""
        self.command_queue.append(cmd)

    def execute_queued_commands(self):
        """Executes all queued commands as a batch."""
        if not self.command_queue:
            print("No commands to execute")
            return
        composite_cmd = CompositeCommand(self.command_queue)
        try:
            composite_cmd.execute()
            self.command_queue.clear()
            self.push(composite_cmd)
        except Exception as e:
            logger.exception(f"Batch execution failed: {e}")
            composite_cmd.undo()
            raise


# region Commands
class Command(ABC):
    def __str__(self):
        return self.__class__.__name__

    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def undo(self):
        pass


class CompositeCommand(Command):
    """A composite command that executes and undoes multiple commands as a single unit."""

    def __init__(self, commands):
        """Initialize with a list of commands.

        Parameters:
            commands: A list of Command objects to be executed/undone together."""
        self.commands: list[Command] = commands

    def execute(self):
        executed_commands: list[Command] = []
        for command in self.commands:
            try:
                command.execute()
                executed_commands.append(command)
            except Exception:
                # logger.exception("Error executing command %s: %s", type(command).__name__, e, exc_info=1, stack_info=True)
                for command in reversed(executed_commands):
                    command.undo()
                return
        return True

    def undo(self):
        for command in reversed(self.commands):
            try:
                command.undo()
            except Exception as e:
                logger.exception(
                    "Error undoing %s: %s",
                    type(command).__name__,
                    e,
                    exc_info=1,
                    stack_info=True,
                )


class FileMoveCommand(Command):
    """Move a file and store previous state.

    Parameters:
        src_file: Source path of file.
        dest_file: Destination path of file.
    """

    def __init__(self, source_path: str, destination_path: str, quiet: bool = False):
        """Initialize the command with source and destination paths.

        Parameters:
            source_path (str): The path of the source file.
            destination_path (str): The path to move the file to.
            quiet (bool): If True, suppresses logging output."""

        self.source_path = source_path
        self.destination_path = destination_path
        self.quiet = quiet
        self.target_path = None

    @property
    def details(self) -> str:
        return f"{self.source_path} => {self.destination_path}"

    def execute(self):
        """Executes the move operation (moves the file from src to dest)."""
        if not os.path.exists(self.source_path):
            raise ValueError(f"File not found: {self.source_path}")
        if self.source_path == self.destination_path:
            raise ValueError(
                "Cancel move (src == dest): %s => %s",
                self.source_path,
                self.destination_path,
            )

        dest_is_dir = os.path.isdir(self.destination_path)
        dest_exists = os.path.exists(self.destination_path)
        if dest_exists and not dest_is_dir:
            raise FileExistsError(f"Destination file already exists: {self.destination_path}")
        self.target_path = (
            os.path.join(self.destination_path, os.path.basename(self.source_path))
            if dest_is_dir
            else self.destination_path
        )
        if os.path.exists(self.target_path):
            raise FileExistsError(f"Target path already exists: {self.target_path}")
        parent_dir = os.path.dirname(self.target_path)
        os.makedirs(parent_dir, exist_ok=True)
        try:
            shutil.move(self.source_path, self.target_path)
            if not self.quiet:
                logger.debug("File\tmoved %s to %s", self.source_path, self.target_path)
        except Exception as e:
            raise ValueError(
                "Error moving file: %s => %s\n%s",
                self.source_path,
                self.destination_path,
                e,
            )
        return True

    def undo(self):
        """Reverses the move operation."""
        if os.path.exists(self.target_path):
            os.makedirs(os.path.dirname(self.source_path), exist_ok=True)
            if os.path.exists(self.source_path):
                raise FileExistsError(f"Cannot undo move: Source file already exists at {self.source_path}")
            try:
                shutil.move(self.target_path, self.source_path)
                if not self.quiet:
                    logger.debug(
                        "Undo file\tmove: %s back to %s",
                        self.target_path,
                        self.source_path,
                    )
            except Exception as e:
                raise ValueError("Error undoing move %s: %s", self.details, e)
        else:
            raise ValueError("Undo failed: File does not exist at source: %s", self.details)


class TreeMoveCommand(Command):
    """Initialize the command with treeview, item ID, and new location details.

    Parameters:
        tree: The Treeview widget where the operation takes place.
        item_id: The ID of the item to move.
        new_parent: The new parent ID (or '' for the root).
        new_index: The new position index under the new parent."""

    def __init__(self, tree, item_id, new_parent, new_values):
        # if not tree.exists(item_id):
        #     raise ValueError("item_id doesn't exist")
        self.tree = tree
        self.item_id = item_id
        self.item_text = tree.item(item_id, "text")
        self.new_parent = new_parent
        self.new_values = new_values
        self.new_index = "end"
        self.old_parent = tree.parent(item_id)
        self.old_values = tree.item(item_id, "values")
        self.old_index = tree.index(item_id)

    @property
    def details(self) -> str:
        return f"{self.item_text}: {self.old_values} => {self.new_values}"

    def execute(self):
        """Move treeview entry and refresh its values."""
        if not self.item_id:
            raise ValueError("Item ID doesn't exist")
        if self.tree.parent(self.item_id) == self.new_parent:
            self.new_index = self.old_index
        if self.new_values == self.old_values and self.tree.parent(self.item_id) == self.new_parent:
            return None
        self.tree.delete(self.item_id)
        values = tuple(self.new_values) if self.new_values else tuple(self.old_values)
        if len(values) < 3:
            raise ValueError
        lora_definition, lora_path, png_path = values
        if png_path and png_path != "None":
            tags = ["dir_mismatch"] if TreeMoveCommand.quality_mismatch(lora_path, png_path) else ["has_imgs"]
        else:
            tags = ["no_imgs"]
        updated_selection = self.tree.insert(
            self.new_parent,
            self.new_index,
            text=self.item_text,
            values=values,
            tags=tuple(tags),
        )
        self.item_id = updated_selection
        logger.debug(
            f"Row\tmoved to \"{self.tree.item(self.new_parent, 'text')}\" and updated with new values: {values}"
        )
        return updated_selection

    def undo(self):
        """Reverses the move operation (moves the Treeview item back to its original location)."""
        if not self.item_id:
            raise ValueError("Item ID doesn't exist")
        if self.tree.parent(self.item_id) == self.old_parent:
            self.new_index = self.old_index
        if self.old_values == self.new_values and self.tree.parent(self.item_id) == self.old_parent:
            return
        self.tree.delete(self.item_id)
        values = tuple(self.old_values)
        if len(values) < 3:
            raise ValueError
        lora_definition, lora_path, png_path = values
        if png_path and png_path != "None":
            tags = ["dir_mismatch"] if TreeMoveCommand.quality_mismatch(lora_path, png_path) else ["has_imgs"]
        else:
            tags = ["no_imgs"]
        updated_selection = self.tree.insert(
            self.old_parent,
            self.new_index,
            text=self.item_text,
            values=values,
            tags=tuple(tags),
        )
        self.item_id = updated_selection
        logger.debug(
            f"Undo row\tmove: {self.new_parent} back to \"{self.tree.item(self.old_parent, 'text')}\" and updated with new values: {values}"
        )
        return updated_selection

    @staticmethod
    def quality_mismatch(model_path: str, png_path: str) -> bool:
        """Check if the two paths don't share quality."""
        return TreeMoveCommand.get_quality_from_filepath(model_path) != TreeMoveCommand.get_quality_from_filepath(
            png_path
        )

    @staticmethod
    def get_quality_from_filepath(filepath: str) -> str:
        """Get the quality from directory or safetensors/png files."""
        match = CAT_QUAL_PATTERN.search(filepath)
        return match.group() if match else "None"
