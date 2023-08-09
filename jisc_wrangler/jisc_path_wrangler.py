"""
JISC Wrangler

A command line tool for restructuring mangled & duplicated
JISC newspaper XML files.
"""
import argparse
import logging
import os
import re
import sys
from datetime import datetime
from distutils.dir_util import copy_tree
from pathlib import Path
from shutil import copy
from typing import Pattern, Union

from tqdm import tqdm  # type: ignore

from jisc_wrangler import constants, logutils, utils


def main():
    try:
        # Prepare for execution.
        args = parse_args()
        initialise(args)

        # Record the prior state of the output directory.
        existing_output_files = utils.count_all_files(args.output_dir, "output")

        # Process all of the files under the input directory.
        process_inputs(args)

        # Check that all of the input files were processed.
        validate(existing_output_files, args)

    except Exception as e:  # pylint: disable=broad-exception-caught
        logging.exception(str(e))
        print(f"ERROR: {str(e)}")
        sys.exit()


def process_inputs(args: argparse.Namespace) -> None:
    """Process all of the files under the input directory.

    Args:
        args (argparse.Namespace): Runtime parameters.

    Raises:
        RuntimeError: If the sub matches == 0.
        RuntimeError: If there are left over files.
    """

    # Look at the input file paths & extract the 'stubs'.
    all_files = utils.list_files(args.input_dir, sort_them=True)
    logging.info("Found %s input files.", len(all_files))

    # Preprocess P_LSIDYV_ANOMALY files to correct the anomalous title code.
    fix_anomalous_title_codes(all_files, args.working_dir)

    all_stubs = extract_file_path_stubs(all_files, args.working_dir, sort_them=True)

    # Get a sorted list of _unique_ file path stubs.
    unique_stubs = utils.remove_duplicates(all_stubs, sort_them=True)
    logging.info("Found %s unique file path stubs.", len(unique_stubs))

    # Print the number of titles to be processed (and a progress bar).
    msg = f"Processing {len(unique_stubs)} unique title code "
    msg += "directory..." if len(unique_stubs) == 1 else "directories..."
    print(msg)

    # Iterate over the unique stubs.
    leftover_files = all_files
    leftover_stubs = all_stubs
    for stub in tqdm(unique_stubs):
        # Count the number of leftover stubs matching this unique stub.
        i = utils.count_matches_in_list(stub, leftover_stubs)

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


def process_stub(stub: str, full_paths: list, args: argparse.Namespace) -> None:
    """Process a single file path stub.

    The 'stub' is the initial part of the path, up to & including the newspaper
    title code.

    Args:
        stub (str): A file stub path.
        full_paths (list): A list of full paths to a JISC newspaper file
        corresponding to the given stub.
        args (argparse.Namespace): Namespace object containing runtime
        parameters.
    """

    logging.info(">>> Processing stub: %s", stub)
    # Count the number of leftover stubs corresponding to this stub.

    while len(full_paths) != 0:
        full_path = full_paths[0]
        processed = process_full_path(full_path, len(stub), args)

        logging.debug("Processing of full path: %s returned: %s", full_path, processed)

        # Remove the full_paths that have been processed. If processed is
        # None,  only a single full path was processed. Otherwise, all of the
        # full_paths that begin with the processed string have been processed.
        if processed is None:
            num_processed_paths = 1
        else:
            num_processed_paths = utils.count_matches_in_list(processed, full_paths)
        full_paths = full_paths[num_processed_paths:]

    logging.info(">>> Finished processing stub: %s", stub)


def process_full_path(
    full_path: str, stub_length: int, args: argparse.Namespace
) -> Union[str, None]:
    """Process a full path to a JISC newspaper file.

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
        full_path (str): The full path to a JISC newspaper file.
        stub_length (int): The number of chars in the full_path up to &
                           including the title code.
        args (argparse.Namespace): Namespace object containing runtime
                            parameters.

    Returns:
        str: The portion of the full path that was processed, or None if
        the full path points to a duplicate file.
    """

    logging.debug("Processing full path: %s", full_path)

    # If the full path matches the P_OSMAPS pattern, ignore it.
    if constants.OS_MAPS_PATTERN.search(full_path):
        utils.ignore_file(full_path, args.working_dir)
        return full_path

    # Get the part of the full path that can be handled in this step by
    # inspecting the existing output directory structure.
    from_to = determine_from_to(full_path, stub_length, args.output_dir)

    # If the "copy from" is the whole of the full_path, handle a single file
    if from_to[0] is None:
        process_duplicate_file(full_path, from_to, args.working_dir, args.dry_run)
    elif from_to[0] == full_path:
        process_single_file(from_to, args.dry_run)
    else:
        process_subdir(from_to, args.dry_run)
    return from_to[0]


