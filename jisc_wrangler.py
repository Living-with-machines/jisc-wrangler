"""
JISC Wrangler

A command line tool for restructuring mangled & duplicated
JISC newspaper XML files.
"""
import os
from sys import exit
import logging
import argparse
from pathlib import Path
from shutil import move, copy
from distutils.dir_util import copy_tree
from datetime import datetime
from re import compile, IGNORECASE
from hashlib import md5
from tqdm import tqdm  # type: ignore

__version__ = '0.0.1'

# Regex patterns for INPUT DIRECTORIES:
# These should be exhaustive when used case-insenstively (grep -E -i).
# Parts in parentheses are the corresponding standardised output paths.
P_SERVICE = os.path.join(
    '([A-Z]{4}', '[0-9]{4}', '[0-9]{2}', '[0-9]{2})(', ')service', '')
P_MASTER = os.path.join(
    '([A-Z]{4}', '[0-9]{4}', '[0-9]{2}', '[0-9]{2})(', ')master', '')
P_SUBDAY = '_[S,V]'
P_SERVICE_SUBDAY = os.path.join('([A-Z]{4}', '[0-9]{4}', '[0-9]{2}',
                                '[0-9]{2})' + P_SUBDAY + '(', ')service', '')
P_MASTER_SUBDAY = os.path.join('([A-Z]{4}', '[0-9]{4}', '[0-9]{2}',
                               '[0-9]{2})' + P_SUBDAY + '(', ')master', '')
P_LSIDY = 'lsidy'
P_OSMAPS = os.path.join('OSMaps.*?(\\.shp|', 'metadata)\\.xml$')

service_pattern = compile(P_SERVICE, IGNORECASE)
service_subday_pattern = compile(P_SERVICE_SUBDAY, IGNORECASE)
master_pattern = compile(P_MASTER, IGNORECASE)
master_subday_pattern = compile(P_MASTER_SUBDAY, IGNORECASE)
lsidy_pattern = compile(P_LSIDY)
os_maps_pattern = compile(P_OSMAPS)

dir_patterns = [service_pattern, service_subday_pattern, master_pattern,
                master_subday_pattern, lsidy_pattern, os_maps_pattern]

# Regex patterns for the STANDARDISED OUTPUT DIRECTORIES:
# Note matches only end of line $.
P_STANDARD_SUBDIR = os.path.join(
    '[A-Z]{4}', '[0-9]{4}', '[0-9]{2}', '[0-9]{2}$')
standard_subdir_pattern = compile(P_STANDARD_SUBDIR)

# Working filenames
filename_prefix = 'jw_'
name_logfile = 'jw.log'
name_unmatched_file = filename_prefix + 'unmatched.txt'
name_ignored_file = filename_prefix + 'ignored.txt'
name_duplicates_file = filename_prefix + 'duplicates.txt'

# Constants
len_title_code = len('ABCD')
len_title_code_dir = len(os.path.join('ABCD', ''))
len_title_code_y_dir = len(os.path.join('ABCD', 'YYYY', ''))
len_title_code_ym_dir = len(os.path.join('ABCD', 'YYYY', 'MM', ''))
len_title_code_ymd_dir = len(os.path.join('ABCD', 'YYYY', 'MM', 'DD', ''))
len_subday_subscript = len('_X')


def main():

    try:
        # Prepare for execution.
        args = parse_args()
        initialise(args)

        # Record the prior state of the output directory.
        num_existing_output_files = count_all_files(args.output_dir, "output")

        # Process all of the files under the input directory.
        process_inputs(args)

        # Check that all of the input files were processed.
        validate(num_existing_output_files, args)

    except Exception as e:
        logging.exception(str(e))
        print(f"ERROR: {str(e)}")
        exit()


