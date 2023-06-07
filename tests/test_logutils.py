"""Tests for logging.py"""

from jisc_wrangler import logutils


def test_setup_logging(fs, mocker):
    mockfunc = mocker.patch("importlib.metadata.version")
    mockfunc.return_value("jisc-wrangler")
    args = mocker.patch("argparse.Namespace")

    # test no dry run and debug=False
    args.dry_run = False
    args.debug = False
    args.working_dir = "/home/tests/"
    testfile = "home/tests/logfile.txt"
    fs.create_file(testfile)
    logutils.setup_logging(args, "logfile.txt")
    with open(testfile, "r") as reader:
        lines = reader.readlines()
    assert len(lines) == 1
    assert "INFO" in lines[0]

    # test dry run and debug=True
    args2 = mocker.patch("argparse.Namespace")
    args2.dry_run = True
    args2.debug = True
    args2.working_dir = "/home/tests2/"
    testfile2 = "home/tests2/logfile.txt"
    fs.create_file(testfile2)
    logutils.setup_logging(args2, "logfile.txt")
    with open(testfile2, "r") as reader:
        lines = reader.readlines()
    assert len(lines) == 2
    assert "DRY RUN" in lines[-1]
