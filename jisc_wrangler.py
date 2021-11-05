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
__version__ = '0.0.1'


# Working filenames
filename_prefix = 'jw_'
name_logfile = 'jw.log'


def main():

    try:
        # Prepare for execution.
        args = parse_args()
        initialise(args)

        num_existing_output_files = count_all_files(args.output_dir, "output")

        # TODO FROM HERE.
        logging.warning("WRANGLING NOT YET IMPLEMENTED")

    except Exception as e:
        logging.exception(str(e))
        print(f"ERROR: {str(e)}")
        exit()


def list_all_files(dir):
    """List all of all files under a given directory, recursively.

    Returns: a list of strings.
    """

    return [str(f) for f in Path(dir).rglob('*') if os.path.isfile(f)]


def count_all_files(dir, description=None):
    """Count the total number of files under a given directory."""

    ret = len(list_all_files(dir))
    if not description:
        description = str(dir)
    logging.info(f"Counted {ret} files under the {description} directory.")
    return ret


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

    print(f"Logging into the working directory at:\n{log_full_path}")


if __name__ == "__main__":
    main()