def process_inputs(args):
    """
    Process all of the files under the input directory.

    Args:
        args    (Namespace): Namespace object containing runtime parameters.
    """

    # Look at the input file paths & extract the 'stubs'.
    all_files = list_all_files(args.input_dir, sorted=True)
    logging.info(f"Found {len(all_files)} input files.")
    all_stubs = extract_file_path_stubs(
        all_files, args.working_dir, sorted=True)

    # Get a sorted list of _unique_ file path stubs.
    unique_stubs = remove_duplicates(all_stubs, sorted=True)
    logging.info(f"Found {len(unique_stubs)} unique file path stubs.")

    # Print the number of titles to be processed (and a progress bar).
    msg = f"Processing {len(unique_stubs)} unique title code "
    msg += "directory..." if len(unique_stubs) == 1 else "directories..."
    print(msg)

    # Iterate over the unique stubs.
    leftover_files = all_files
    leftover_stubs = all_stubs
    for stub in tqdm(unique_stubs):

        # Count the number of leftover stubs matching this unique stub.
        i = count_matches_in_list(stub, leftover_stubs)

        # Sanity check that we have a non-zero number of matches.
        if i == 0:
            msg = f"Found zero matches for the unique stub: {stub}"
            raise RuntimeError(msg)

        # Process all of the leftover files matching the current stub.
        process_stub(stub, leftover_files[:i], args)

        # When all full paths corresponding to the current stub have been
        # processed, update the lists of leftover files & stubs.
        leftover_files = leftover_files[i:]
        leftover_stubs = leftover_stubs[i:]

    if len(leftover_files) != 0:
        msg = f"All stubs processed but {len(leftover_files)} leftover files."
        raise RuntimeError(msg)


def process_stub(stub, full_paths, args):
    """
    Process a single file path stub.

    The 'stub' is the initial part of the path, up to & including the newspaper
    title code.

    Args:
        stub             (str): A file path stub.
        full_paths (list[str]): A list of full paths to a JISC newspaper files
                                corresponding to the given stub.
        args       (Namespace): Namespace object containing runtime parameters.
    """

    logging.info(f">>> Processing stub: {stub}")
    # Count the number of leftover stubs corresponding to this stub.

    while len(full_paths) != 0:

        full_path = full_paths[0]
        processed = process_full_path(full_path, len(stub), args)

        logging.debug(
            f"Processing of full path: {full_path} returned: {processed}")

        # Remove the full_paths that have been processed. If processed is
        # None,  only a single full path was processed. Otherwise, all of the
        # full_paths that begin with the processed string have been processed.
        if processed is None:
            num_processed_paths = 1
        else:
            num_processed_paths = count_matches_in_list(processed, full_paths)
        full_paths = full_paths[num_processed_paths:]

    logging.info(f">>> Finished processing stub: {stub}")


def process_full_path(full_path, stub_length, args):
    """
    Process a full path to a JISC newspaper file.

    This function implements the core wrangling & deduplification algorithm:
    - ignore non-newspaper files
    - determine the maximal portion of the full path that can be processed in a
    single copy operation:
        - if the full path points to a duplicate file, add it to the list of
        duplicates and continue.
        - if the appropriate (standardised) output subdirectory already exists,
        process the individual file given by the full path.
        - otherwise, process the maximal subdirectory of the full path.

    Here 'processing' means copying the input file or subdirectory to the
    appropriate output directory and then standardising the output directory
    structure. This standardisation procedure makes it possible to determine
    how subsequent full paths should be processed via the above algorithm.

    Args:
        full_path   (str): The full path to a JISC newspaper file.
        stub_length (int): The number of chars in the full_path up to &
                           including the title code.
        args  (Namespace): Namespace object containing runtime parameters.

    Returns:
        str: the portion of the full path that was processed, or None if
        the full path points to a duplicate file.
    """

    logging.debug(f"Processing full path: {full_path}")

    # If the full path matches the P_OSMAPS pattern, ignore it.
    if os_maps_pattern.search(full_path):
        ignore_file(full_path, args.working_dir)
        return full_path

    # Get the part of the full path that can be handled in this step by
    # inspecting the existing output directory structure.
    from_to = determine_from_to(full_path, stub_length, args.output_dir)

    # If the "copy from" is the whole of the full_path, handle a single file
    if from_to[0] is None:
        process_duplicate_file(full_path, from_to, args.working_dir)
    elif from_to[0] == full_path:
        process_single_file(from_to, args.dry_run)
    else:
        process_subdir(from_to, args.dry_run)
    return from_to[0]


