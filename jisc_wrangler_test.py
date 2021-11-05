from jisc_wrangler import *
from unittest.mock import create_autospec


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