def determine_from_to(full_path: str, stub_length: int, output_dir: str) -> tuple:
    """Determine what part of the given full path can be handled in a single
    copy operation by examining the existing output directory structure.

    Args:
        full_path (str): The full path to a JISC newspaper file.
        stub_length (int): The number of chars in the full_path up to &
                           including the title code.
        output_dir (str): The output directory.

    Returns:
        tuple: The part of the full path that can be handled in a single copy
               operation and the target output subdirectory for the copy
               operation, or None if a matching output file already exists.
    """

    # Handle lsidvv files one at a time because their full paths do not include
    # YYYY/MM/DD subdirectories.
    if constants.LSIDYV_PATTERN.search(full_path):
        # The length of the target subdirectory in this case always includes
        # the year, month and day (because we're processing a single file).
        len_subdir = constants.LEN_TITLE_CODE_YMD_DIR
        out_dir = target_output_subdir(full_path, len_subdir, output_dir)

        # Create the output directory if it doesn't already exist.
        if not os.path.isdir(out_dir):
            Path(out_dir).mkdir(parents=True, exist_ok=True)
            logging.info("Created subdirectory at %s", out_dir)

    # Handle regular (i.e. non-lsidyv_pattern) files by checking which output
    # subdirectories already exist.

    # Subdirectory suffix lengths (including a trailing slash) are:
    #   - 5 (title code)
    #   - 10 (title code plus year)
    #   - 13 (title code plus year & month)
    #   - 16 (title code plus year, month & day).

    # Iterate over these subdirectory suffixes in order of increasing length and
    # handle the case where the target subdirectory does not yet exist.
    else:
        len_titles = [
            constants.LEN_TITLE_CODE_DIR,
            constants.LEN_TITLE_CODE_Y_DIR,
            constants.LEN_TITLE_CODE_YM_DIR,
            constants.LEN_TITLE_CODE_YMD_DIR,
        ]
        for len_subdir in len_titles:
            # Get the target output directory for this file (full_path) assuming
            # the current subdirectory depth.
            out_dir = target_output_subdir(full_path, len_subdir, output_dir)

            # If that target subdirectory doesn't already exist...
            if not os.path.isdir(out_dir):
                # ...then that's the part of the full_path that can be handled.
                len_path = stub_length + len_subdir - constants.LEN_TITLE_CODE

                # Handle the case where the path matches the subday pattern.
                # If the full_path matches a subday pattern and the day
                # subdir is to be copied, extend the length of the 'copy from'
                # path by the length of the subscript.
                if len_subdir == constants.LEN_TITLE_CODE_YMD_DIR:
                    if constants.SERVICE_SUBDAY_PATTERN.search(
                        full_path
                    ) or constants.MASTER_SUBDAY_PATTERN.search(full_path):
                        len_path += constants.LEN_SUBDAY_SUBSCRIPT

                return full_path[:len_path], out_dir

    # If the target subdirectory exists, but not the file, then we can copy
    # only the file itself, unless a file with the same name alredy exists.
    target_file = os.path.join(out_dir, os.path.basename(full_path))
    if not os.path.isfile(target_file):
        return full_path, out_dir

    # If a matching file already exists, return None to indicate that no
    # files can be handled in a copy operation.
    return None, target_file


def process_single_file(from_to: tuple, dry_run: bool) -> None:
    """Process a single file by copying to the appropriate output directory.

    Args:
        from_to (tuple): The part of the full path that can be handled in a
                         single copy operation, and the target output
                         subdirectory for the copy.
        dry_run (bool): Whether this is a dry run.
    """
    if not dry_run:
        copy(from_to[0], from_to[1])
    logging.info("Copied file from %s to %s", from_to[0], from_to[1])


