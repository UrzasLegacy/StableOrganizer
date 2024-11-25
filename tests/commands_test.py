import os
import tempfile
import logging
import pytest
import tkinter as tk
from tkinter import ttk, TclError

from handlers.CommandHandler import (
    Stack,
    Command,
    CompositeCommand,
    FileMoveCommand,
    TreeMoveCommand,
)
from helpers import *

logging.basicConfig(level=logging.DEBUG)


# Helper function to clear the stack before each test
def clear_stack():
    stack = Stack()
    with stack.lock:
        stack.commands.clear()


# Mock Command class for testing
class CommandMock(Command):
    def __init__(self):
        self.executed = False
        self.undone = False

    def execute(self):
        self.executed = True

    def undo(self):
        self.undone = True


# Mock Command that fails during execution
class FailingCommandMock(Command):
    def __init__(self):
        self.executed = False
        self.undone = False

    def execute(self):
        self.executed = True
        raise Exception("Execution failed")

    def undo(self):
        self.undone = True


# region Stack class
def test_stack_singleton():
    stack1 = Stack()
    stack2 = Stack()
    assert stack1 is stack2


def test_stack_push():
    clear_stack()
    stack = Stack()
    command = CommandMock()
    stack.push(command)
    assert stack.commands == [command]


def test_stack_pop():
    clear_stack()
    stack = Stack()
    command1 = CommandMock()
    command2 = CommandMock()
    stack.push(command1)
    stack.push(command2)
    cmd = stack.pop()
    assert cmd is command2
    assert stack.commands == [command1]


def test_stack_pop_empty():
    clear_stack()
    stack = Stack()
    with pytest.raises(IndexError):
        stack.pop()


def test_stack_undo():
    clear_stack()
    stack = Stack()
    command = CommandMock()
    stack.push(command)
    stack.undo()
    assert command.undone == True
    assert stack.commands == []


def test_stack_undo_empty():
    clear_stack()
    stack = Stack()
    import io
    from contextlib import redirect_stdout

    f = io.StringIO()
    with redirect_stdout(f):
        stack.undo()
    output = f.getvalue()
    assert "Nothing to undo" in output


# region CompositeCommand
def test_composite_command_execute():
    command1 = CommandMock()
    command2 = CommandMock()
    composite = CompositeCommand([command1, command2])
    composite.execute()
    assert command1.executed == True
    assert command2.executed == True


def test_composite_command_granular_undo():
    command1 = CommandMock()
    command2 = CommandMock()
    composite = CompositeCommand([command1, command2])
    composite.execute()
    command1.undo()
    command2.undo()
    assert command1.undone == True
    assert command2.undone == True


def test_composite_command_atomic_undo():
    command1 = CommandMock()
    command2 = CommandMock()
    composite = CompositeCommand([command1, command2])
    composite.execute()
    composite.undo()
    assert command1.undone == True
    assert command2.undone == True


def test_composite_command_execute_with_failure():
    command1 = CommandMock()
    failing_command = FailingCommandMock()
    command3 = CommandMock()
    composite = CompositeCommand([command1, failing_command, command3])
    composite.execute()
    # command1 should have been executed and then undone
    assert command1.executed == True
    assert command1.undone == True
    # failing_command execution should have failed
    assert failing_command.executed == True
    assert (
        failing_command.undone == False
    )  # It wasn't undone because it didn't complete
    # command3 should not have been executed
    assert command3.executed == False
    assert command3.undone == False


# region FileMoveCommand
def test_file_move_command_execute():
    with tempfile.TemporaryDirectory() as temp_dir:
        source_file = os.path.join(temp_dir, "source.txt")
        destination_dir = os.path.join(temp_dir, "dest")
        destination_file = os.path.join(destination_dir, "source.txt")
        # Create source file
        with open(source_file, "w") as f:
            f.write("test content")
        # Ensure destination directory exists
        os.makedirs(destination_dir)
        command = FileMoveCommand(source_file, destination_dir)
        command.execute()
        # Check that source file no longer exists
        assert not os.path.exists(source_file)
        # Check that file exists in destination
        assert os.path.exists(destination_file)
        # Check that content is the same
        with open(destination_file, "r") as f:
            content = f.read()
        assert content == "test content"


def test_file_move_command_undo():
    with tempfile.TemporaryDirectory() as temp_dir:
        source_file = os.path.join(temp_dir, "source.txt")
        destination_dir = os.path.join(temp_dir, "dest")
        destination_file = os.path.join(destination_dir, "source.txt")
        # Create source file
        with open(source_file, "w") as f:
            f.write("test content")
        # Ensure destination directory exists
        os.makedirs(destination_dir)
        command = FileMoveCommand(source_file, destination_dir)
        command.execute()
        # Now undo
        command.undo()
        # Check that source file exists again
        assert os.path.exists(source_file)
        # Check that destination file no longer exists
        assert not os.path.exists(destination_file)


