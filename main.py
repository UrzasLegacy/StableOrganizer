VERSION = "1.0"

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

from GUI import ModelOrganizerApp
import tkinter as tk


transformer = {
    "TopTop": "Best",
}

# List of categories
#categories = ["_Meh", "_Okay", "_Good", "_Top", "_TopTop", "_Difficult"]
#types = ["Attire","Character","Concept","Style"]

if __name__ == "__main__":
    #print(png_dir_path_found)
    #os.startfile(png_dir_path_found)
    #print(os.path.split(lora_path_found)[0])
    #os.startfile(os.path.split(lora_path_found)[0])
    #os.startfile(f'explorer /select,"{lora_path_found}"')
    #actor = ACT("MoveProcessedLoras", {"dirs": info_dict.get_dirs(), "specific": "okay","data": [lora_dict,png_dict]})
    #actor = ACT("LogDicts", {"data": [lora_dict,png_dict]})
    #open_to_file(lora_path_found)
    #actor.log_dicts()
    #logger.debug(json.dumps(png_dict,indent=2))
    root = tk.Tk()
    app = ModelOrganizerApp(root)
    root.mainloop()