def process_duplicate_file(
    full_path: str, from_to: tuple, working_dir: str, dry_run: bool
) -> None:
    """Process a duplicate file that already exists in the output directory.

    Args:
        full_path (str): The full path to a JISC newspaper file.
        from_to (tuple): The part of the full path that can be handled in a
                         single copy operation, and the target output
                         subdirectory for the copy.
        working_dir (str): The path to the working directory.
        dry_run (bool): Flag indicating whether this is a dry run
    """

    # Hash both the current file and the existing one in the output directory.
    hash_new = utils.hash_file(full_path)
    hash_original = utils.hash_file(from_to[1])

    # Compare the two hashes.
    if hash_new == hash_original:
        # If they're equal, append a line to the duplicates file.
        with open(
            os.path.join(working_dir, constants.NAME_DUPLICATES_FILE),
            "a+",
            encoding="utf-8",
        ) as openfile:
            openfile.write(f"{from_to[1]} duplicated at {full_path}\n")
        logging.info("Added file %s to the duplicates list.", full_path)
    else:
        # Otherwise, log a warning and modify the output filename of the dupe.
        msg = "Conflicting but distinct files detected.\n"
        logging.warning(
            "%sInput file: %s\nConflicts with: %s", msg, full_path, from_to[1]
        )
        alt_from_to = (full_path, utils.alt_output_file(from_to[1]))
        process_single_file(alt_from_to, dry_run)


def process_subdir(from_to: tuple, dry_run: bool) -> None:
    """Process a subdirectory by copying to the appropriate output directory
    and standardise the subdirectory names.

    Args:
        from_to (tuple): The part of the full path that can be handled in a
                         single copy operation, and the target output
                         subdirectory for the copy.
        dry_run (bool): Flag indicating whether this is a dry run.
    """

    # If the copy_from is a directory, make a directory with the same name
    # under the output directory and copy its contents. (Note the copy_tree
    # function automatically creates the destination directory.)
    copy_tree(src=from_to[0], dst=from_to[1], dry_run=dry_run)
    logging.info("Copied directory from %s to %s", from_to[0], from_to[1])

    # Standardise the destination directory structure.
    if not dry_run:
        standardise_output_dirs(from_to[1])


def standardise_output_dirs(output_subdir: str) -> None:
    """Standardise the directory structure under an output subdirectory.

    Args:
        output_subdir (str): The output subdirectory to be standardised.
    """

    # Get a list of all directories under the output subdirectory of interest.
    subdirs = utils.list_all_subdirs(output_subdir)

    # Iterate over the list of subdirectories.
    for subdir in subdirs:
        # if a 'SERVICE' or 'MASTER' pattern matches,
        # remove the last subdirectory.
        if (
            constants.SERVICE_PATTERN.search(subdir)
            or constants.SERVICE_SUBDAY_PATTERN.search(subdir)
            or constants.MASTER_PATTERN.search(subdir)
            or constants.MASTER_SUBDAY_PATTERN.search(subdir)
        ):
            remove_last_subdir(subdir)

        # If a 'SUBDAY' pattern matches, rename the 'subday' directory.
        if constants.SERVICE_SUBDAY_PATTERN.search(
            subdir
        ) or constants.MASTER_SUBDAY_PATTERN.search(subdir):
            remove_subday_subdir(subdir)

        # No standardisation needed in the case of lsidyv files.
        if constants.LSIDYV_PATTERN.search(subdir):
            raise NotImplementedError(
                "Standardisation of 'LSIDYV' directories implemented"
            )

    # Check that the new subdirectory structure is standard.
    unique_leaf_subdirs = list(
        set(os.path.dirname(f) for f in utils.list_files(output_subdir))
    )
    for subdir in unique_leaf_subdirs:
        if not constants.STANDARD_SUBDIR_PATTERN.search(subdir):
            msg = f"Failed to standardise output subdirectory: {subdir}"
            raise RuntimeError(msg)
    logging.info("Standardised output directory %s", output_subdir)


