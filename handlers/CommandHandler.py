"""Actions that use the stack go here"""

import logging
import os
import shutil
import threading
import tkinter.messagebox as msgbox
from abc import ABC, abstractmethod

from helpers import LORA_CAT_QUAL_PATTERN

ROOT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(ROOT_DIRECTORY, "debugging.log")

logger = logging.getLogger(__name__)


# region Stack
class Stack:
    """A stack to manage commands, enabling undo functionality.

    Properties:
        history: list[str]
        queue: list[str]"""

    def __init__(self):
        self.command_history = []
        self.command_queue = []
        self.lock = threading.Lock()
        self.q_lock = threading.Lock()

    @property
    def history(self):
        return map(str, self.command_history)

    @property
    def queue(self):
        return map(str, self.command_queue)

    def push(self, command):
        """Adds a command to the stack."""
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
        if not self.command_history:
            print("Nothing to undo")
            return
        command = self.command_history.pop()
        command.undo()

    def queue_command(self, cmd):
        """Adds command to a queue for later processing."""
        with self.q_lock:
            self.command_queue.append(cmd)

    def execute_queued_commands(self):
        """Executes all queued commands as a composite."""
        if not self.command_queue:
            logger.debug("No commands to execute")
            return
        with self.q_lock:
            results = None
            composite_cmd = CompositeCommand(self.command_queue)
            try:
                results = composite_cmd.execute()
                self.command_queue.clear()
                self.push(composite_cmd)
            except Exception as e:
                logger.debug("Queued batch execution failed")
                composite_cmd.undo()
                raise e
            return results


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


class CommandResult:
    """Standardized command result.

    Parameters:
        success: bool = Only True when there's a result that can be undone. False doesn't necessarily mean critical error
        data: any = Payload for commands that return a result to the executor
        details: str = Error message would go here
        error: Exception = If an error is raised, it'll be captured here for the higher function to re-raise"""

    def __init__(self, success: bool, data=None, details: str = "", error: Exception = None):
        self.success = success
        self.data = data
        self.details = details
        self.error = error

    def __repr__(self):
        return f"CommandResult(success={self.success}, data={self.data}, details={self.details})"


class CompositeCommand(Command):
    """A composite command that executes and undoes multiple commands as a single unit.

    Parameters:
        commands: A list of Command objects to be executed/undone together.

    Properties:
        details: Description of the commands in this composite
        result: CommandResult"""

    def __init__(self, commands):
        self.commands: list[Command] = commands
        self.results = []

    @property
    def details(self) -> str:
        out = []
        for command in self.commands:
            out.append(command.details)
        return out

    @property
    def result(self) -> str:
        out = []
        for result in self.results:
            out.append(result.data if result.data else self.success)
        return out

    def execute(self):
        executed_commands: list[Command] = []
        results = []
        for command in self.commands:
            try:
                result: CommandResult = command.execute()
                if result.success:
                    executed_commands.append(command)
                elif result.error:
                    raise result.error
                results.append(result)
            except Exception as e:
                try:
                    for command in reversed(executed_commands):
                        command.undo()
                except Exception as e2:
                    return CommandResult(False, None, "CompositeCommand", e2)
                return CommandResult(False, None, "exec:CompositeCommand", e)
        self.commands = executed_commands
        self.results = results
        return CommandResult(True, self.results, "CompositeCommand")

    def undo(self):
        errors = []
        for command in reversed(self.commands):
            try:
                command.undo()
            except Exception as e:
                logger.warning("Error during undo: %s", e)
                errors.append(str(e))
        if errors:
            return CommandResult(False, None, f"Undo composite errors: {', '.join(errors)}")
        self.results.clear()


