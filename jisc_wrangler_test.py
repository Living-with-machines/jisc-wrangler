from jisc_wrangler import *
from unittest.mock import create_autospec

paths = ['/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/11/07/service/WO1_BDPO_1894_11_07-0008-054.xml',
         '/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/11/07/service/WO1_BDPO_1894_11_07-0008-055.xml',
         '/data/JISC/JISC1_VOL1_C0/009/Data/Job-2001/Batch_0162/2001-0162/WO1/RDNP/1862/01/05/service/WO1_RDNP_1862_01_05-0001-001.xml',
         '/data/JISC/JISC1_VOL1_C0/009/Data/Job-2001/Batch_0162/2001-0162/WO1/RDNP/1862/01/05/service/WO1_RDNP_1862_01_05-0001-002.xml',
         '/data/JISC/JISC1/JISC2_VOL1_C0/097/2001-0346/WO1/LEMR/1873/01/04_S/service/WO1_LEMR_1873_01_04_S-0001.xml']
stubs = ['/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO',
         '/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO',
         '/data/JISC/JISC1_VOL1_C0/009/Data/Job-2001/Batch_0162/2001-0162/WO1/RDNP',
         '/data/JISC/JISC1_VOL1_C0/009/Data/Job-2001/Batch_0162/2001-0162/WO1/RDNP',
         '/data/JISC/JISC1/JISC2_VOL1_C0/097/2001-0346/WO1/LEMR']


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


def test_extract_pattern_stubs():

    # The first five paths match the P_SERVICE pattern.
    actual = extract_pattern_stubs(service_pattern, paths)
    assert actual == stubs[:4]

    # The fifth path matches the P_SERVICE_SUBDAY pattern.
    actual = extract_pattern_stubs(service_subday_pattern, paths)
    assert actual == stubs[4:5]

    # None of the paths matches the P_MASTER pattern.
    actual = extract_pattern_stubs(master_pattern, paths)
    assert actual == []


def test_count_matches_in_list():

    l = paths

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