def remove_last_subdir(path: str) -> None:
    """Removes the last subdirectory in the path on the filesystem, moving any
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

    utils.move_from_to(from_dir=path, to_dir=os.path.dirname(path))


def remove_subday_subdir(path: str) -> None:
    """Removes the subdirectory within the given output path that matches the
    P_SUBDAY pattern and moves its contents to the corresponding directory
    without the subday subscript. The full path is assumed to match either
    the P_SERVICE_SUBDAY or P_MASTER_SUBDAY pattern, so the subscripted
    directory is the last-but-one from the end.

    For example, if the path is '/.../output_dir/PMGZ/1897/06/19_S' then the
    last subdirectory is renamed from '19_S' to '19'.

    Args:
        path (str): The full path to the subscripted subdirectory.

    Raises:
           ValueError: If the subscripted directory name is not found in the
                       path.
    """

    # Remove any trailing directory separator.
    path = os.path.normpath(path)

    # Make sure the last-but-one subdirectory matches the expected pattern.
    subscript_dir_path = os.path.dirname(path)
    subday_pattern = re.compile(constants.P_SUBDAY + "$", re.IGNORECASE)
    if not subday_pattern.search(subscript_dir_path):
        msg = f"Failed to match subscripted subdirectory:\n{subscript_dir_path}"
        raise ValueError(msg)

    # Remove the last characters (the subscript) from subdirectory name.
    # new_path = os.path.join(subscript_dir_path[:-len_subday_subscript], '')
    to_dir = subscript_dir_path[: -constants.LEN_SUBDAY_SUBSCRIPT]
    utils.move_from_to(from_dir=subscript_dir_path, to_dir=to_dir)


def target_output_subdir(full_path: str, len_subdir: int, output_dir: str) -> str:
    """Construct the path to an output subdirectory. The subdirectory depth is
    determined by the len_subdir argument.

    Args:
        full_path (str): The full path to a JISC newspaper file.
        len_subdir (int): The number of chars in the output subdirectory
                          path after the output directory.
        output_dir (str): The output directory.

    Returns:
        str: The output directory.
    """
    subdir = standardised_output_subdir(full_path)[:len_subdir]
    return os.path.join(output_dir, subdir)


def standardised_output_subdir(full_path: str) -> str:
    """Determine the standardised output subdirectory for a given full path.

    Args:
        full_path (str): The full path to a JISC newspaper file.

    Raises:
        RuntimeError: When no match is found.

    Returns:
        str: The standardised path.
    """
    # Loop over the directory pattens.
    for pattern in constants.DIR_PATTERNS:
        # If the directory pattern matches, extract the standardised path.
        searched_pattern = pattern.search(full_path)
        if searched_pattern:
            if pattern == constants.LSIDYV_PATTERN:
                # Handle the lsidvy pattern by inspecting the filename.
                filename = os.path.basename(full_path)
                title_code, year, month = filename.split("-")[:3]
                day = filename.split("-")[-1].split(".")[0][: constants.LEN_DAY]
                return os.path.join(title_code.upper(), year, month, day, "")

            return (searched_pattern.group(1) + searched_pattern.group(2)).upper()

    # If no match is found, raise an error.
    msg = f"Failed to compute a standardisation for the full path: {full_path}"
    raise RuntimeError(msg)


def extract_file_path_stubs(
    paths: list, working_dir: str, sort_them: bool = False
) -> list:
    """Construct a list of file path strubs for all directory patterns.

    The 'stub' is the initial part of the path, up to & including the title
    code.

    Args:
        paths (list): The paths to directorys containig stubs.
        working_dir (str): The working directory.
        sort_them (bool, optional): Whether the retuned stubs should be sorted.
                                 Defaults to False.

    Raises:
        RuntimeError: The lengths of stubs and paths do not match.

    Returns:
        list: stubs.
    """

    stubs = utils.flatten(
        [extract_pattern_stubs(p, paths) for p in constants.DIR_PATTERNS]
    )

    # Check all files were matched against the known directory patterns.
    if len(paths) != len(stubs):
        # Write the unmatched full paths to a file in the working directory.
        utils.write_unmatched_file(paths, working_dir)
        msg = f"Matched only {len(stubs)} directory patterns out of"
        msg = f"{msg} {len(paths)} files. See the {constants.NAME_UNMATCHED_FILE} file."
        raise RuntimeError(msg)

    if sort_them:
        stubs.sort()
    return stubs


def extract_pattern_stubs(pattern: Pattern, paths: list) -> list:
    """Construct a list of file path stubs for a given directory pattern.

    The 'stub' is the initial part of the path, up to & including the title
    code.

    Args:
        pattern (Pattern): The pattern to search for.
        paths (list): A list of paths to search.

    Returns:
        list: stubs for each of the given paths.
    """

    if pattern == constants.LSIDYV_PATTERN:
        # Handle the lsidyv pattern.
        ret = [str[0 : mpat.end()] for str in paths if (mpat := pattern.search(str))]
    else:
        # Match on the directory pattern (title code & subdirectories thereof)
        # but extract only the initial part of the path (up to & including the
        # title code).
        ret = [
            str[0 : mpat.start() + constants.LEN_TITLE_CODE]
            for str in paths
            if (mpat := pattern.search(str))
        ]

    logging.info("Found %s files matching the %s pattern.", len(ret), pattern)
    return ret


def fix_anomalous_title_codes(paths: list, working_dir: str) -> None:
    """Correct the anomalous title codes in list and on disk.

    Args:
        paths (list): A list of paths to search.
        working_dir (str): The working directory.
    """

    count = 0
    for index, path in enumerate(paths):
        if constants.LISIDYV_ANOMALY_PATTERN.search(path):
            # Correct the title code anomaly.
            new_path = fix_title_code_anomaly(path, working_dir)

            # Copy the anomalous file to the working directory.
            Path(os.path.dirname(new_path)).mkdir(parents=True, exist_ok=True)
            copy(path, new_path)

            # Update the paths list element to refer to the copied file.
            paths[index] = new_path

            logging.debug("Copied anomalous path %s to %s", path, new_path)
            count += 1

    logging.info("Fixed %s anomalous paths.", count)


def fix_title_code_anomaly(path: str, working_dir: str) -> str:
    """Fix anomaly in title code.

    Args:
        paths (str): A list of paths to search.
        working_dir (str): The working directory.

    Raises:
        ValueError: When an anamalous title code is found.

    Returns:
        str: Corrected path.
    """

    mpat = constants.LISIDYV_ANOMALY_PATTERN.search(path)
    if not mpat:
        raise ValueError(f"Anomalous title code not found in {path}")

    return os.path.join(
        working_dir,
        path[mpat.start() : mpat.end() - 2] + path[mpat.end() - 1 :],
    )


def validate(num_existing_output_files: int, args: argparse.Namespace) -> None:
    """Validate the processing by comparing the number of input & output files.

    Args:
        num_existing_output_files (int): Number of output files that existed
                                        before processing began.
        args    (argparse.Namespace): Runtime parameters.
    """

    # Check all of the input files were processed. Every input file should be
    # in the output directory, the duplicates file or the ignored file.
    num_input_files = utils.count_all_files(args.input_dir)
    logging.info("Counted %s input files.", num_input_files)

    num_duplicated_files = utils.count_lines(
        os.path.join(args.working_dir, constants.NAME_DUPLICATES_FILE)
    )
    logging.info("Counted %s duplicated files.", num_duplicated_files)

    num_ignored_files = utils.count_lines(
        os.path.join(args.working_dir, constants.NAME_IGNORED_FILE)
    )
    logging.info("Counted %s ignored files.", num_ignored_files)

    if args.dry_run:
        logging.info("Final validation checks omitted in dry-run.")
        return

    num_new_output_files = (
        utils.count_all_files(args.output_dir) - num_existing_output_files
    )
    logging.info("Counted new output files. %s", num_new_output_files)

    num_processed_files = (
        num_new_output_files + num_duplicated_files + num_ignored_files
    )

    if num_processed_files != num_input_files:
        msg = f"Only {num_processed_files} of {num_input_files} input files"
        raise RuntimeError(f"{msg} were processed.")

    logging.info("All files were processed successfully.")


##
# Setup:
##


def parse_args() -> argparse.Namespace:
    """Parse arguments from the command line.

    Returns:  argsparse.Namespace: Parsed command line arguments.
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
        action="store_true",
        help="Perform a dry run (don't copy any files)",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run in debug mode (verbose logging)",
    )

    return parser.parse_args()


