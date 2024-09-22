import os
import logging

ROOT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

log_file_path = os.path.join(ROOT_DIRECTORY, "debugging.log")
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file_path),
    ]
)
logger = logging.getLogger(__name__)

import tkinter as tk
from GUI import StableOrganizerApp

if __name__ == "__main__":
    root = tk.Tk()
    app = StableOrganizerApp(root)
    root.mainloop()