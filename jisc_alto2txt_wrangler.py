"""
JISC alto2txt Wrangler

A command line tool for replacing 4-character title codes with 7-digit
NLP codes in the metadata XML files generated by executing alto2txt on the
output produced by JISC Wrangler.

Only the XML content of the _metadata.xml files produced by alto2txt is
modified. Specifically, the value of the "id" attribute associated with the
"publication" element is changed from a 4-character title code to a 7-digit
NLP code.

File structure and names are unchanged (i.e. duplicated in the output), to
ensure that paths and files quoted to in the metadata XML remain valid.
"""
import os
from sys import exit
from pathlib import Path
from shutil import copy
import logging
import argparse
from datetime import datetime
import csv
import xml.etree.ElementTree as ET
from tqdm import tqdm  # type: ignore
from jisc_wrangler import __version__

# Constants
publication_element_name = 'publication'
publication_id_attribute_name = 'id'
issue_element_name = "issue"
date_element_name = 'date'

# Data.
title_code_lookup_file = "data/title_code_lookup.csv"
title_code_lookup_delimiter = '|'
title_index = 0
nlp_index = 1
start_day_index = 2
start_month_index = 3
start_year_index = 4
end_day_index = 5
end_month_index = 6
end_year_index = 7

# Filenames
name_logfile = 'jw_alto2txt.log'
metadata_xml_suffix = '_metadata.xml'
plaintext_extension = '.txt'


def main():

    try:
        # Prepare for execution.
        args = parse_args()
        initialise(args)

        # Process all of the files under the input directory.
        process_inputs(args)

        # Check that all of the input files were processed.
        validate(args)

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

    # Read the title code lookup file.
    lookup = read_title_code_lookup_file()

    # Get the input metadata file full paths.
    metadata_files = list_files(args.input_dir, metadata_xml_suffix)

    logging.info(f"Found {len(metadata_files)} metadata files.")

    # Print the number of files to be processed (and a progress bar).
    print(f"Processing {len(metadata_files)} metadata files")

    failure_count = 0
    for file in tqdm(metadata_files):

        logging.debug(f"Processing file {file}")

        # Read the metadata XML file.
        xml_tree = ET.parse(file)

        # Replace the 4 character title code with the 7 character NLP code
        # in the metadata XML.
        title_code, nlp = replace_publication_id(xml_tree, lookup)

        # If the publication code replacement failed, skip this file.
        if title_code is None:
            logging.warning(
                f"Skipping file {file} & associated plaintext file")
            continue

        # Construct the output file path.
        output_file = file.replace(args.input_dir, args.output_dir, 1)

        # Write the modified XML tree to the output file.
        if not args.dry_run:

            output_dir = os.path.dirname(output_file)
            if not os.path.isdir(output_dir):
                Path(output_dir).mkdir(parents=True, exist_ok=True)
                logging.info(f"Created subdirectory at {output_dir}")

            # xml_tree.write(output_file)
            try:
                with open(output_file, 'wb') as f:
                    xml_tree.write(f)
            except TypeError as e:
                failure_count += 1
                msg = f"TypeError thrown when writing XML ElementTree to {output_file}"
                logging.error(msg)
                os.remove(output_file)
                print(msg + ". File was removed. Continuing...")

        # Find the corresponding plaintext file.
        plaintext_path = Path(file.replace(
            metadata_xml_suffix, plaintext_extension))

        if not plaintext_path.is_file():
            msg = f"Failed to find plaintext file at: {plaintext_path}"
            raise RuntimeError(msg)

        # Construct the output plaintext file path.
        output_plaintext_file = str(plaintext_path).replace(
            args.input_dir, args.output_dir, 1)

        # Copy the plain text file to the output directory.
        if not args.dry_run:
            copy(str(plaintext_path), output_plaintext_file)

    if failure_count > 0:
        print(
            f"There were {failure_count} failures requiring manual intervention.")


def validate(args):

    # Compare the number of input & output metadata files.
    input_metadata_files = list_files(args.input_dir, metadata_xml_suffix)
    output_metadata_files = list_files(args.output_dir, metadata_xml_suffix)

    if len(input_metadata_files) != len(output_metadata_files):
        msg = f"unequal input & output metadata file counts."
        logging.warning(msg)
        print(f"WARNING: {msg}")

    # Compare the number of input & output plaintext files.
    input_plaintext_files = list_files(args.input_dir, plaintext_extension)
    output_plaintext_files = list_files(args.output_dir, plaintext_extension)

    if len(input_plaintext_files) != len(output_plaintext_files):
        msg = f"unequal input & output plaintext file counts."
        logging.warning(msg)
        print(f"WARNING: {msg}")

    logging.info(f"Processed {len(output_metadata_files)} metadata files.")
    logging.info(f"Processed {len(output_plaintext_files)} plaintext files.")


