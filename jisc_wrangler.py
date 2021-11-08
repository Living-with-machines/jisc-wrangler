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

        # Look at the input file paths & extract the 'stubs'.
        num_existing_output_files = count_all_files(args.output_dir, "output")
        all_files = list_all_files(args.input_dir, sorted=True)
        logging.info(f"Found {len(all_files)} input files.")
        all_stubs = extract_file_path_stubs(
            all_files, args.working_dir, sorted=True)

        # TODO FROM HERE.
        logging.warning("WRANGLING NOT YET IMPLEMENTED")

    except Exception as e:
        logging.exception(str(e))
        print(f"ERROR: {str(e)}")
        exit()


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
