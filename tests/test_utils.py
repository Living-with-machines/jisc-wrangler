import os
from datetime import datetime

from pytest import raises

from jisc_wrangler import constants, utils

from .test_constants import *


def test_flattern():
    nested_list = [["a", 1], ["b", 2], ["c", 3], ["d", 4], ["e", 5]]
    expeted = ["a", 1, "b", 2, "c", 3, "d", 4, "e", 5]
    assert utils.flatten(nested_list) == expeted


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


def test_count_lines(fs):
    filenumber = 120
    file_contents = "\n".join([f"{i}" for i in range(filenumber)])
    fakefile = "/home/xyz.txt"
    fs.create_file(fakefile, contents=file_contents)
    assert utils.count_lines(fakefile) == filenumber
    assert utils.count_lines(fakefile.replace(".txt", "_.txt")) == 0


def test_count_all_files(fs):
    fs.create_dir("/home/output/ABCD/")
    for i in range(4):
        fs.create_file(f"/home/output/ABCD/abc-{i}.xml")
    assert utils.count_all_files("/home/output/ABCD/") == 4


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


def test_remove_duplicates():
    before = ["a", "b", "d", "c", "a"]
    after = ["a", "b", "d", "c"]
    after_sort = ["a", "b", "c", "d"]
    assert len(utils.remove_duplicates(before)) == len(after)
    assert utils.remove_duplicates(before, sort_them=True) == after_sort


def test_hash_file(fs):
    filenumber = 120
    file_contents = "\n".join([f"{i}" for i in range(filenumber)])
    fakefile = "/home/xyz.txt"
    fs.create_file(fakefile, contents=file_contents)
    assert utils.hash_file(fakefile) == "553cb5c5e571a4e16e897e58364e1212"


def test_alt_output_file():
    file_path = "/jisc1and2full/clean/ANJO/1891/01/07/WO1_ANJO_1891_01_07-0001-001.xml"
    expected = (
        "/jisc1and2full/clean/ANJO/1891/01/07/WO1_ANJO_1891_01_07-0001-001"
        + constants.ALT_FILENAME_SUFFIX
        + ".xml"
    )
    actual = utils.alt_output_file(file_path)

    assert actual == expected


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


def test_move_from_to(fs):
    dir1 = "/home/output1/"
    fs.create_dir(dir1)
    for i in range(4):
        fs.create_file(dir1 + f"abc-{i}.xml")
    dir2 = "/home/output2/"
    assert not os.path.isdir(dir2)
    utils.move_from_to(dir1, dir2)
    assert os.path.isdir(dir2)
    assert not os.path.isdir(dir1)
    for i in range(4):
        assert os.path.exists(dir2 + f"abc-{i}.xml")


def test_write_unmactched_file(fs):
    testdir = "/home/output/"
    testfile = testdir + "unmatched.txt"
    fs.create_dir(testdir)
    fs.create_file(testfile)
    assert not os.path.exists(testdir + "jw_unmatched.txt")
    utils.write_unmatched_file(["aa/bbb/c_2021_33/ee"], testdir)
    assert os.path.exists(testdir + "jw_unmatched.txt")
    with open(testdir + "jw_unmatched.txt", "r") as reader:
        assert reader.read().rstrip() == "aa/bbb/c_2021_33/ee"
    utils.write_unmatched_file(["aa/eeee/c_2021_33/ee"], testdir)
    with open(testdir + "jw_unmatched.txt", "r") as reader:
        assert reader.readlines()[-1].rstrip() == "aa/eeee/c_2021_33/ee"


def test_ignore_file(fs):
    testdir = "/home/output/"
    ignoredir = "/home/ignoredir/"
    testfile = testdir + "ignoreme.txt"
    fs.create_dir(testdir)
    fs.create_dir(ignoredir)
    fs.create_file(testfile)
    assert not os.path.exists(ignoredir + "jw_ignored.txt")
    utils.ignore_file(testfile, ignoredir)
    assert os.path.exists(ignoredir + "jw_ignored.txt")
    with open(ignoredir + "jw_ignored.txt", "r") as reader:
        assert reader.read().rstrip() == testfile
    testfile2 = testdir + "ignoremetoo.txt"
    utils.ignore_file(testfile2, ignoredir)
    with open(ignoredir + "jw_ignored.txt", "r") as reader:
        assert reader.readlines()[-1].rstrip() == testfile2


def test_date_in_range():
    start = datetime.strptime("01-03-2023", "%d-%m-%Y")
    end = datetime.strptime("01-04-2023", "%d-%m-%Y")
    date_between = datetime.strptime("15-03-2023", "%d-%m-%Y")
    date_before = datetime.strptime("01-02-2023", "%d-%m-%Y")
    date_after = datetime.strptime("01-05-2023", "%d-%m-%Y")
    assert utils.date_in_range(start, end, date_before) is False
    assert utils.date_in_range(start, end, date_between) is True
    assert utils.date_in_range(start, end, date_after) is False
    errormsg = f"Invalid date interval. Start: {end}, End: {start}."
    with raises(ValueError, match=errormsg):
        utils.date_in_range(end, start, date_between)


def test_parse_publication_date():
    date_str = "1999-01-01"
    expected = ("1999", "01", "01")
    assert expected == utils.parse_publicaton_date(date_str)
