from cmath import exp
from jisc_wrangler import *
from pytest import raises
from unittest.mock import create_autospec

paths = ['/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/11/07/service/WO1_BDPO_1894_11_07-0008-054.xml',
         '/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/11/07/service/WO1_BDPO_1894_11_07-0008-055.xml',
         '/data/JISC/JISC1_VOL1_C0/009/Data/Job-2001/Batch_0162/2001-0162/WO1/RDNP/1862/01/05/service/WO1_RDNP_1862_01_05-0001-001.xml',
         '/data/JISC/JISC1_VOL1_C0/009/Data/Job-2001/Batch_0162/2001-0162/WO1/RDNP/1862/01/05/service/WO1_RDNP_1862_01_05-0001-002.xml',
         '/data/JISC/JISC1/JISC2_VOL1_C0/097/2001-0346/WO1/LEMR/1873/01/04_S/service/WO1_LEMR_1873_01_04_S-0001.xml',
         '/data/JISC/JISC2/lsidyv10001b/MOPT-1861-12-05.xml',
         '/data/JISC/JISC2/lsidyvfd9b/IMTS-1877-10-13_mets.xml']
stubs = ['/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO',
         '/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO',
         '/data/JISC/JISC1_VOL1_C0/009/Data/Job-2001/Batch_0162/2001-0162/WO1/RDNP',
         '/data/JISC/JISC1_VOL1_C0/009/Data/Job-2001/Batch_0162/2001-0162/WO1/RDNP',
         '/data/JISC/JISC1/JISC2_VOL1_C0/097/2001-0346/WO1/LEMR',
         '/data/JISC/JISC2/lsidyv10001b/MOPT-',
         '/data/JISC/JISC2/lsidyvfd9b/IMTS-']


def test_list_all_files(fs):

    # Use pyfakefs to fake the filesystem.
    dir = '/home/'

    assert list_all_files(dir) == []

    fs.create_dir('/home/output/')
    fs.create_dir('/home/output/ABCD/')
    assert list_all_files(dir) == []

    fs.create_file('/home/output/ABCD/abc.xml')
    assert os.path.isfile('/home/output/ABCD/abc.xml')
    assert list_all_files(dir) == ['/home/output/ABCD/abc.xml']

    fs.create_file('/home/xyz.txt')
    assert set(list_all_files(dir)) == set(
        ['/home/output/ABCD/abc.xml', '/home/xyz.txt'])


def test_list_all_subdirs(fs):

    # Use pyfakefs to fake the filesystem
    dir = '/home/'

    assert list_all_subdirs(dir) == []

    fs.create_dir('/home/output/')
    fs.create_dir('/home/output/ABCD/')
    assert set(list_all_subdirs(dir)) == set(
        ['/home/output/', '/home/output/ABCD/'])

    fs.create_file('/home/output/ABCD/abc.xml')
    assert os.path.isfile('/home/output/ABCD/abc.xml')
    assert set(list_all_subdirs(dir)) == set(
        ['/home/output/', '/home/output/ABCD/'])

    fs.create_dir('/home/XYZ/')
    assert set(list_all_subdirs(dir)) == set(
        ['/home/output/', '/home/output/ABCD/', '/home/XYZ/'])


def test_extract_pattern_stubs():

    # The first five paths match the P_SERVICE pattern.
    actual = extract_pattern_stubs(service_pattern, paths)
    assert actual == stubs[:4]

    # The fifth path matches the P_SERVICE_SUBDAY pattern.
    actual = extract_pattern_stubs(service_subday_pattern, paths)
    assert actual == stubs[4:5]

    # The sixth & seventh paths match the P_LSIDYV pattern.
    actual = extract_pattern_stubs(lsidyv_pattern, paths)
    assert actual == stubs[5:7]

    # None of the paths matches the P_MASTER pattern.
    actual = extract_pattern_stubs(master_pattern, paths)
    assert actual == []