class FileMoveCommand(Command):
    """Move a file, store previous state and result.

    Parameters:
        src_file: Source path of file.
        dest_file: Destination path of file.

    Returns:
        True if successful

    """

    def __init__(self, source_path: str, destination_path: str):
        self.source_path = os.path.normpath(source_path)
        self.destination_path = os.path.normpath(destination_path)
        self.target_path = None
        self._result = None

    @property
    def details(self) -> str:
        return f"file_mv:{self.source_path} => {self.destination_path}"

    @property
    def result(self) -> str:
        return self._result

    def execute(self):
        """Executes the move operation (moves the file from src to dest)."""
        try:
            if not os.path.exists(self.source_path):
                logger.warning("File not found: %s", self.source_path)
                return CommandResult(False, None, f"File not found: {self.details}")
            if self.source_path == self.destination_path:
                logger.info("No movement needed: Source and destination are the same.")
                return CommandResult(False, None, "No movement, src == dest")
            dest_is_dir = os.path.isdir(self.destination_path)
            dest_exists = os.path.exists(self.destination_path)
            if dest_exists and not dest_is_dir:
                msgbox.showinfo("Dest file already exists: No movement", f"{self.destination_path}")
                self._result = CommandResult(
                    False, None, f"Dest file already exists: No movement: {self.destination_path}"
                )
                return self._result  # TODO user option to replace?
            self.target_path = (
                os.path.join(self.destination_path, os.path.basename(self.source_path))
                if dest_is_dir
                else self.destination_path
            )
            if os.path.exists(self.target_path):
                logger.warning("Destination file exists: %s", self.target_path)
                self._result = CommandResult(
                    False, None, f"Dest file already exists: No movement2: {self.destination_path}"
                )
                return self._result  # TODO user option to replace?
            parent_dir = os.path.dirname(self.target_path)
            os.makedirs(parent_dir, exist_ok=True)
            shutil.move(self.source_path, self.target_path)
            logger.debug("File\tmoved %s to %s", self.source_path, self.target_path)
            self._result = CommandResult(True, None, self.details)
            return self._result
        except Exception as e:
            logger.exception("Unexpected error during file move: %s", self.details)
            self._result = CommandResult(False, None, f"Uncaught error:exec:{self.details}", e)
            return self._result

    def undo(self):
        """Reverses the move operation."""
        try:
            if os.path.exists(self.target_path):
                os.makedirs(os.path.dirname(self.source_path), exist_ok=True)
                if os.path.exists(self.source_path):
                    msgbox.showinfo("File undo failed", f"Cannot undo move: Source file already exists\n{self.details}")
                    self._result = CommandResult(
                        False, None, f"Cannot undo move: Source file already exists\n{self.details}"
                    )
                    return self._result
                try:
                    shutil.move(self.target_path, self.source_path)
                    logger.debug(
                        "Undo file\tmove: %s back to %s",
                        self.target_path,
                        self.source_path,
                    )
                    self.target_path = None
                    self._result = None
                except Exception as e:
                    msgbox.showinfo("File undo error", f"Error undoing move {self.details}")
                    self._result = CommandResult(False, None, f"Error undoing move: {self.details}", e)
                    return self._result
            else:
                msgbox.showinfo("File undo error", f"Undo failed: File does not exist at source: {self.details}")
                self._result = CommandResult(False, None, f"Undo failed: File does not exist at source: {self.details}")
                return self._result
        except Exception as e:
            msgbox.showinfo("Uncaught error", f"{self.details}")
            self._result = CommandResult(False, None, f"Uncaught error:undo:{self.details}", e)


class TreeMoveCommand(Command):
    """Initialize the command with treeview, item ID, and new location details.

    Parameters:
        tree: The Treeview widget where the operation takes place.
        item_id: The ID of the item to move.
        new_parent: The new parent ID (or '' for the root).
        new_index: The new position index under the new parent.

    Returns:
        New row id"""

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
        self._result = None

    @property
    def details(self) -> str:
        return f"row_mv:{self.item_text}: {self.old_values} => {self.new_values}"

    @property
    def result(self) -> str:
        return self._result

    def execute(self) -> CommandResult | None:
        """Move treeview entry and refresh its values."""
        try:
            if not self.item_id:
                msgbox.showinfo("Command Failed! Item ID error.", f"exec:{self.details}")
                self._result = CommandResult(False, None, f"exec:Item ID error:{self.details}")
                return self._result
            if self.tree.parent(self.item_id) == self.new_parent:
                self.new_index = self.old_index
            if self.new_values == self.old_values and self.tree.parent(self.item_id) == self.new_parent:
                return None
            self.tree.delete(self.item_id)
            values = tuple(self.new_values) if self.new_values else tuple(self.old_values)
            if len(values) < 3:
                msgbox.showinfo(
                    "Command Failed! Row value length error.",
                    f"exec:{self.details}",
                )
                self._result = CommandResult(False, None, f"exec:Row value length error:{self.details}")
                return self._result
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
            self._result = CommandResult(True, self.item_id, self.details)
            logger.debug(
                f"Row\tmoved to \"{self.tree.item(self.new_parent, 'text')}\" and updated with new values: {values}"
            )
            return self._result
        except Exception as e:
            msgbox.showinfo("Uncaught error", f"exec:{self.details}")
            return CommandResult(False, None, f"Uncaught error:exec:{self.details}", e)

    def undo(self):
        """Reverses the move operation (moves the Treeview item back to its original location)."""
        try:
            if self.tree.parent(self.item_id) == self.old_parent:
                self.new_index = self.old_index
            if self.old_values == self.new_values and self.tree.parent(self.item_id) == self.old_parent:
                return CommandResult(True, None, "undo:No movement")
            self.tree.delete(self.item_id)
            values = tuple(self.old_values)
            if len(values) < 3:
                msgbox.showinfo("Undo Failed! Row value length error.", f"undo:{self.details}")
                return CommandResult(False, None, f"undo:Row value length error:{self.details}")
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
        except Exception as e:
            msgbox.showinfo("Uncaught error", f"undo:{self.details}")
            return CommandResult(False, None, f"Uncaught error:undo:{self.details}", e)

    @staticmethod
    def quality_mismatch(model_path: str, png_path: str) -> bool:
        """Check if the two paths don't share quality."""
        return TreeMoveCommand.get_quality_from_filepath(model_path) != TreeMoveCommand.get_quality_from_filepath(
            png_path
        )

    @staticmethod
    def get_quality_from_filepath(filepath: str) -> str:
        """Get the quality from directory or safetensors/png files."""
        match = LORA_CAT_QUAL_PATTERN.search(filepath)
        return match.group() if match else "None"
