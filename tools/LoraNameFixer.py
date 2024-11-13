import os
import logging
from AliDictionaries import lora_dict
import json

root_directory = r"s:\A1111\models\Lora\PONY\_Top"

log_file_path = os.path.splitext(os.path.abspath(__file__))[0] + ".log"

logging.basicConfig(
    level=logging.DEBUG,  # Set the minimum log level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Format for log messages
    datefmt='%Y-%m-%d %H:%M:%S',  # Format for timestamps
    handlers=[
        logging.FileHandler(log_file_path)  # Output logs to a file
    ]
)

logger = logging.getLogger(__name__)
logger.propagate = False

def find_safetensors_files(root_directory):
    safetensors_files = []
    for subdir, _, files in os.walk(root_directory):
        for file in files:
            if file.endswith('.safetensors'):
                safetensors_files.append(os.path.join(subdir, file))
    return safetensors_files

def main():
    safetensors_files = find_safetensors_files(root_directory)
    options = ["_Attire", "_Character", "_Concept", "_Style"]

    for filepath in safetensors_files:
        file_name = os.path.basename(filepath)
        if not any(opt in file_name for opt in options):
            print(f"\nCurrent file: {file_name}")
            print("Choose an option to add to the filename:")
            for i, option in enumerate(options):
                print(f"{i + 1}. {option}")
            choice = int(input("Enter the number of your choice: ")) - 1
            if 0 <= choice < len(options):
                base_name, ext = os.path.splitext(file_name)
                new_file_name = f"{base_name}{options[choice]}".replace(" ","_")
                new_full_file_name = f"{new_file_name}{ext}"
                new_file_path = os.path.join(os.path.dirname(filepath), new_full_file_name)
                os.rename(filepath, new_file_path)
                logging.debug(f"Renamed to: {new_full_file_name}")
                # Update the dictionary
                dict_old_name = base_name.replace("Pony_XL_","").replace("SDXL_","")
                dict_new_name = new_file_name.replace("Pony_XL_","").replace("SDXL_","")
                if dict_old_name in lora_dict:
                    lora_dict[dict_new_name] = lora_dict.pop(dict_old_name)
                    logging.debug(f"Updated dictionary: {dict_new_name}: {lora_dict[dict_new_name]}")
                else:
                    print(f"No entry in dictionary for old name: {dict_old_name}")
            else:
                print("Invalid choice, skipping this file.")


if __name__ == "__main__":
    main()