def determine_from_to(full_path, stub_length, output_dir):
    """
    Determine what part of the given full path can be handled in a single copy
    operation by examining the existing output directory structure.

    Args:
        full_path   (str): The full path to a JISC newspaper file.
        stub_length (int): The number of chars in the full_path up to &
                           including the title code.
        output_dir  (str): The output directory.

    Returns:
        str: the part of the full path that can be handled in a single copy
        operation.
        str: the target output subdirectory for the copy operation, or None if
        a matching output file already exists.
    """

    # TODO: Handle the lsidy_pattern.
    if lsidy_pattern.search(full_path):
        raise NotImplementedError("LSIDY pattern not yet handled.")

    # Subdirectory suffix lengths (including a trailing slash) are:
    #   - 5 (title code)
    #   - 10 (title code plus year)
    #   - 13 (title code plus year & month)
    #   - 16 (title code plus year, month & day).
    for len_subdir in [len_title_code_dir, len_title_code_y_dir,
                       len_title_code_ym_dir, len_title_code_ymd_dir]:
        out_dir = target_output_subdir(full_path, len_subdir, output_dir)
        if not os.path.isdir(out_dir):
            len_path = stub_length + len_subdir - len_title_code

            # If the full_path matches a subday pattern and the day
            # subdir is to be copied, extend the length of the 'copy from'
            # path by the length of the subscript.
            if len_subdir == 16:
                if (service_subday_pattern.search(full_path) or
                        master_subday_pattern.search(full_path)):
                    len_path += len_subday_subscript

            return full_path[:len_path], out_dir

    # If the target subdirectory exists, but not the file, then we can copy
    # only the file itself, unless a file with the same name alredy exists.
    target_file = os.path.join(out_dir, os.path.basename(full_path))
    if not os.path.isfile(target_file):
        return full_path, out_dir

    # If a matching file already exists, return None for the
    return None, target_file


def process_single_file(from_to, dry_run):
    """
    Process a single file by copying to the appropriate output directory.

    Args:
        from_to (str, str): The part of the full path that can be handled in a
                            single copy operation, and the target output
                            subdirectory for the copy.
        dry_run     (bool): Flag indicating whether this is a dry run.
    """

    if not dry_run:
        copy(from_to[0], from_to[1])
    logging.info(f"Copied file from {from_to[0]} to {from_to[1]}")


def process_duplicate_file(full_path, from_to, working_dir):
    """
    Process a duplicate filename that already exists in the output directory.

    Args:
        full_path    (str): The full path to a JISC newspaper file.
        from_to (str, str): The part of the full path that can be handled in a
                            single copy operation, and the target output
                            subdirectory for the copy.
        working_dir  (str): The path to the working directory.
    """

    # Hash both the current file and the existing one in the output directory.
    hash_new = hash_file(full_path)
    hash_original = hash_file(from_to[1])

    # Compare the two hashes. If they're equal, append a line to the duplicates
    # file. Otherwise raise an error.
    if hash_new == hash_original:
        with open(working_file(name_duplicates_file, working_dir), 'a+') as f:
            f.write(f"{from_to[1]} duplicated at {full_path}\n")
        f.close()
        logging.info(f"Added file {full_path} to the duplicates list.")
    else:
        msg = "Conflicting but distinct files detected.\n"
        msg = f"{msg}Input file: {full_path}\n"
        msg = f"{msg}Output subdirectory: {from_to[1]}"
        raise RuntimeError(msg)


def process_subdir(from_to, dry_run):
    """
    Process a subdirectory by copying to the appropriate output directory
    and standardise the subdirectory names.

    Args:
        from_to (str, str): The part of the full path that can be handled in a
                            single copy operation, and the target output
                            subdirectory for the copy.
        dry_run     (bool): Flag indicating whether this is a dry run.
    """

    # If the copy_from is a directory, make a directory with the same name
    # under the output directory and copy its contents. (Note the copy_tree
    # function automatically creates the destination directory.)
    copy_tree(from_to[0], from_to[1], dry_run)
    logging.info(f"Copied directory from {from_to[0]} to {from_to[1]}")

    # Standardise the destination directory structure.
    standardise_output_dirs(from_to[1])


