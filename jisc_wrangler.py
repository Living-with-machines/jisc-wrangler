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
from datetime import datetime
from re import compile, IGNORECASE
from tqdm import tqdm  # type: ignore

__version__ = '0.0.1'

# Regex patterns for INPUT DIRECTORIES:
# These should be exhaustive when used case-insenstively (grep -E -i).
# Parts in parentheses are the corresponding standardised output paths.
P_SERVICE = '([A-Z]{4}\\/[0-9]{4}\\/[0-9]{2}\\/[0-9]{2})(\\/)service\\/'
P_SERVICE_SUBDAY = '([A-Z]{4}\\/[0-9]{4}\\/[0-9]{2}\\/[0-9]{2})_[S,V](\\/)service\\/'
P_MASTER = '([A-Z]{4}\\/[0-9]{4}\\/[0-9]{2}\\/[0-9]{2})(\\/)master\\/'
P_MASTER_SUBDAY = '([A-Z]{4}\\/[0-9]{4}\\/[0-9]{2}\\/[0-9]{2})_[S,V](\\/)master\\/'
P_LSIDY = 'lsidy'
P_OSMAPS = 'OSMaps.*?(\\.shp|\\/metadata)\\.xml$'

service_pattern = compile(P_SERVICE, IGNORECASE)
service_subday_pattern = compile(P_SERVICE_SUBDAY, IGNORECASE)
master_pattern = compile(P_MASTER, IGNORECASE)
master_subday_pattern = compile(P_MASTER_SUBDAY, IGNORECASE)
lsidy_pattern = compile(P_LSIDY)
os_maps_pattern = compile(P_OSMAPS)

dir_patterns = [service_pattern, service_subday_pattern, master_pattern,
                master_subday_pattern, lsidy_pattern, os_maps_pattern]

# Working filenames
filename_prefix = 'jw_'
name_logfile = 'jw.log'
name_unmatched_file = filename_prefix + 'unmatched.txt'

# Constants
len_title_code = len('ABCD')


def main():

    try:
        # Prepare for execution.
        args = parse_args()
        initialise(args)

        # Record the prior state of the output directory.
        num_existing_output_files = count_all_files(args.output_dir, "output")

        # Process all of the files under the input directory.
        process_inputs(args)

        # TODO.
        # Check that all of the input files were processed.
        # validate(num_existing_output_files)
        logging.warning("Validation not yet implemented.")

        # # TODO FROM HERE.
        # logging.warning("WRANGLING NOT YET IMPLEMENTED")

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

    # Iterate over the unique stubs.
    leftover_files = all_files
    leftover_stubs = all_stubs
    msg = f"Processing {len(unique_stubs)} unique title code "
    msg = msg + "directory..." if len(unique_stubs) == 1 else "directories..."
    print(msg)
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

    logging.warning("Wrangling not yet implemented.")


def remove_duplicates(strs, sorted=False):
    """Remove duplicates from a list."""

    unique_strs = list(set(strs))

    if sorted:
        unique_strs.sort()
    return unique_strs


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


def remove_duplicate_stubs(stubs, sorted=False):

    unique_stubs = list(set(stubs))
    logging.info(f"Found {len(unique_stubs)} unique file path stubs.")

    if sorted:
        unique_stubs.sort()
    return unique_stubs


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
    if not description:
        description = str(dir)
    logging.info(f"Counted {ret} files under the {description} directory.")
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

    print("This is JISC Wrangler")

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
