from cmath import exp
from unittest.mock import create_autospec

from pytest import raises

from jisc_wrangler import constants, utils
from jisc_wrangler.jisc_plain_wrangler import *

from .test_constants import *


def test_extract_pattern_stubs():
    # The first five paths match the P_SERVICE pattern.
    actual = extract_pattern_stubs(constants.SERVICE_PATTERN, paths)
    assert actual == stubs[:4]

    # The fifth path matches the P_SERVICE_SUBDAY pattern.
    actual = extract_pattern_stubs(constants.SERVICE_SUBDAY_PATTERN, paths)
    assert actual == stubs[4:5]

    # The sixth & seventh paths match the P_LSIDYV pattern.
    actual = extract_pattern_stubs(constants.LSIDYV_PATTERN, paths)
    assert actual == stubs[5:7]

    # None of the paths matches the P_MASTER pattern.
    actual = extract_pattern_stubs(constants.MASTER_PATTERN, paths)
    assert actual == []


def test_target_output_subdir():
    # TODO: test with each type of path (i.e. matching each directory pattern)
    output_dir = "/home/output/"

    #
    # Test with a full path matching the P_SERVICE pattern.
    #
    full_path = "/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/11/07/service/WO1_BDPO_1894_11_07-0008-054.xml"

    # If the suffix length is that of the title code subdirectory, then the output
    # target subdirectory is the output directory plus the title code directory.
    len_subdir = len("ABCD/")
    actual = target_output_subdir(full_path, len_subdir, output_dir)
    expected = output_dir + "BDPO/"
    assert actual == expected

    # If the suffix length is that of the title code & year subdirectories, then
    # the output target subdirectory is the output directory plus the title code
    # and year directories.
    len_subdir = len("ABCD/1999/")
    actual = target_output_subdir(full_path, len_subdir, output_dir)
    expected = output_dir
    assert actual == output_dir + "BDPO/" + "1894/"

    len_subdir = len("ABCD/1999/00/")
    actual = target_output_subdir(full_path, len_subdir, output_dir)
    expected = output_dir
    assert actual == output_dir + "BDPO/" + "1894/" + "11/"

    len_subdir = len("ABCD/1999/00/00/")
    actual = target_output_subdir(full_path, len_subdir, output_dir)
    expected = output_dir
    assert actual == output_dir + "BDPO/" + "1894/" + "11/" + "07/"

    #
    # Test with a full path matching the P_SERVICE_SUBDAY pattern.
    #
    full_path = "/data/JISC/JISC1/JISC2_VOL1_C0/097/2001-0346/WO1/LEMR/1873/01/04_S/service/WO1_LEMR_1873_01_04_S-0001.xml"

    # If the suffix length is that of the title code subdirectory, then the output
    # target subdirectory is the output directory plus the title code directory.
    len_subdir = len("ABCD/")
    actual = target_output_subdir(full_path, len_subdir, output_dir)
    expected = output_dir + "LEMR/"
    assert actual == expected

    # If the suffix length is that of the title code & year subdirectories, then
    # the output target subdirectory is the output directory plus the title code
    # and year directories.
    len_subdir = len("ABCD/1999/")
    actual = target_output_subdir(full_path, len_subdir, output_dir)
    expected = output_dir
    assert actual == output_dir + "LEMR/" + "1873/"

    len_subdir = len("ABCD/1999/00/")
    actual = target_output_subdir(full_path, len_subdir, output_dir)
    expected = output_dir
    assert actual == output_dir + "LEMR/" + "1873/" + "01/"

    len_subdir = len("ABCD/1999/00/00/")
    actual = target_output_subdir(full_path, len_subdir, output_dir)
    expected = output_dir
    assert actual == output_dir + "LEMR/" + "1873/" + "01/" + "04/"

    #
    # Test with a full path matching the P_LSIDYV pattern.
    #
    full_path = "/data/JISC/JISC2/lsidyv100b3f/MOPT-1863-02-16.xml"

    len_subdir = len("ABCD/1999/00/00/")
    actual = target_output_subdir(full_path, len_subdir, output_dir)
    expected = output_dir
    assert actual == output_dir + "MOPT/" + "1863/" + "02/" + "16/"


