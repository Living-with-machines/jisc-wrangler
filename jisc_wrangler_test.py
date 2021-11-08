from jisc_wrangler import *
from unittest.mock import create_autospec

paths = ['/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/11/07/service/WO1_BDPO_1894_11_07-0008-054.xml',
         '/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO/1894/11/07/service/WO1_BDPO_1894_11_07-0008-055.xml']
stubs = ['/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO',
         '/data/JISC/JISC1_VOL4_C1/042/0002_Job2001-final delivery  12$17$2006 at 2$48 PM/0001_$$Fileserver8$disk19$tape/2001-0274/Delivery/WO1/BDPO']


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

    actual = extract_pattern_stubs(service_pattern, paths)
    assert actual == stubs
