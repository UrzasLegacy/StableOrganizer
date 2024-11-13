import os
import time
import logging
import json
import hashlib
import multiprocessing
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

ROOT_DIRECTORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)

hash_json_filepath = r"AliHashes.json"
duplicates_json_filepath = r"AliHashDuplicates.json"
root_directory = r"X:\SD_X\models\checkpoints\_IN\_Staging1"


def collect_safetensors_filepaths(root_dir):
    safetensors_filepaths = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.safetensors'):
                safetensors_filepaths.append(os.path.join(dirpath, filename))
    return safetensors_filepaths


def process_files(file_paths, max_workers=None):
    if max_workers is None:
        max_workers = multiprocessing.cpu_count()

    hash_dict = load_json_file(hash_json_filepath, {})
    duplicates_dict = defaultdict(list)

    def _process_file(filepath):
        hash_value = retrieve_sha256_hash(filepath,force_compute=True)
        base_name = os.path.basename(filepath)
        model_name, ext = os.path.splitext(base_name)
        hash_dict[hash_value] = (model_name, os.path.abspath(filepath))
        duplicates_dict[hash_value].append(os.path.abspath(filepath))

    # with ThreadPoolExecutor(max_workers=max_workers) as executor:
    #     executor.map(process_file, file_paths)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(_process_file, filepath): filepath for filepath in file_paths}
        for future in tqdm(as_completed(future_to_file), total=len(file_paths), ncols=80, leave=False, desc="Processing files"):
            try:
                future.result()
            except Exception as e:
                filepath = future_to_file[future]
                logger.error(f"Error processing {filepath}: {e}")

    sorted_hash_dict = dict(sorted(hash_dict.items(), key=lambda item: item[1][0]))

    # Identify and log duplicates
    duplicate_files = {hash_value: paths for hash_value, paths in duplicates_dict.items() if len(paths) > 1}

    save_json_file(hash_json_filepath, sorted_hash_dict)
    save_json_file(duplicates_json_filepath, duplicate_files)
    # Log duplicate files
    for hash_value, paths in duplicate_files.items():
        logger.warning(f"Duplicate hash {hash_value} found in files: {paths}")


def retrieve_sha256_hash(filepath, ads_stream_name="sha256", create_alternate_data_stream=True, create_hash_file=False, force_compute=False):
    def _compute_hash(filepath, create_alternate_data_stream, create_hash_file):
        try:
            sha256_hash = hashlib.sha256()
            with open(filepath, 'rb') as f:
                for byte_block in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(byte_block)
            hash = sha256_hash.hexdigest()

            if create_hash_file:
                _write_hash_file(filepath, hash)
            if create_alternate_data_stream:
                _write_hash_ADS(filepath, hash)

            return hash
        except Exception as e:
            logger.error(f"Hash could not be computed: {e}")
            return None

    def _write_hash_ADS(filepath, stream_value, stream_name=ads_stream_name,):
        ads_path = f"{filepath}:{stream_name}"
        try:
            with open(ads_path, 'w') as ads:
                ads.write(stream_value)
        except Exception as e:
            logger.error(f"Error setting alternate data stream on file {ads_path}: {e}")

    def _read_hash_ADS(filepath, stream_name):
        ads_path = f"{filepath}:{stream_name}"
        try:
            with open(ads_path, 'r') as ads:
                content = ads.read()
                return content
        except FileNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error reading ADS {ads_path}: {e}")
            return None

    def _read_hash_file(filepath):
        file_no_ext = os.path.splitext(filepath)[0]
        hash_file_path = file_no_ext + ".sha256"
        if os.path.isfile(hash_file_path):
            try:
                with open(hash_file_path, "r") as f:
                    content = f.read().strip()
                logger.info(f"Hash retrieved from hash file {hash_file_path}: {content}")
                return content
            except OSError as e:
                logger.error(f"Error reading existing hash file {hash_file_path}: {e}")

    def _write_hash_file(filepath, hash_value):
        file_no_ext = os.path.splitext(filepath)[0]
        hash_file_path = file_no_ext + ".sha256"
        try:
            with open(hash_file_path, "w") as f:
                f.write(hash_value)
                logger.info(f"Hash computed and set to hash file {hash_file_path}: {hash_value}")
        except OSError as e:
            logger.error(f"Error writing to hash file: {e}")


    if force_compute:
        model_hash = _compute_hash(filepath, create_alternate_data_stream, create_hash_file)
    else:
        model_hash = _read_hash_ADS(filepath, ads_stream_name)
        if not model_hash:
            model_hash = _read_hash_file(filepath)
            if not model_hash:
                model_hash = _compute_hash(filepath, create_alternate_data_stream, create_hash_file)

    return model_hash


def load_json_file(file: str, default=None, relative_path: bool = True):
    """Reads a json file and returns the json dict, stripping out "//" comments first."""
    if relative_path:
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), file)
    else:
        filepath = file
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='UTF-8') as file:
            config = re.sub(r"(?:^|\s)//.*", "", file.read(), flags=re.MULTILINE)
        return json.loads(config)
    return default


def save_json_file(file: str, data: dict, relative_path: bool=True):
    if relative_path:
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), file)
    else:
        filepath = file
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='UTF-8') as file:
        json.dump(data, file, sort_keys=False, indent=2, separators=(",", ": "))


def main():
    safetensors_files = collect_safetensors_filepaths(root_directory)
    start_time = time.time()
    process_files(safetensors_files, 4)
    print(f"Elapsed: {time.time() - start_time}")
    input("Press enter to exit...")


if __name__ == "__main__":
    main()