def test_count_matches_in_list():

    l = paths.copy()

    # This prefix is common to all of the paths.
    p = '/data/JISC/JISC1'
    assert count_matches_in_list(p, l) == 5

    # This prefix is common to the first four paths.
    p = '/data/JISC/JISC1_VOL'
    assert count_matches_in_list(p, l) == 4

    # The stubs[0] matches the beginning of both the paths.
    p = stubs[0]
    assert count_matches_in_list(p, l) == 2

    p = '/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/11/07/service/'
    assert count_matches_in_list(p, l) == 2

    p = '/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/11/07/service/WO1_BDPO_1894_11_07-0008-054'
    assert count_matches_in_list(p, l) == 1

    # Matches are found only up to the first non-match in the list.
    p = '/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/11/07/service/WO1_BDPO_1894_11_07-0008-055'
    assert count_matches_in_list(p, l) == 0

    p = 'data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/11/07/service/'
    # Note the missing '/' at the beginning of p.
    assert count_matches_in_list(p, l) == 0

    p = stubs[0]
    # Insert a non-matching string at index 1 (2nd position).
    l.insert(1, 'XXX')
    # Matches are found only up to the first non-match in the list.
    assert count_matches_in_list(p, l) == 1

    l = []
    p = '/data/JISC/JISC1_VOL'
    assert count_matches_in_list(p, l) == 0


def test_target_output_subdir():

    # TODO: test with each type of path (i.e. matching each directory pattern)
    output_dir = '/home/output/'

    #
    # Test with a full path matching the P_SERVICE pattern.
    #
    full_path = '/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/11/07/service/WO1_BDPO_1894_11_07-0008-054.xml'

    # If the suffix length is that of the title code subdirectory, then the output
    # target subdirectory is the output directory plus the title code directory.
    len_subdir = len('ABCD/')
    actual = target_output_subdir(full_path, len_subdir, output_dir)
    expected = output_dir + 'BDPO/'
    assert actual == expected

    # If the suffix length is that of the title code & year subdirectories, then
    # the output target subdirectory is the output directory plus the title code
    # and year directories.
    len_subdir = len('ABCD/1999/')
    actual = target_output_subdir(full_path, len_subdir, output_dir)
    expected = output_dir
    assert actual == output_dir + 'BDPO/' + '1894/'

    len_subdir = len('ABCD/1999/00/')
    actual = target_output_subdir(full_path, len_subdir, output_dir)
    expected = output_dir
    assert actual == output_dir + 'BDPO/' + '1894/' + '11/'

    len_subdir = len('ABCD/1999/00/00/')
    actual = target_output_subdir(full_path, len_subdir, output_dir)
    expected = output_dir
    assert actual == output_dir + 'BDPO/' + '1894/' + '11/' + '07/'

    #
    # Test with a full path matching the P_SERVICE_SUBDAY pattern.
    #
    full_path = '/data/JISC/JISC1/JISC2_VOL1_C0/097/2001-0346/WO1/LEMR/1873/01/04_S/service/WO1_LEMR_1873_01_04_S-0001.xml'

    # If the suffix length is that of the title code subdirectory, then the output
    # target subdirectory is the output directory plus the title code directory.
    len_subdir = len('ABCD/')
    actual = target_output_subdir(full_path, len_subdir, output_dir)
    expected = output_dir + 'LEMR/'
    assert actual == expected

    # If the suffix length is that of the title code & year subdirectories, then
    # the output target subdirectory is the output directory plus the title code
    # and year directories.
    len_subdir = len('ABCD/1999/')
    actual = target_output_subdir(full_path, len_subdir, output_dir)
    expected = output_dir
    assert actual == output_dir + 'LEMR/' + '1873/'

    len_subdir = len('ABCD/1999/00/')
    actual = target_output_subdir(full_path, len_subdir, output_dir)
    expected = output_dir
    assert actual == output_dir + 'LEMR/' + '1873/' + '01/'

    len_subdir = len('ABCD/1999/00/00/')
    actual = target_output_subdir(full_path, len_subdir, output_dir)
    expected = output_dir
    assert actual == output_dir + 'LEMR/' + '1873/' + '01/' + '04/'

    #
    # Test with a full path matching the P_LSIDYV pattern.
    #
    full_path = '/data/JISC/JISC2/lsidyv100b3f/MOPT-1863-02-16.xml'

    len_subdir = len('ABCD/1999/00/00/')
    actual = target_output_subdir(full_path, len_subdir, output_dir)
    expected = output_dir
    assert actual == output_dir + 'MOPT/' + '1863/' + '02/' + '16/'