def test_standardised_output_subdir():
    # Test with a full path matching the P_SERVICE pattern.
    full_path = "/data/JISC/JISC1_VOL1_C0/009/Data/Job-2001/Batch_0162/2001-0162/WO1/RDNP/1862/01/05/service/WO1_RDNP_1862_01_05-0001-001.xml"
    assert constants.SERVICE_PATTERN.search(full_path)

    actual = standardised_output_subdir(full_path)
    expected = "RDNP/1862/01/05/"
    assert actual == expected

    # Test with a full path matching the P_SERVICE_SUBDAY pattern.
    full_path = "/data/JISC/JISC1_VOL1_C0/009/Data/Job-2001/Batch_0162/2001-0162/WO1/RDNP/1862/01/05_S/service/WO1_RDNP_1862_01_05-0001-001.xml"
    assert constants.SERVICE_SUBDAY_PATTERN.search(full_path)

    actual = standardised_output_subdir(full_path)
    expected = "RDNP/1862/01/05/"
    assert actual == expected

    # Test with a full path matching the P_MASTER pattern.
    full_path = "/data/JISC/JISC1_VOL1_C0/009/Data/Job-2001/Batch_0162/2001-0162/WO1/RDNP/1862/01/05/master/WO1_RDNP_1862_01_05-0001-001.xml"
    assert constants.MASTER_PATTERN.search(full_path)

    actual = standardised_output_subdir(full_path)
    expected = "RDNP/1862/01/05/"
    assert actual == expected

    # Test with a full path matching the P_MASTER_SUBDAY pattern.
    full_path = "/data/JISC/JISC1_VOL1_C0/009/Data/Job-2001/Batch_0162/2001-0162/WO1/RDNP/1862/01/05_V/master/WO1_RDNP_1862_01_05-0001-001.xml"
    assert constants.MASTER_SUBDAY_PATTERN.search(full_path)

    actual = standardised_output_subdir(full_path)
    expected = "RDNP/1862/01/05/"
    assert actual == expected

    # Test with a full path matching the P_LSIDYV pattern.
    full_path = "/data/JISC/JISC2/lsidyv100b3f/MOPT-1863-02-16.xml"
    assert constants.LSIDYV_PATTERN.search(full_path)

    actual = standardised_output_subdir(full_path)
    expected = "MOPT/1863/02/16/"
    assert actual == expected

    # Test with a full path matching the P_LSIDYV pattern with _mets subscript.
    full_path = "/data/JISC/JISC2/lsidyvfd9b/IMTS-1877-10-13_mets.xml"
    assert constants.LSIDYV_PATTERN.search(full_path)

    actual = standardised_output_subdir(full_path)
    expected = "IMTS/1877/10/13/"
    assert actual == expected