def test_file_move_command_execute_no_source():
    with tempfile.TemporaryDirectory() as temp_dir:
        source_file = os.path.join(temp_dir, "nonexistent.txt")
        destination_dir = os.path.join(temp_dir, "dest")
        command = FileMoveCommand(source_file, destination_dir)
        with pytest.raises(ValueError) as excinfo:
            command.execute()
        assert "File not found" in str(excinfo.value)


def test_file_move_command_execute_same_source_dest():
    with tempfile.TemporaryDirectory() as temp_dir:
        source_file = os.path.join(temp_dir, "source.txt")
        with open(source_file, "w") as f:
            f.write("test content")
        command = FileMoveCommand(source_file, source_file)
        with pytest.raises(ValueError) as excinfo:
            command.execute()
        assert "Cancel move" in str(excinfo.value)


def test_file_move_command_execute_dest_exists():
    with tempfile.TemporaryDirectory() as temp_dir:
        source_file = os.path.join(temp_dir, "source.txt")
        destination_file = os.path.join(temp_dir, "dest.txt")
        # Create source file
        with open(source_file, "w") as f:
            f.write("test content")
        # Create destination file
        with open(destination_file, "w") as f:
            f.write("existing content")
        command = FileMoveCommand(source_file, destination_file)
        with pytest.raises(FileExistsError) as excinfo:
            command.execute()
        assert "Destination file already exists" in str(excinfo.value)


def test_file_move_command_execute_target_exists():
    with tempfile.TemporaryDirectory() as temp_dir:
        source_file = os.path.join(temp_dir, "source.txt")
        destination_dir = os.path.join(temp_dir, "dest")
        destination_file = os.path.join(destination_dir, "source.txt")
        # Create source file
        with open(source_file, "w") as f:
            f.write("test content")
        # Create destination file at target path
        os.makedirs(destination_dir)
        with open(destination_file, "w") as f:
            f.write("existing content")
        command = FileMoveCommand(source_file, destination_dir)
        with pytest.raises(FileExistsError) as excinfo:
            command.execute()
        assert "Target path already exists" in str(excinfo.value)


def test_file_move_command_execute_quiet(caplog):
    with tempfile.TemporaryDirectory() as temp_dir:
        source_file = os.path.join(temp_dir, "source.txt")
        destination_dir = os.path.join(temp_dir, "dest")
        # Create source file
        with open(source_file, "w") as f:
            f.write("test content")
        # Ensure destination directory exists
        os.makedirs(destination_dir)
        command = FileMoveCommand(source_file, destination_dir, quiet=True)
        with caplog.at_level(logging.DEBUG):
            command.execute()
        # Check that no log message was emitted
        assert len(caplog.records) == 0


def test_file_move_command_execute_logging(caplog):
    with tempfile.TemporaryDirectory() as temp_dir:
        source_file = os.path.join(temp_dir, "source.txt")
        destination_dir = os.path.join(temp_dir, "dest")
        # Create source file
        with open(source_file, "w") as f:
            f.write("test content")
        # Ensure destination directory exists
        os.makedirs(destination_dir)
        command = FileMoveCommand(source_file, destination_dir, quiet=False)
        with caplog.at_level(logging.DEBUG):
            command.execute()

        # Check that log message was emitted
        assert any("File\tmoved" in record.message for record in caplog.records)


def test_file_move_command_undo_source_exists():
    with tempfile.TemporaryDirectory() as temp_dir:
        source_file = os.path.join(temp_dir, "source.txt")
        destination_dir = os.path.join(temp_dir, "dest")
        destination_file = os.path.join(destination_dir, "source.txt")
        # Create source file
        with open(source_file, "w") as f:
            f.write("test content")
        # Ensure destination directory exists
        os.makedirs(destination_dir)
        command = FileMoveCommand(source_file, destination_dir)
        command.execute()
        # Create file at source path to simulate conflict during undo
        with open(source_file, "w") as f:
            f.write("conflicting content")
        with pytest.raises(FileExistsError) as excinfo:
            command.undo()
        assert "Cannot undo move: Source file already exists" in str(excinfo.value)


def test_file_move_command_undo_target_missing():
    with tempfile.TemporaryDirectory() as temp_dir:
        source_file = os.path.join(temp_dir, "source.txt")
        destination_dir = os.path.join(temp_dir, "dest")
        # Create source file
        with open(source_file, "w") as f:
            f.write("test content")
        # Ensure destination directory exists
        os.makedirs(destination_dir)
        command = FileMoveCommand(source_file, destination_dir)
        command.execute()
        # Delete target file to simulate missing file
        destination_file = os.path.join(destination_dir, "source.txt")
        os.remove(destination_file)
        with pytest.raises(ValueError) as excinfo:
            command.undo()
        assert "Undo failed: File does not exist at source" in str(excinfo.value)


# region TreeMoveCommand
def test_tree_move_command_execute():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    tree = ttk.Treeview(root)
    # Set up tree
    parent = tree.insert("", "end", text="Parent")
    child = tree.insert(
        parent, "end", text="Child", values=("value1", "value2", "value3")
    )
    new_parent = tree.insert("", "end", text="New Parent")
    # Create command
    new_values = ("new_value1", "new_value2", "new_value3")
    command = TreeMoveCommand(tree, child, new_parent, new_values)
    # Execute command
    command.execute()
    # Check that child is now under new_parent
    assert tree.parent(command.item_id) == new_parent
    # Check that values are updated
    assert tree.item(command.item_id, "values") == new_values
    root.destroy()


