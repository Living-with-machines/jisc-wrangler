"""
JISC constants

Constants for JISC wrangler
"""

import os
import re

# Regex patterns for INPUT DIRECTORIES:
# These should be mutually exclusive and exhaustive when used
# case-insenstively (grep -E -i). Parts in parentheses are the
# corresponding standardised output paths.
P_SERVICE = os.path.join(
    "([A-Z]{4}", "[0-9]{4}", "[0-9]{2}", "[0-9]{2})(", ")service", ""
)
P_MASTER = os.path.join(
    "([A-Z]{4}", "[0-9]{4}", "[0-9]{2}", "[0-9]{2})(", ")master", ""
)
P_SUBDAY = "_[S,V]"
P_SERVICE_SUBDAY = os.path.join(
    "([A-Z]{4}", "[0-9]{4}", "[0-9]{2}", "[0-9]{2})" + P_SUBDAY + "(", ")service", ""
)
P_MASTER_SUBDAY = os.path.join(
    "([A-Z]{4}", "[0-9]{4}", "[0-9]{2}", "[0-9]{2})" + P_SUBDAY + "(", ")master", ""
)
P_LSIDYV = os.path.join("lsidyv[a-z0-9]{4}[a-z0-9]?[a-z0-9]?", "[A-Z]{4}-")
P_LSIDYV_ANOMALY = os.path.join("lsidyv[a-z0-9]{4}[a-z0-9]?[a-z0-9]?", "[A-Z]{5}-")
P_OSMAPS = os.path.join("OSMaps.*?(\\.shp|", "metadata)\\.xml$")

SERVICE_PATTERN = re.compile(P_SERVICE, re.IGNORECASE)
SERVICE_SUBDAY_PATTERN = re.compile(P_SERVICE_SUBDAY, re.IGNORECASE)
MASTER_PATTERN = re.compile(P_MASTER, re.IGNORECASE)
MASTER_SUBDAY_PATTERN = re.compile(P_MASTER_SUBDAY, re.IGNORECASE)
LSIDYV_PATTERN = re.compile(P_LSIDYV)
LISIDYV_ANOMALY_PATTERN = re.compile(P_LSIDYV_ANOMALY)
OS_MAPS_PATTERN = re.compile(P_OSMAPS)

# Do *not* include the anomalous pattern here.
DIR_PATTERNS = [
    SERVICE_PATTERN,
    SERVICE_SUBDAY_PATTERN,
    MASTER_PATTERN,
    MASTER_SUBDAY_PATTERN,
    LSIDYV_PATTERN,
    OS_MAPS_PATTERN,
]

# Regex patterns for the STANDARDISED OUTPUT DIRECTORIES:
# Note matches only end of line $.
P_STANDARD_SUBDIR = os.path.join("[A-Z]{4}", "[0-9]{4}", "[0-9]{2}", "[0-9]{2}$")
STANDARD_SUBDIR_PATTERN = re.compile(P_STANDARD_SUBDIR)

# Working filenames
FILENAME_PREFIX = "jw_"
NAME_LOGFILE = "jw.log"
NAME_LOGFILE_ALTO2TXT = "jw_alto2txt.log"
NAME_UNMATCHED_FILE = FILENAME_PREFIX + "unmatched.txt"
NAME_IGNORED_FILE = FILENAME_PREFIX + "ignored.txt"
NAME_DUPLICATES_FILE = FILENAME_PREFIX + "duplicates.txt"
METADATA_XML_SUFFIX = "_metadata.xml"
PLAINTEXT_EXTENSION = ".txt"

# Constants
LEN_TITLE_CODE = len("ABCD")
LEN_TITLE_CODE_DIR = len(os.path.join("ABCD", ""))
LEN_TITLE_CODE_Y_DIR = len(os.path.join("ABCD", "YYYY", ""))
LEN_TITLE_CODE_YM_DIR = len(os.path.join("ABCD", "YYYY", "MM", ""))
LEN_TITLE_CODE_YMD_DIR = len(os.path.join("ABCD", "YYYY", "MM", "DD", ""))
LEN_SUBDAY_SUBSCRIPT = len("_X")
LEN_DAY = len("DD")
PUPBLICATION_ELEMENT_NAME = "publication"
PUBLICATION_ID_ATTRIBUTE_NAME = "id"
ISSUE_ELEMENT_NAME = "issue"
DATE_ELEMENT_NAME = "date"
INPUT_SUB_PATH_ELEMENT_NAME = ".//input_sub_path"

# Data.
TITLE_CODE_LOOKUP_FILE = "data/title_code_lookup.csv"
TITLE_CODE_LOOKUP_DELIMITER = "|"
TITLE_INDEX = 0
NLP_INDEX = 1
START_DAY_INDEX = 2
START_MONTH_INDEX = 3
START_YEAR_INDEX = 4
END_DAY_INDEX = 5
END_MONTH_INDEX = 6
END_YEAR_INDEX = 7

# Suffix used to distinguish non-duplicates with conflicting filenames.
ALT_FILENAME_SUFFIX = "_ALT"
