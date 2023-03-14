"""
JISC constants

Constants for JISC wrangler
"""

import os
from re import compile, IGNORECASE

# Regex patterns for INPUT DIRECTORIES:
# These should be mutually exclusive and exhaustive when used
# case-insenstively (grep -E -i). Parts in parentheses are the
# corresponding standardised output paths.
P_SERVICE = os.path.join(
    '([A-Z]{4}', '[0-9]{4}', '[0-9]{2}', '[0-9]{2})(', ')service', '')
P_MASTER = os.path.join(
    '([A-Z]{4}', '[0-9]{4}', '[0-9]{2}', '[0-9]{2})(', ')master', '')
P_SUBDAY = '_[S,V]'
P_SERVICE_SUBDAY = os.path.join('([A-Z]{4}', '[0-9]{4}', '[0-9]{2}',
                                '[0-9]{2})' + P_SUBDAY + '(', ')service', '')
P_MASTER_SUBDAY = os.path.join('([A-Z]{4}', '[0-9]{4}', '[0-9]{2}',
                               '[0-9]{2})' + P_SUBDAY + '(', ')master', '')
P_LSIDYV = os.path.join('lsidyv[a-z0-9]{4}[a-z0-9]?[a-z0-9]?', '[A-Z]{4}-')
P_LSIDYV_ANOMALY = os.path.join(
    'lsidyv[a-z0-9]{4}[a-z0-9]?[a-z0-9]?', '[A-Z]{5}-')
P_OSMAPS = os.path.join('OSMaps.*?(\\.shp|', 'metadata)\\.xml$')

service_pattern = compile(P_SERVICE, IGNORECASE)
service_subday_pattern = compile(P_SERVICE_SUBDAY, IGNORECASE)
master_pattern = compile(P_MASTER, IGNORECASE)
master_subday_pattern = compile(P_MASTER_SUBDAY, IGNORECASE)
lsidyv_pattern = compile(P_LSIDYV)
lsidyv_anomaly_pattern = compile(P_LSIDYV_ANOMALY)
os_maps_pattern = compile(P_OSMAPS)

# Do *not* include the anomalous pattern here.
dir_patterns = [
    service_pattern, service_subday_pattern, master_pattern,
    master_subday_pattern, lsidyv_pattern, os_maps_pattern
]

# Working filenames
filename_prefix = 'jw_'
name_logfile = 'jw.log'
name_logfile_alto2txt = 'jw_alto2txt.log'
name_unmatched_file = filename_prefix + 'unmatched.txt'
name_ignored_file = filename_prefix + 'ignored.txt'
name_duplicates_file = filename_prefix + 'duplicates.txt'
metadata_xml_suffix = '_metadata.xml'
plaintext_extension = '.txt'

# Constants
len_title_code = len('ABCD')
len_title_code_dir = len(os.path.join('ABCD', ''))
len_title_code_y_dir = len(os.path.join('ABCD', 'YYYY', ''))
len_title_code_ym_dir = len(os.path.join('ABCD', 'YYYY', 'MM', ''))
len_title_code_ymd_dir = len(os.path.join('ABCD', 'YYYY', 'MM', 'DD', ''))
len_subday_subscript = len('_X')
len_day = len('DD')
publication_element_name = 'publication'
publication_id_attribute_name = 'id'
issue_element_name = "issue"
date_element_name = 'date'
input_sub_path_element_name = './/input_sub_path'

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

# Suffix used to distinguish non-duplicates with conflicting filenames.
alt_filename_suffix = '_ALT'