def test_tree_move_command_undo():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    tree = ttk.Treeview(root)
    # Set up tree
    parent = tree.insert("", "end", text="Parent")
    child = tree.insert(
        parent, "end", text="Child", values=("value1", "value2", "value3")
    )
    new_parent = tree.insert("", "end", text="New Parent")
    # Create command
    new_values = ("new_value1", "new_value2", "new_value3")
    command = TreeMoveCommand(tree, child, new_parent, new_values)
    # Execute command
    command.execute()
    # Undo command
    command.undo()
    # Check that child is back under original parent
    assert tree.parent(command.item_id) == parent
    # Check that values are restored
    assert tree.item(command.item_id, "values") == ("value1", "value2", "value3")
    root.destroy()


def test_tree_move_command_execute_no_item():
    root = tk.Tk()
    root.withdraw()
    tree = ttk.Treeview(root)
    # Non-existent item_id
    item_id = "nonexistent"
    new_parent = tree.insert("", "end", text="New Parent")
    new_values = ("new_value1", "new_value2", "new_value3")
    command = None
    with pytest.raises(TclError) as e:
        command = TreeMoveCommand(tree, item_id, new_parent, new_values)
        command.execute()
    assert "Item nonexistent not found" in str(e.value)
    root.destroy()


def test_tree_move_command_execute_no_change():
    root = tk.Tk()
    root.withdraw()
    tree = ttk.Treeview(root)
    # Set up tree
    parent = tree.insert("", "end", text="Parent")
    child = tree.insert(
        parent, "end", text="Child", values=("value1", "value2", "value3")
    )
    # Create command with same parent and values
    new_values = ("value1", "value2", "value3")
    command = TreeMoveCommand(tree, child, parent, new_values)
    # Execute command
    result = command.execute()
    # Check that command did nothing
    assert result is None
    # Check that child is still under original parent
    assert tree.parent(child) == parent
    # Check that values are unchanged
    assert tree.item(child, "values") == new_values
    root.destroy()


def test_tree_move_command_undo_no_item():
    root = tk.Tk()
    root.withdraw()
    tree = ttk.Treeview(root)
    # Set up tree
    parent = tree.insert("", "end", text="Parent")
    child = tree.insert(
        parent, "end", text="Child", values=("value1", "value2", "value3")
    )
    new_parent = tree.insert("", "end", text="New Parent")
    new_values = ("new_value1", "new_value2", "new_value3")
    with pytest.raises(TclError):
        command = TreeMoveCommand(tree, child, new_parent, new_values)
        # Execute command
        command.execute()
        # Delete item to simulate missing item
        tree.delete(command.item_id)
        command.undo()
    root.destroy()


# region quality_mismatch
def test_quality_mismatch_same_quality():
    # Both paths contain the same category-quality combination
    model_path = "/models/Attire_Good/model.safetensors"
    png_path = "/images/Attire_Good/image.png"
    result = TreeMoveCommand.quality_mismatch(model_path, png_path)
    assert result == False  # No mismatch


def test_quality_mismatch_different_quality():
    # Paths contain different category-quality combinations
    model_path = "/models/Attire_Good/model.safetensors"
    png_path = "/images/Attire_Best/image.png"
    result = TreeMoveCommand.quality_mismatch(model_path, png_path)
    assert result == True  # Mismatch


def test_quality_mismatch_one_missing():
    # One path does not contain any category-quality combination
    model_path = "/models/Attire_Good/model.safetensors"
    png_path = "/images/unknown/image.png"
    result = TreeMoveCommand.quality_mismatch(model_path, png_path)
    assert result == True  # Mismatch


def test_quality_mismatch_both_missing():
    # Neither path contains any category-quality combination
    model_path = "/models/unknown/model.safetensors"
    png_path = "/images/unknown/image.png"
    result = TreeMoveCommand.quality_mismatch(model_path, png_path)
    assert result == False  # No mismatch because both are "None"


def test_quality_mismatch_same_none():
    # Both paths return "None" for quality
    model_path = "/models/unknown/model.safetensors"
    png_path = "/images/unknown/image.png"
    result = TreeMoveCommand.quality_mismatch(model_path, png_path)
    assert result == False  # No mismatch


def test_quality_mismatch_case_insensitive():
    # Test case sensitivity
    model_path = "/models/attire_good/model.safetensors"
    png_path = "/images/Attire_Good/image.png"
    result = TreeMoveCommand.quality_mismatch(model_path, png_path)
    assert result == True  # Mismatch if case-sensitive


def test_quality_mismatch_substring():
    # Test when a category-quality is a substring of another
    model_path = "/models/Attire_Good/model.safetensors"
    png_path = "/images/Attire_Goodness/image.png"
    result = TreeMoveCommand.quality_mismatch(model_path, png_path)
    assert result == True  # Mismatch because "Attire_Good" != "None"