def initialise(args: argparse.Namespace) -> None:
    """Set up working directories and logging.

    Args:
        args (argparse.Namespace): Runtime arguments.
    """

    print(">>> This is JISC Wrangler <<<")

    setup_directories(args)
    logutils.setup_logging(args, constants.NAME_LOGFILE)

    logging.info("Input directory: %s", args.input_dir)
    logging.info("Output directory: %s", args.output_dir)
    logging.info("Working directory: %s ", args.working_dir)


def setup_directories(args: argparse.Namespace) -> None:
    """Prepare working & output directories.

    Args:
        args (argparse.Namespace): Runtime arguments.

    Raises:
        ValueError: When input directory does not exist.
    """

    # Check the input directory path exists.
    if not os.path.exists(args.input_dir):
        raise ValueError("Please provide a valid input directory")

    # Prepare the output directory.
    if not os.path.exists(args.output_dir):
        Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    # Create a timestamped working subdirectory.
    working_subdir = (
        f'{constants.FILENAME_PREFIX}{datetime.now().strftime("%Y-%m-%d_%Hh-%Mm-%Ss")}'
    )
    working_dir = os.path.join(args.working_dir, working_subdir)
    if not os.path.exists(working_dir):
        Path(working_dir).mkdir(parents=True, exist_ok=True)
        # Set the working_dir argument to the timestamped subdirectory.
        args.working_dir = working_dir


if __name__ == "__main__":
    main()