def standardise_output_dirs(output_subdir):
    """
    Standardise the directory structure under an output subdirectory.

    Args:
        output_subdir (str): The output subdirectory to be standardised.
    """

    # Get a list of all directories under the output subdirectory of interest.
    subdirs = list_all_subdirs(output_subdir)

    # Iterate over the list of subdirectories.
    for subdir in subdirs:
        # if a 'SERVICE' or 'MASTER' pattern matches,
        # remove the last subdirectory.
        if (service_pattern.search(subdir) or
            service_subday_pattern.search(subdir) or
            master_pattern.search(subdir) or
                master_subday_pattern.search(subdir)):

            remove_last_subdir(subdir)

        # If a 'SUBDAY' pattern matches, rename the 'subday' directory.
        if (service_subday_pattern.search(subdir) or
                master_subday_pattern.search(subdir)):

            remove_subday_subdir(subdir)

        # TODO:
        # If 'LSIDY' pattern matches, ... (TBD)
        if lsidy_pattern.search(subdir):
            raise NotImplementedError(
                "Standardisation of 'LSIDY' directories not yet implemented")

    # Check that the new subdirectory structure is standard.
    unique_leaf_subdirs = list(
        set([os.path.dirname(f) for f in list_all_files(output_subdir)]))
    for subdir in unique_leaf_subdirs:
        if not standard_subdir_pattern.search(subdir):
            msg = f"Failed to standardise output subdirectory: {subdir}"
            raise RuntimeError(msg)
    logging.info(f"Standardised output directory {output_subdir}")


def remove_last_subdir(path):
    """
    Removes the last subdirectory in the path on the filesystem, moving any
    files contained to the parent directory.

    For example, if the path is '/.../output_dir/0000038/1875/12/01/service/',
    then:
     - all files in the service/ subdirectory are moved to the parent 01/
     - the service/ subdirectory is removed.

    Args:
        path (str): The full path to the subdirectory.
    """

    # Remove any trailing directory separator.
    path = os.path.normpath(path)

    # Make sure we're looking at a directory, not a file.
    if os.path.isfile(path):
        path = os.path.dirname(path)
    if not os.path.isdir(path):
        raise ValueError(f"Path {path} does not exist on the filesystem.")

    move_from_to(from_dir=path, to_dir=os.path.dirname(path))


def remove_subday_subdir(path):
    """
    Removes the subdirectory within the given output path that matches the
    P_SUBDAY pattern and moves its contents to the corresponding directory
    without the subday subscript. The full path is assumed to match either
    the P_SERVICE_SUBDAY or P_MASTER_SUBDAY pattern, so the subscripted
    directory is the last-but-one from the end.

    For example, if the path is '/.../output_dir/PMGZ/1897/06/19_S' then the
    last subdirectory is renamed from '19_S' to '19'.

    Args:
        path (str): The full path to the subscripted subdirectory.

    Raises: ValueError if the subscripted directory name is not found in the
            path.
    """

    # Remove any trailing directory separator.
    path = os.path.normpath(path)

    # Make sure the last-but-one subdirectory matches the expected pattern.
    subscript_dir_path = os.path.dirname(path)
    subday_pattern = compile(P_SUBDAY + '$', IGNORECASE)
    if not subday_pattern.search(subscript_dir_path):
        msg = f"Failed to match subscripted subdirectory:\n{subscript_dir_path}"
        raise ValueError(msg)

    # Remove the last characters (the subscript) from subdirectory name.
    #new_path = os.path.join(subscript_dir_path[:-len_subday_subscript], '')
    to_dir = subscript_dir_path[:-len_subday_subscript]
    move_from_to(from_dir=subscript_dir_path, to_dir=to_dir)


