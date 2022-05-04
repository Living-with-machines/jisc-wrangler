from datetime import datetime
import csv

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


def replace_publication_id(xml_tree, lookup):
    """
    Replace a 4-character title code with a 7-digit NLP code in an XML tree.

    The XML tree structure is assumed to contain a "publication" element with
    "id" attribute, and sub-element "issue" which itself has a sub-element
    named "date".

    Args:
        xml_tree    (str): An XML ElementTree.
        lookup     (dict): A dictionary for NLP code lookups.

    Returns: the modified XML ElementTree with replaced publication id
             attribute.
    """

    try:
        pub_elem = xml_tree.find(publication_element_name)
        title_code = pub_elem.attrib[publication_id_attribute_name]

        date_str = pub_elem.find(issue_element_name +
                                 "/" + date_element_name).text
        year, month, day = parse_publicaton_date(date_str)

        new_title_code = title_code_to_nlp(
            title_code, year, month, day, lookup)

        pub_elem.set(publication_id_attribute_name, new_title_code)

    except Exception as e:
        print(f"Failed to replace publication id.")
        print(f"ERROR: {str(e)}")
        exit()

    return xml_tree


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
