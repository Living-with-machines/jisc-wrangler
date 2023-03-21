"""
JISC utility functions

utility functions used across the JISC wrangler package
"""

import os
from pathlib import Path
from jisc_wrangler import constants
import logging
from hashlib import md5
from shutil import move
from datetime import datetime

def flatten(nested_list: list) -> list:
    """Flatten a list of lists.

    Args:
        nested_list (list): nested list to flatten.

    Returns:
        list: The flattened list.
    """
    return [item for sublist in nested_list for item in sublist]

def list_files(dir: str, suffix: str="", sorted: bool=False) -> list:
    """List all files under a given directory with a given suffix, recursively.

    Args:
        dir (str): Directory to check.
        suffix (str, optional): file suffix to filter. Defaults to "".
        sorted (bool, optional): Whether to sort the results. Defaults to False.

    Returns:
        list: Files in the target dir.
    """
    ret = [
        str(f)
        for f in Path(dir).rglob(
            '*' + suffix
        )
        if os.path.isfile(f)
    ]
    if sorted:
        ret.sort()
    return ret

def count_lines(file: str) -> int:
    """Count the number of lines in a file or file-like object.

    Args:
        file (str): File name.

    Returns:
        int: Line count.
    """
    if not os.path.isfile(file):
        return 0
    with open(file, 'r') as f:
        ret = sum(1 for _ in f.readlines())
    return ret

def count_all_files(dir: str, description:str=None) -> int:
    """Count the total number of files under a given directory.

    Args:
        dir (str): Direcrtory to check.
        description (_type_, optional): Description of dir. Defaults to None.

    Returns:
        int: File count.
    """
    

    ret = len(list_files(dir))
    if description:
        logging.info(f"Counted {ret} files under the {description} directory.")
    return ret


def count_matches_in_list(prefix: str, str_list: list) -> int:
    """Count how many strings, at the start of a list, begin with a given prefix.

    Args:
        prefix (str): Prefix to check.
        str_list (list): List of strings to check.

    Returns:
        int: String with prefix count.
    """

    if len(str_list) == 0:
        logging.warning("Empty list passed to 'count_matches_in_list'")
        return 0

    i = 0
    while i != len(str_list) and str_list[i].startswith(prefix):
        i += 1
    return i


def remove_duplicates(strs: list, sorted=False) -> list:
    """Remove duplicates from a list.

    Args:
        strs (list): List of strings.
        sorted (bool, optional): Whether to sort the unique strings.
                                 Defaults to False.

    Returns:
        list: _description_
    """

    unique_strs = list(set(strs))

    if sorted:
        unique_strs.sort()
    return unique_strs


def hash_file(path: str, blocksize: int=65536) -> str:
    """Calculate the MD5 hash of a given file

    Args:
        path (str): Path to the file to be hashed.
        blocksize (int, optional): Memory size to read in the file. Defaults to 65536.

    Returns:
        str: The HEX digest hash of the given file
    """
    
    # Instatiate the hashlib module with md5
    hasher = md5()

    # Open the file and instatiate the buffer
    f = open(path, "rb")
    buf = f.read(blocksize)

    # Continue to read in the file in blocks
    while len(buf) > 0:
        hasher.update(buf)  # Update the hash
        buf = f.read(blocksize)  # Update the buffer

    f.close()
    return hasher.hexdigest()


def alt_output_file(file_path: str) -> str:
    """Get alternative file output.

    Args:
        file_path (str): path to file.

    Returns:
        str: The alternative output file path.
    """
    file_path, extension = os.path.splitext(file_path)
    return file_path + constants.alt_filename_suffix + extension


def list_all_subdirs(dir: str) -> list:
    """List subdirectories in given directory.

    Args:
        dir (str): Directory to search.

    Returns:
        list: Subdirectories in dir.
    """
    return [os.path.join(str(d), '') for d in Path(dir).rglob('*')
            if not os.path.isfile(d)]

def move_from_to(from_dir: str, to_dir: str) -> None:
    """Move all files from one directory to another, and delete the first
    directory.

    Args:
        from_dir (str): The path to the source directory.
        to_dir (str): The path to the target directory.
    """

    # If the target directory does not already exist, create it.
    if not os.path.exists(to_dir):
        Path(to_dir).mkdir(parents=False, exist_ok=True)
        logging.info(f"Created subdirectory at {to_dir}")

    for f in list_files(from_dir):
        move(f, to_dir)
    logging.debug(f"Moved all files from: {from_dir} to: {to_dir}")
    Path.rmdir(Path(from_dir).absolute())
    logging.debug(f"Removed directory: {from_dir}.")


def write_unmatched_file(paths: list, working_dir: str) -> None:
    """Write out a list of files that do not match any of the directory patterns.

    Args:
        paths (list): Paths to check.
        working_dir (str): Working directory.
    """
    for pattern in constants.dir_patterns:
        paths = [str for str in paths if not pattern.search(str)]
    unmatched_file = os.path.join(working_dir, constants.name_unmatched_file)
    with open(unmatched_file, 'w') as f:
        for path in paths:
            f.write(f"{path}\n")
    f.close()


def ignore_file(full_path: str, working_dir: str) -> None:
    """Process a file that can be safely ignored.

    Args:
        full_path (str): Full path to the file.
        working_dir (str): Working directory.
    """
    with open(os.path.join(working_dir, constants.name_ignored_file), 'a+') as f:
        f.write(f"{full_path}\n")
    f.close()
    logging.info(f"Added file {full_path} to the ignored list.")

"""Return date if date is in the range [start, end]

    Args:
        start (datetime): the start of the range
        end (datetime): the end of the range
        date (datetime): the date of interest
    """
def date_in_range(start: datetime, end: datetime, date: datetime) -> bool:
    """Check if date is in the range [start, end].

    Args:
        start (datetime): The start of the date range.
        end (datetime): The end of the date range.
        date (datetime): The date of interest.

    Raises:
        ValueError: If start is after end.

    Returns:
        bool: Whether the date is within range..
    """
    
    if start > end:
        raise ValueError(f"Invalid date interval. Start: {start}, End: {end}.")
    return start <= date <= end

def parse_publicaton_date(date_str: str) -> tuple:
    """Parse a date string seperated by '-'.

    Args:
        date_str (str): string to extract date from.

    Returns:
        tuple: Date split on '-'.
    """
    return tuple(date_str.split('-'))