def target_output_subdir(full_path, len_subdir, output_dir):
    """
    Construct the path to an output subdirectory. The subdirectory depth is
    determined by the len_subdir argument.

    Args:
        full_path     (str): The full path to a JISC newspaper file.
        len_subdir    (int): The number of chars in the output subdirectory
                             path after the output directory.
        output_dir    (str): The output directory.
    """

    subdir = standardised_output_subdir(full_path)[:len_subdir]
    return os.path.join(output_dir, subdir)


def standardised_output_subdir(full_path):
    """
    Determine the standardised output subdirectory for a given full path.

    Args:
        full_path   (str): The full path to a JISC newspaper file.
    """

    # Loop over the directory pattens.
    for pattern in dir_patterns:

        # If the directory pattern matches, extract the standardised path.
        s = pattern.search(full_path)
        if s:
            return (s.group(1) + s.group(2)).upper()

    # If no match is found, raise an error.
    msg = f"Failed to compute a standardisation for the full path: {full_path}"
    raise RuntimeError(msg)


def extract_file_path_stubs(paths, working_dir, sorted=False):
    """Construct a list of file path stubs for all directory patterns.

    The 'stub' is the initial part of the path, up to & including the title
    code.

    Returns: a list of strings, one stub for each of the given paths,
    optionally sorted.

    Raises: RuntimeError if any path is not pattern-matched to obtain the stub.
    """

    stubs = flatten([extract_pattern_stubs(p, paths) for p in dir_patterns])

    # Check all files were matched against the known directory patterns.
    if len(paths) != len(stubs):

        # Write the unmatched full paths to a file in the working directory.
        write_unmatched_file(paths, working_dir)
        msg = f"Matched only {len(stubs)} directory patterns out of"
        msg = f"{msg} {len(paths)} files. See the {name_unmatched_file} file."
        raise RuntimeError(msg)

    if sorted:
        stubs.sort()
    return stubs


def extract_pattern_stubs(pattern, paths):
    """Construct a list of file path stubs for a given directory pattern.

    The 'stub' is the initial part of the path, up to & including the title
    code.

    Returns: a list of strings, one stub for each of the given paths.
    """

    # Match on the directory pattern (title code and subdirectories thereof)
    # but extract only the initial part of the path (up to & including the title code).
    ret = [str[0:m.start() + len_title_code]
           for str in paths if (m := pattern.search(str))]
    logging.info(
        f"Found {len(ret)} files matching the {pattern.pattern} pattern.")
    return ret


def validate(num_existing_output_files, args):
    """Validate the processing by comparing the number of input & output files.

    Args:
        num_existing_output_files (int): Number of output files that existed
                                         before processing began.
        args    (Namespace): Namespace object containing runtime parameters.
    """

    # Check all of the input files were processed. Every input file should be
    # in the output directory, the duplicates file or the ignored file.
    num_input_files = count_all_files(args.input_dir)
    logging.info(f"Counted {num_input_files} input files.")

    num_duplicated_files = count_lines(
        working_file(name_duplicates_file, args.working_dir))
    logging.info(f"Counted {num_duplicated_files} duplicated files.")

    num_ignored_files = count_lines(
        working_file(name_ignored_file, args.working_dir))
    logging.info(f"Counted {num_ignored_files} ignored files.")

    num_new_output_files = count_all_files(
        args.output_dir) - num_existing_output_files
    logging.info(f"Counted {num_new_output_files} new output files.")

    num_processed_files = num_new_output_files + \
        num_duplicated_files + num_ignored_files

    if (num_processed_files != num_input_files):
        msg = f"Only {num_processed_files} of {num_input_files} input files"
        raise RuntimeError(f"{msg} were processed.")

    logging.info("All files were processed successfully.")


##
# Utils:
##

def flatten(nested_list):
    """Flatten a list of lists."""

    return [item for sublist in nested_list for item in sublist]


def list_all_files(dir, sorted=False):
    """List all of all files under a given directory, recursively.

    Returns: a list of strings, optionally sorted.
    """

    ret = [str(f) for f in Path(dir).rglob('*') if os.path.isfile(f)]
    if sorted:
        ret.sort()
    return ret