def test_standardised_output_subdir():

    # Test with a full path matching the P_SERVICE pattern.
    full_path = '/data/JISC/JISC1_VOL1_C0/009/Data/Job-2001/Batch_0162/2001-0162/WO1/RDNP/1862/01/05/service/WO1_RDNP_1862_01_05-0001-001.xml'
    assert service_pattern.search(full_path)

    actual = standardised_output_subdir(full_path)
    expected = 'RDNP/1862/01/05/'
    assert actual == expected

    # Test with a full path matching the P_SERVICE_SUBDAY pattern.
    full_path = '/data/JISC/JISC1_VOL1_C0/009/Data/Job-2001/Batch_0162/2001-0162/WO1/RDNP/1862/01/05_S/service/WO1_RDNP_1862_01_05-0001-001.xml'
    assert service_subday_pattern.search(full_path)

    actual = standardised_output_subdir(full_path)
    expected = 'RDNP/1862/01/05/'
    assert actual == expected

    # Test with a full path matching the P_MASTER pattern.
    full_path = '/data/JISC/JISC1_VOL1_C0/009/Data/Job-2001/Batch_0162/2001-0162/WO1/RDNP/1862/01/05/master/WO1_RDNP_1862_01_05-0001-001.xml'
    assert master_pattern.search(full_path)

    actual = standardised_output_subdir(full_path)
    expected = 'RDNP/1862/01/05/'
    assert actual == expected

    # Test with a full path matching the P_MASTER_SUBDAY pattern.
    full_path = '/data/JISC/JISC1_VOL1_C0/009/Data/Job-2001/Batch_0162/2001-0162/WO1/RDNP/1862/01/05_V/master/WO1_RDNP_1862_01_05-0001-001.xml'
    assert master_subday_pattern.search(full_path)

    actual = standardised_output_subdir(full_path)
    expected = 'RDNP/1862/01/05/'
    assert actual == expected

    # Test with a full path matching the P_LSIDYV pattern.
    full_path = '/data/JISC/JISC2/lsidyv100b3f/MOPT-1863-02-16.xml'
    assert lsidyv_pattern.search(full_path)

    actual = standardised_output_subdir(full_path)
    expected = 'MOPT/1863/02/16/'
    assert actual == expected

    # Test with a full path matching the P_LSIDYV pattern with _mets subscript.
    full_path = '/data/JISC/JISC2/lsidyvfd9b/IMTS-1877-10-13_mets.xml'
    assert lsidyv_pattern.search(full_path)

    actual = standardised_output_subdir(full_path)
    expected = 'IMTS/1877/10/13/'
    assert actual == expected


def test_determine_from_to(fs):

    # Use pyfakefs to fake the filesystem
    output_dir = '/home/output/'
    fs.create_dir('/home/output/')

    #
    # Test with a full path matching the P_SERVICE pattern.
    #
    full_path = '/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/11/07/service/WO1_BDPO_1894_11_07-0008-054.xml'
    stub = '/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO'

    # If the title directory is missing, we can copy the entire title.
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = '/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/'
    expected_to = '/home/output/BDPO/'
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    # If the matching title directory is missing, we can copy the entire title.
    fs.create_dir('/home/output/ABCD/')
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = '/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/'
    expected_to = '/home/output/BDPO/'
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    # If the year directory is missing, we can handle the entire year.
    fs.create_dir('/home/output/BDPO/')
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = '/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/'
    expected_to = '/home/output/BDPO/1894/'
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    # If the matching year directory is missing, we can handle the entire year.
    fs.create_dir('/home/output/BDPO/1999/')
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = '/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/'
    expected_to = '/home/output/BDPO/1894/'
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    # If the month directory is missing, we can handle the entire month.
    fs.create_dir('/home/output/BDPO/1894/')
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = '/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/11/'
    expected_to = '/home/output/BDPO/1894/11/'
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    # If the matching month directory is missing, we can handle the entire month.
    fs.create_dir('/home/output/BDPO/1894/12/')
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = '/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/11/'
    expected_to = '/home/output/BDPO/1894/11/'
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    # If the day directory is missing, we can handle the entire day.
    fs.create_dir('/home/output/BDPO/1894/11/')
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = '/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/11/07/'
    expected_to = '/home/output/BDPO/1894/11/07/'
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    # If the matching day directory is missing, we can handle the entire day.
    fs.create_dir('/home/output/BDPO/1894/11/08')
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = '/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/11/07/'
    expected_to = '/home/output/BDPO/1894/11/07/'
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    # If the matching day directory exists, but not a matching file, we can handle the file.
    fs.create_dir('/home/output/BDPO/1894/11/07/')
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = paths[0]
    expected_to = '/home/output/BDPO/1894/11/07/'
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    # If a matching file exists, we can't handle anything.
    fs.create_file(
        '/home/output/BDPO/1894/11/07/WO1_BDPO_1894_11_07-0008-054.xml')
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = None
    expected_to = '/home/output/BDPO/1894/11/07/WO1_BDPO_1894_11_07-0008-054.xml'
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    #
    # Test with a full path matching the P_SERVICE_SUBDAY pattern.
    #
    full_path = '/data/JISC/JISC1/JISC2_VOL1_C0/097/2001-0346/WO1/LEMR/1873/01/04_S/service/WO1_LEMR_1873_01_04_S-0001.xml'
    stub = '/data/JISC/JISC1/JISC2_VOL1_C0/097/2001-0346/WO1/LEMR'

    # If the title directory is missing, we can copy the entire title.
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = os.path.join(stubs[4], '')
    expected_to = '/home/output/LEMR/'
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    # If the matching month directory is missing, we can handle the entire month.
    fs.create_dir('/home/output/LEMR/1873/02/')
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = '/data/JISC/JISC1/JISC2_VOL1_C0/097/2001-0346/WO1/LEMR/1873/01/'
    expected_to = '/home/output/LEMR/1873/01/'
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    # If the matching day directory is missing, we can handle the entire day.
    # Note that in this case the 'copy from' directory includes the subday subscript.
    fs.create_dir('/home/output/LEMR/1873/01/03/')
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = '/data/JISC/JISC1/JISC2_VOL1_C0/097/2001-0346/WO1/LEMR/1873/01/04_S/'
    expected_to = '/home/output/LEMR/1873/01/04/'
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    # If the matching day directory exists, but not a matching file, we can handle the file.
    fs.create_dir('/home/output/LEMR/1873/01/04/')
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = full_path
    expected_to = '/home/output/LEMR/1873/01/04/'
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    # If a matching file exists, we can't handle anything.
    fs.create_file(
        '/home/output/LEMR/1873/01/04/WO1_LEMR_1873_01_04_S-0001.xml')
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = None
    expected_to = '/home/output/LEMR/1873/01/04/WO1_LEMR_1873_01_04_S-0001.xml'
    assert actual[0] == expected_from
    assert actual[1] == expected_to


