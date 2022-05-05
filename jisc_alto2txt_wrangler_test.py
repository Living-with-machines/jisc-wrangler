import xml.etree.ElementTree as ET
from jisc_alto2txt_wrangler import *
import pytest


@pytest.fixture
def xml_tree():

    xml_string = """<?xml version="1.0"?>
        <lwm>
            <process>
                <lwm_tool>
                <name>extract_text</name>
                <version>0.3.0</version>
                <source>https://github.com/alan-turing-institute/Living-with-Machines-code</source>
                </lwm_tool>
                <source_type>newspaper</source_type>
                <xml_flavour>bln</xml_flavour>
                <software>Apex CoVantage, LLC</software>
                <input_sub_path>RDNP/1850/05/05</input_sub_path>
                <input_filename>WO1_RDNP_1850_05_05-0001-001.xml</input_filename>
            </process>
            <publication id="RDNP">
                <title>Reynolds's Weekly News</title>
                <location>London</location>
                <issue id="1">
                    <date>1850-05-05</date>
                    <item id="0001-001">
                        <plain_text_file>WO1_RDNP_1850_05_05-0001-001.txt</plain_text_file>
                        <title>THE PROSPECTS OF THE DEMOCRATIC CAUSE.</title>
                        <word_count>3161</word_count>
                        <ocr_quality_summary>Good</ocr_quality_summary>
                    </item>
                </issue>
            </publication>
        </lwm>
        """

    return ET.fromstring(xml_string)


def test_replace_publication_id(xml_tree):

    # Initially the publication id is "RDNP"
    assert xml_tree.find(publication_element_name).attrib[
        publication_id_attribute_name] == "RDNP"

    lookup = read_title_code_lookup_file()
    result = replace_publication_id(xml_tree, lookup)

    # After replacement the publication id in the XML tree is "0000095"
    assert len(xml_tree.findall(publication_element_name)) == 1
    assert xml_tree.find(publication_element_name).attrib[
        publication_id_attribute_name] == "0000095"

    # The return value is the publication id:
    assert result == ("RDNP", "0000095")


def test_read_title_code_lookup_file():

    lookup = read_title_code_lookup_file()

    assert isinstance(lookup, dict)
    assert "ANJO" in lookup

    # Two lines in the lookup table for "ANJO"
    assert isinstance(lookup["ANJO"], list)
    assert len(lookup["ANJO"]) == 2

    # First line for "ANJO" is for 01/01/1800 to 23/08/1876 with NLP 31.
    assert isinstance(lookup["ANJO"][0], tuple)
    assert len(lookup["ANJO"][0]) == 2

    # This is the date range.
    assert isinstance(lookup["ANJO"][0][0], tuple)
    assert len(lookup["ANJO"][0][0]) == 2

    assert lookup["ANJO"][0][0][0] == datetime.strptime(
        "01-Jan-1800", "%d-%b-%Y")
    assert lookup["ANJO"][0][0][1] == datetime.strptime(
        "23-Aug-1876", "%d-%b-%Y")

    # This is the NLP code.
    assert isinstance(lookup["ANJO"][0][1], str)
    assert lookup["ANJO"][0][1] == "0000031"

    assert "SNSR" in lookup

    # One line in the lookup table for "SNSR"
    assert isinstance(lookup["SNSR"], list)
    assert len(lookup["SNSR"]) == 1

    # Single line for "SNSR" is for 19/01/1840 to 12/07/1840 with NLP 97.
    assert isinstance(lookup["SNSR"][0], tuple)
    assert len(lookup["SNSR"][0]) == 2

    # This is the date range.
    assert isinstance(lookup["SNSR"][0][0], tuple)
    assert len(lookup["SNSR"][0][0]) == 2

    assert lookup["SNSR"][0][0][0] == datetime.strptime(
        "19-Jan-1840", "%d-%b-%Y")
    assert lookup["SNSR"][0][0][1] == datetime.strptime(
        "12-Jul-1840", "%d-%b-%Y")

    # This is the NLP code.
    assert isinstance(lookup["SNSR"][0][1], str)
    assert lookup["SNSR"][0][1] == "0000097"


def test_title_code_to_nlp():

    lookup = read_title_code_lookup_file()

    title_code = "ANJO"
    year = "1876"
    month = "08"
    day = "22"
    expected = "0000031"

    assert title_code_to_nlp(title_code, year, month, day, lookup) == expected

    title_code = "ANJO"
    year = "1876"
    month = "08"
    day = "24"
    expected = None

    assert title_code_to_nlp(title_code, year, month, day, lookup) == expected

    title_code = "ANJO"
    year = "1876"
    month = "08"
    day = "30"
    expected = "0000032"

    assert title_code_to_nlp(title_code, year, month, day, lookup) == expected

    title_code = "ANJO"
    year = "1900"
    month = "12"
    day = "31"
    expected = "0000032"

    assert title_code_to_nlp(title_code, year, month, day, lookup) == expected

    title_code = "ANJO"
    year = "1901"
    month = "01"
    day = "01"
    expected = None

    assert title_code_to_nlp(title_code, year, month, day, lookup) == expected

    title_code = "COGE"
    year = "1803"
    month = "07"
    day = "01"
    expected = None

    assert title_code_to_nlp(title_code, year, month, day, lookup) == expected

    title_code = "COGE"
    year = "1803"
    month = "07"
    day = "02"
    expected = "0000179"

    assert title_code_to_nlp(title_code, year, month, day, lookup) == expected

    title_code = "COGE"
    year = "1810"
    month = "07"
    day = "02"
    expected = None

    assert title_code_to_nlp(title_code, year, month, day, lookup) == expected

    title_code = "COGE"
    year = "1811"
    month = "03"
    day = "16"
    expected = "0000177"

    assert title_code_to_nlp(title_code, year, month, day, lookup) == expected

    title_code = "COGE"
    year = "1835"
    month = "08"
    day = "29"
    expected = "0000177"

    assert title_code_to_nlp(title_code, year, month, day, lookup) == expected

    title_code = "COGE"
    year = "1835"
    month = "09"
    day = "29"
    expected = "0000178"

    assert title_code_to_nlp(title_code, year, month, day, lookup) == expected

    title_code = "COGE"
    year = "1888"
    month = "08"
    day = "29"
    expected = "0000180"

    assert title_code_to_nlp(title_code, year, month, day, lookup) == expected

    title_code = "IPJO"
    year = "1800"
    month = "12"
    day = "27"
    expected = "0000071"

    assert title_code_to_nlp(title_code, year, month, day, lookup) == expected

    title_code = "IPJL"
    year = "1800"
    month = "12"
    day = "27"
    expected = "0000071"

    assert title_code_to_nlp(title_code, year, month, day, lookup) == expected

    title_code = "LAGE"
    year = "1892"
    month = "12"
    day = "31"
    expected = "0000488"

    assert title_code_to_nlp(title_code, year, month, day, lookup) == expected

    title_code = "LAGER"
    year = "1892"
    month = "12"
    day = "31"
    expected = "0000488"

    assert title_code_to_nlp(title_code, year, month, day, lookup) == expected