def count_all_files(dir, description=None):
    """Count the total number of files under a given directory."""

    ret = len(list_all_files(dir))
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
    """Move all file from one directory to another, and delete the first
    directory.

    Args:
        from_dir    (str): The path to the source directory.
        to_dir      (str): The path to the target directory.
    """

    # If the target directory does not already exist, create it.
    if not os.path.exists(to_dir):
        Path(to_dir).mkdir(parents=False, exist_ok=True)
        logging.info(f"Created non-subscripted subdirectory at {to_dir}")

    for f in list_all_files(from_dir):
        move(f, to_dir)
    logging.debug(f"Moved all files from: {from_dir} to: {to_dir}")
    Path.rmdir(Path(from_dir).absolute())
    logging.debug(f"Removed directory: {from_dir}.")


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

##
# Working files:
##


def working_file(filename, working_dir):
    """Construct the full path to a working file."""

    return os.path.join(working_dir, filename)


def write_unmatched_file(paths, working_dir):
    """Write out a list of files that do not match any of the directory patterns."""

    for pattern in dir_patterns:
        paths = [str for str in paths if not pattern.search(str)]
    unmatched_file = working_file(name_unmatched_file, working_dir)
    with open(unmatched_file, 'w') as f:
        for path in paths:
            f.write(f"{path}\n")
    f.close()


def ignore_file(full_path, working_dir):
    """Process a file that can be safely ignored."""

    with open(working_file(name_ignored_file, working_dir), 'a+') as f:
        f.write(f"{full_path}\n")
    f.close()
    logging.info(f"Added file {full_path} to the ignored list.")


##
# Setup:
##


def parse_args():
    """Parse arguments from the command line

    Returns: a Namespace object containing parsed command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Restructure mangled & duplicated JISC newspaper XML files"
    )

    parser.add_argument(
        "input_dir",
        help="Input directory containing mangled JISC data",
    )

    parser.add_argument(
        "output_dir",
        help="Output directory to which clean JISC data are written",
    )

    parser.add_argument(
        "--working_dir",
        type=str,
        default=".",
        help="Working directory to which temporary & log files are written",
    )

    parser.add_argument(
        "--dry-run",
        action='store_true',
        help="Perform a dry run (don't copy any files)",
    )

    parser.add_argument(
        "--debug",
        action='store_true',
        help="Run in debug mode (verbose logging)",
    )

    return parser.parse_args()


def initialise(args):
    """
    Set up working directories and logging.
    """

    print(">>> This is JISC Wrangler <<<")

    setup_directories(args)
    setup_logging(args)

    logging.info(f"Input directory: {args.input_dir}")
    logging.info(f"Output directory: {args.output_dir}")
    logging.info(f"Working directory: {args.working_dir}")


def setup_directories(args):
    """
    Prepare working & output directories.
    """

    # Check the input directory path exists.
    if not os.path.exists(args.input_dir):
        raise ValueError("Please provide a valid input directory")

    # Prepare the output directory.
    if not os.path.exists(args.output_dir):
        Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    # Create a timestamped working subdirectory.
    working_subdir = \
        f'{filename_prefix}{datetime.now().strftime("%Y-%m-%d_%Hh-%Mm-%Ss")}'
    working_dir = os.path.join(args.working_dir, working_subdir)
    if not os.path.exists(working_dir):
        Path(working_dir).mkdir(parents=True, exist_ok=True)
        # Set the working_dir argument to the timestamped subdirectory.
        args.working_dir = working_dir


def setup_logging(args):
    """
    Prepare logging.
    """

    # Logging
    level = logging.INFO
    if (args.debug):
        level = logging.DEBUG
    log_full_path = os.path.join(args.working_dir, name_logfile)
    logging.basicConfig(filename=log_full_path, filemode='w',
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        level=level)
    logging.info(
        f"This log file was generated by JISC Wrangler v{__version__}")
    if args.dry_run:
        logging.info("Executing a DRY RUN. No files will be copied.")

    print(f"Logging to the working directory at:\n{log_full_path}")


if __name__ == "__main__":
    main()
