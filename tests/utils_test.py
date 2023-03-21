import os

from jisc_wrangler import constants, utils

from .test_constants import *


def test_list_files(fs):
    # Use pyfakefs to fake the filesystem.
    dir = "/home/"

    assert utils.list_files(dir) == []

    fs.create_dir("/home/output/")
    fs.create_dir("/home/output/ABCD/")
    assert utils.list_files(dir) == []

    fs.create_file("/home/output/ABCD/abc.xml")
    assert os.path.isfile("/home/output/ABCD/abc.xml")
    assert utils.list_files(dir) == ["/home/output/ABCD/abc.xml"]

    fs.create_file("/home/xyz.txt")
    assert set(utils.list_files(dir)) == set(
        ["/home/output/ABCD/abc.xml", "/home/xyz.txt"]
    )


def test_list_all_subdirs(fs):
    # Use pyfakefs to fake the filesystem
    dir = "/home/"

    assert utils.list_all_subdirs(dir) == []

    fs.create_dir("/home/output/")
    fs.create_dir("/home/output/ABCD/")
    assert set(utils.list_all_subdirs(dir)) == set(
        ["/home/output/", "/home/output/ABCD/"]
    )

    fs.create_file("/home/output/ABCD/abc.xml")
    assert os.path.isfile("/home/output/ABCD/abc.xml")
    assert set(utils.list_all_subdirs(dir)) == set(
        ["/home/output/", "/home/output/ABCD/"]
    )

    fs.create_dir("/home/XYZ/")
    assert set(utils.list_all_subdirs(dir)) == set(
        ["/home/output/", "/home/output/ABCD/", "/home/XYZ/"]
    )


def test_count_matches_in_list():
    l = paths.copy()

    # This prefix is common to all of the paths.
    p = "/data/JISC/JISC1"
    assert utils.count_matches_in_list(p, l) == 5

    # This prefix is common to the first four paths.
    p = "/data/JISC/JISC1_VOL"
    assert utils.count_matches_in_list(p, l) == 4

    # The stubs[0] matches the beginning of both the paths.
    p = stubs[0]
    assert utils.count_matches_in_list(p, l) == 2

    p = "/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/11/07/service/"
    assert utils.count_matches_in_list(p, l) == 2

    p = "/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/11/07/service/WO1_BDPO_1894_11_07-0008-054"
    assert utils.count_matches_in_list(p, l) == 1

    # Matches are found only up to the first non-match in the list.
    p = "/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/11/07/service/WO1_BDPO_1894_11_07-0008-055"
    assert utils.count_matches_in_list(p, l) == 0

    p = "data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/11/07/service/"
    # Note the missing '/' at the beginning of p.
    assert utils.count_matches_in_list(p, l) == 0

    p = stubs[0]
    # Insert a non-matching string at index 1 (2nd position).
    l.insert(1, "XXX")
    # Matches are found only up to the first non-match in the list.
    assert utils.count_matches_in_list(p, l) == 1

    l = []
    p = "/data/JISC/JISC1_VOL"
    assert utils.count_matches_in_list(p, l) == 0


def test_alt_output_file():
    file_path = "/jisc1and2full/clean/ANJO/1891/01/07/WO1_ANJO_1891_01_07-0001-001.xml"
    expected = (
        "/jisc1and2full/clean/ANJO/1891/01/07/WO1_ANJO_1891_01_07-0001-001"
        + constants.ALT_FILENAME_SUFFIX
        + ".xml"
    )
    actual = utils.alt_output_file(file_path)

    assert actual == expected