def replace_publication_id(xml_tree, lookup):
    """
    Replace a 4-character title code with a 7-digit NLP code in an XML tree.

    The XML tree structure is assumed to contain a "publication" element with
    "id" attribute, and sub-element "issue" which itself has a sub-element
    named "date".

    Args:
        xml_tree    (str): An XML ElementTree.
        lookup     (dict): A dictionary for NLP code lookups.

    Returns: the 7-digit NLP code.
    """

    pub_elem = xml_tree.find(publication_element_name)

    if pub_elem is None:
        logging.warning(f"Failed to find publication element in XML tree.")
        return None, None

    title_code = pub_elem.attrib[publication_id_attribute_name]
    if title_code is None:
        logging.warning(f"Failed to find title code attribute in XML tree.")
        return None, None

    date_str = pub_elem.find(issue_element_name +
                             "/" + date_element_name).text
    if date_str is None:
        logging.warning(f"Failed to find issue/date element in XML tree.")
        return None, None

    year, month, day = parse_publicaton_date(date_str)

    nlp = title_code_to_nlp(
        title_code, year, month, day, lookup)

    try:
        pub_elem.set(publication_id_attribute_name, nlp)
    except Exception as e:
        print(f"Failed to set publication element in XML tree.")
        print(f"ERROR: {str(e)}")
        return None, None

    return title_code, nlp


def parse_publicaton_date(date_str):
    """Parse a date string"""

    return tuple(date_str.split('-'))


def title_code_to_nlp(title_code, year, month, day, lookup):
    """
    Convert a 4-character title code to a 7-digit NLP code.

    Args:
        title_code  (str): A 4-character JISC title code.
        year        (str): A publication year in YYYY format.
        month       (str): A publication month in MM format.
        day         (str): A publication day in DD format.
        lookup     (dict): A dictionary for NLP code lookups.

    Returns: the 7-digit NLP code for the title (and date) as a string,
             or None if the NLP code is not available.
    """

    code_lookup = lookup[title_code]
    if not code_lookup:
        return None

    date = datetime.strptime(day + '-' + month + '-' + year, "%d-%m-%Y")
    for entry in code_lookup:
        date_range = entry[0]
        if date_in_range(date_range[0], date_range[1], date):
            return entry[1]

    return None


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


def read_title_code_lookup_file():
    """
    Read the csv daa file for title code lookups.

    Returns: a dictionary keyed by title code. Values are pairs in which the
             first element is a date range (i.e. a pair of datetime objects)
             and the second element is the corresponding NLP code.
    """

    # Read the title code lookup file.
    rows = []
    with open(title_code_lookup_file) as csvfile:
        csvreader = csv.reader(csvfile, delimiter=title_code_lookup_delimiter)
        for row in csvreader:
            rows.append(row)

    ret = dict()
    # Ignore the header row.
    for row in rows[1:]:
        start = parse_lookup_date(row, start=True)
        end = parse_lookup_date(row, start=False)
        # Pad the NLP code to 7 characters.
        nlp = row[nlp_index].strip().rjust(7, '0')
        title_code = row[title_index].strip()

        element = ((start, end), nlp)
        # If the title code is not already in the dictionary, add it.
        if title_code not in ret:
            ret[title_code] = list()
        ret[title_code].append(element)
    return(ret)


def parse_lookup_date(row, start):
    """Parse a date from a lookup table row.

    Args:
        row     : a row from the lookup table
        start   : a boolean flag

    Returns: a datetime object.
    """

    if start:
        day_index = start_day_index
        month_index = start_month_index
        year_index = start_year_index
    else:
        day_index = end_day_index
        month_index = end_month_index
        year_index = end_year_index

    # Pad the day to 2 characters.
    day = row[day_index].strip().rjust(2, '0')
    # Truncate the month to 3 characters
    month = row[month_index].strip()[0:3]
    year = row[year_index].strip()

    return datetime.strptime(day + '-' + month + '-' + year, "%d-%b-%Y")


def list_files(dir, suffix, sorted=False):
    """List all files under a given directory with a given suffix, recursively.

    Returns: a list of strings, optionally sorted.
    """

    ret = [str(f) for f in Path(dir).rglob(
        '*' + suffix) if os.path.isfile(f)]
    if sorted:
        ret.sort()
    return ret


##
# Setup:
##


def parse_args():
    """Parse arguments from the command line

    Returns: a Namespace object containing parsed command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Replace publication IDs in JISC alto2txt output"
    )

    parser.add_argument(
        "input_dir",
        help="Input directory containing JISC alto2txt output",
    )

    parser.add_argument(
        "output_dir",
        help="Output directory to which updated alto2txt output is written",
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

    print(">>> This is JISC alto2txt Wrangler <<<")

    setup_logging(args)
    setup_directories(args)

    logging.info(f"Input directory: {args.input_dir}")
    logging.info(f"Output directory: {args.output_dir}")


def setup_directories(args):
    """
    Prepare working & output directories.
    """

    # Check the input directory path exists.
    if not os.path.exists(args.input_dir):
        raise ValueError("Please provide a valid input directory.")

    # Prepare the output directory.
    if not os.path.exists(args.output_dir):
        Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    # Check the output directory is empty.
    if len([str(f) for f in Path(args.output_dir).rglob('*') if os.path.isfile(f)]) > 0:
        raise RuntimeError("Output directory must be initially empty.")


def setup_logging(args):
    """
    Prepare logging.
    """

    # Logging
    level = logging.INFO
    if (args.debug):
        level = logging.DEBUG
    log_full_path = os.path.join(os.getcwd(), name_logfile)
    logging.basicConfig(filename=log_full_path, filemode='w',
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        level=level)
    logging.info(
        f"This log file was generated by JISC alto2txt Wrangler v{__version__}")
    if args.dry_run:
        logging.info("Executing a DRY RUN. No files will be copied.")

    print(f"Logging to the current directory at:\n{log_full_path}")


if __name__ == "__main__":
    main()