def test_alt_output_file():

    file_path = "/jisc1and2full/clean/ANJO/1891/01/07/WO1_ANJO_1891_01_07-0001-001.xml"
    expected = "/jisc1and2full/clean/ANJO/1891/01/07/WO1_ANJO_1891_01_07-0001-001" + \
        alt_filename_suffix + ".xml"
    actual = alt_output_file(file_path)

    assert actual == expected


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


def test_fix_title_code_anomaly():

    working_dir = '/home/working_dir/'
    path = '/data/JISC/JISC2/lsidyv785a3/LAGER-1892-12-31_mets.xml'
    expected = working_dir + 'lsidyv785a3/LAGE-1892-12-31_mets.xml'

    actual = fix_title_code_anomaly(path, working_dir)

    assert actual == expected

    # The path variable has not changed.
    assert path == '/data/JISC/JISC2/lsidyv785a3/LAGER-1892-12-31_mets.xml'

    non_anomalous_path = '/data/JISC/JISC2/lsidyv10001b/MOPT-1861-12-05.xml'
    with raises(ValueError):
        fix_title_code_anomaly(non_anomalous_path, working_dir)


def test_fix_anomalous_title_codes(fs):

    # Use pyfakefs to fake the filesystem
    working_dir = '/home/working_dir/'
    fs.create_dir(working_dir)

    # Add an anomalous path to the list.
    paths_plus_one = paths.copy()
    anomalous_path = '/data/JISC/JISC2/lsidyv785a3/LAGER-1892-12-31_mets.xml'
    paths_plus_one.append(anomalous_path)
    expected = working_dir + 'lsidyv785a3/LAGE-1892-12-31_mets.xml'

    # Use pyfakefs to fake the filesystem
    for path in paths_plus_one:
        fs.create_file(path)

    fix_anomalous_title_codes(paths_plus_one, working_dir)

    # All except the last (anomalous) one are unchanged.
    assert paths_plus_one[:-1] == paths
    assert paths_plus_one[-1] == expected

    # Check that the anomalous file has been copied and renamed.
    files_in_input_dir = list_all_files('/data/')

    assert len(files_in_input_dir) == len(paths_plus_one)
    assert files_in_input_dir[:-1] == paths_plus_one[:-1]

    # The original anomalous file remains.
    assert files_in_input_dir[-1] == anomalous_path

    files_in_working_dir = list_all_files(working_dir)

    # The title code in the file copied to the working directory has been fixed.
    assert len(files_in_working_dir) == 1
    assert files_in_working_dir[0] == expected