def test_determine_from_to(fs):
    # Use pyfakefs to fake the filesystem
    output_dir = "/home/output/"
    fs.create_dir("/home/output/")

    # Test with a full path matching the P_SERVICE pattern.
    full_path = "/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/11/07/service/WO1_BDPO_1894_11_07-0008-054.xml"
    stub = "/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO"

    # If the title directory is missing, we can copy the entire title.
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = "/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/"
    expected_to = "/home/output/BDPO/"
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    # If the matching title directory is missing, we can copy the entire title.
    fs.create_dir("/home/output/ABCD/")
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = "/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/"
    expected_to = "/home/output/BDPO/"
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    # If the year directory is missing, we can handle the entire year.
    fs.create_dir("/home/output/BDPO/")
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = "/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/"
    expected_to = "/home/output/BDPO/1894/"
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    # If the matching year directory is missing, we can handle the entire year.
    fs.create_dir("/home/output/BDPO/1999/")
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = "/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/"
    expected_to = "/home/output/BDPO/1894/"
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    # If the month directory is missing, we can handle the entire month.
    fs.create_dir("/home/output/BDPO/1894/")
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = "/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/11/"
    expected_to = "/home/output/BDPO/1894/11/"
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    # If the matching month directory is missing, we can handle the entire month.
    fs.create_dir("/home/output/BDPO/1894/12/")
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = "/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/11/"
    expected_to = "/home/output/BDPO/1894/11/"
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    # If the day directory is missing, we can handle the entire day.
    fs.create_dir("/home/output/BDPO/1894/11/")
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = "/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/11/07/"
    expected_to = "/home/output/BDPO/1894/11/07/"
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    # If the matching day directory is missing, we can handle the entire day.
    fs.create_dir("/home/output/BDPO/1894/11/08")
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = "/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/11/07/"
    expected_to = "/home/output/BDPO/1894/11/07/"
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    # If the matching day directory exists, but not a matching file, we can handle the file.
    fs.create_dir("/home/output/BDPO/1894/11/07/")
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = paths[0]
    expected_to = "/home/output/BDPO/1894/11/07/"
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    # If a matching file exists, we can't handle anything.
    fs.create_file("/home/output/BDPO/1894/11/07/WO1_BDPO_1894_11_07-0008-054.xml")
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = None
    expected_to = "/home/output/BDPO/1894/11/07/WO1_BDPO_1894_11_07-0008-054.xml"
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    #
    # Test with a full path matching the P_SERVICE_SUBDAY pattern.
    #
    full_path = "/data/JISC/JISC1/JISC2_VOL1_C0/097/2001-0346/WO1/LEMR/1873/01/04_S/service/WO1_LEMR_1873_01_04_S-0001.xml"
    stub = "/data/JISC/JISC1/JISC2_VOL1_C0/097/2001-0346/WO1/LEMR"

    # If the title directory is missing, we can copy the entire title.
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = os.path.join(stubs[4], "")
    expected_to = "/home/output/LEMR/"
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    # If the matching month directory is missing, we can handle the entire month.
    fs.create_dir("/home/output/LEMR/1873/02/")
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = "/data/JISC/JISC1/JISC2_VOL1_C0/097/2001-0346/WO1/LEMR/1873/01/"
    expected_to = "/home/output/LEMR/1873/01/"
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    # If the matching day directory is missing, we can handle the entire day.
    # Note that in this case the 'copy from' directory includes the subday subscript.
    fs.create_dir("/home/output/LEMR/1873/01/03/")
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = (
        "/data/JISC/JISC1/JISC2_VOL1_C0/097/2001-0346/WO1/LEMR/1873/01/04_S/"
    )
    expected_to = "/home/output/LEMR/1873/01/04/"
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    # If the matching day directory exists, but not a matching file, we can handle the file.
    fs.create_dir("/home/output/LEMR/1873/01/04/")
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = full_path
    expected_to = "/home/output/LEMR/1873/01/04/"
    assert actual[0] == expected_from
    assert actual[1] == expected_to

    # If a matching file exists, we can't handle anything.
    fs.create_file("/home/output/LEMR/1873/01/04/WO1_LEMR_1873_01_04_S-0001.xml")
    actual = determine_from_to(full_path, len(stub), output_dir)
    expected_from = None
    expected_to = "/home/output/LEMR/1873/01/04/WO1_LEMR_1873_01_04_S-0001.xml"
    assert actual[0] == expected_from
    assert actual[1] == expected_to


def test_fix_title_code_anomaly():
    working_dir = "/home/working_dir/"
    path = "/data/JISC/JISC2/lsidyv785a3/LAGER-1892-12-31_mets.xml"
    expected = working_dir + "lsidyv785a3/LAGE-1892-12-31_mets.xml"

    actual = fix_title_code_anomaly(path, working_dir)

    assert actual == expected

    # The path variable has not changed.
    assert path == "/data/JISC/JISC2/lsidyv785a3/LAGER-1892-12-31_mets.xml"

    non_anomalous_path = "/data/JISC/JISC2/lsidyv10001b/MOPT-1861-12-05.xml"
    with raises(ValueError):
        fix_title_code_anomaly(non_anomalous_path, working_dir)


def test_fix_anomalous_title_codes(fs):
    # Use pyfakefs to fake the filesystem
    working_dir = "/home/working_dir/"
    fs.create_dir(working_dir)

    # Add an anomalous path to the list.
    paths_plus_one = paths.copy()
    anomalous_path = "/data/JISC/JISC2/lsidyv785a3/LAGER-1892-12-31_mets.xml"
    paths_plus_one.append(anomalous_path)
    expected = working_dir + "lsidyv785a3/LAGE-1892-12-31_mets.xml"

    # Use pyfakefs to fake the filesystem
    for path in paths_plus_one:
        fs.create_file(path)

    fix_anomalous_title_codes(paths_plus_one, working_dir)

    # All except the last (anomalous) one are unchanged.
    assert paths_plus_one[:-1] == paths
    assert paths_plus_one[-1] == expected

    # Check that the anomalous file has been copied and renamed.
    files_in_input_dir = utils.list_files("/data/")

    assert len(files_in_input_dir) == len(paths_plus_one)
    assert files_in_input_dir[:-1] == paths_plus_one[:-1]

    # The original anomalous file remains.
    assert files_in_input_dir[-1] == anomalous_path

    files_in_working_dir = utils.list_files(working_dir)

    # The title code in the file copied to the working directory has been fixed.
    assert len(files_in_working_dir) == 1
    assert files_in_working_dir[0] == expected
