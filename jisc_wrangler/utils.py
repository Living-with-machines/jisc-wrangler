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

def flatten(nested_list):
    """Flatten a list of lists."""
    return [item for sublist in nested_list for item in sublist]

def list_files(dir, suffix="", sorted=False):
    """List all files under a given directory with a given suffix, recursively.

    Returns: a list of strings, optionally sorted.
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

def count_lines(file):
    """
    Count the number of lines in a file or file-like object.

    Args:
        file (file or stream): The file to be counted.
    """
    if not os.path.isfile(file):
        return 0
    with open(file, 'r') as f:
        ret = sum(1 for _ in f.readlines())
    return ret

def count_all_files(dir, description=None):
    """Count the total number of files under a given directory."""

    ret = len(list_files(dir))
    if description:
        logging.info(f"Counted {ret} files under the {description} directory.")
    return ret


def count_matches_in_list(prefix, str_list):
    """
    Count how many strings, at the start of a list, begin with a given prefix.
    """

    if len(str_list) == 0:
        logging.warning("Empty list passed to 'count_matches_in_list'")
        return 0

    i = 0
    while i != len(str_list) and str_list[i].startswith(prefix):
        i += 1
    return i


def remove_duplicates(strs, sorted=False):
    """Remove duplicates from a list."""

    unique_strs = list(set(strs))

    if sorted:
        unique_strs.sort()
    return unique_strs


def hash_file(path, blocksize=65536):
    """Calculate the MD5 hash of a given file
    Arguments
    ---------
        path {str, os.path}: Path to the file to be hashed.
        blocksize {int}: Memory size to read in the file (default: 65536)
    Returns
    -------
        hash {str}: The HEX digest hash of the given file
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


def alt_output_file(file_path):
    """Get an alternative output file path.

    Args:
        file_path (str): The standard output file path

    Returns:
        The alternative output file path (string).
    """
    file_path, extension = os.path.splitext(file_path)
    return file_path + constants.alt_filename_suffix + extension


def list_all_subdirs(dir):
    """
    Get a list of all subdirectories in a given directory, recursively.

    Args:
        dir (str): The path to a directory on the filesystem.

    Returns: a list of strings, each with a trailing directory separator.
    """

    return [os.path.join(str(d), '') for d in Path(dir).rglob('*')
            if not os.path.isfile(d)]


def move_from_to(from_dir, to_dir):
    """Move all files from one directory to another, and delete the first
    directory.

    Args:
        from_dir    (str): The path to the source directory.
        to_dir      (str): The path to the target directory.
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


def write_unmatched_file(paths, working_dir):
    """Write out a list of files that do not match any of the directory patterns.
    """
    for pattern in constants.dir_patterns:
        paths = [str for str in paths if not pattern.search(str)]
    unmatched_file = os.path.join(working_dir, constants.name_unmatched_file)
    with open(unmatched_file, 'w') as f:
        for path in paths:
            f.write(f"{path}\n")
    f.close()


def ignore_file(full_path, working_dir):
    """Process a file that can be safely ignored.
    """
    with open(os.path.join(working_dir, constants.name_ignored_file), 'a+') as f:
        f.write(f"{full_path}\n")
    f.close()
    logging.info(f"Added file {full_path} to the ignored list.")

def date_in_range(start, end, date):
    """Return date if date is in the range [start, end]

    Args:
        start (datetime): the start of the range
        end (datetime): the end of the range
        date (datetime): the date of interest
    """
    if start > end:
        raise ValueError(f"Invalid date interval. Start: {start}, End: {end}.")
    return start <= date <= end

def parse_publicaton_date(date_str):
    """Parse a date string"""
    return tuple(date_str.split('-'))