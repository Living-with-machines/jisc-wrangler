"""Tests for logging.py"""

from jisc_wrangler import logutils


def test_setup_logging(fs, mocker):
    mockfunc = mocker.patch("importlib.metadata.version")
    mockfunc.return_value("jisc-wrangler")
    args = mocker.patch("argparse.Namespace")

    # test no dry run and debug=False
    args.dry_run = False
    args.debug = False
    testfile = "home/tests/logfile.txt"
    fs.create_file(testfile)
    logutils.setup_logging(args, testfile)
    with open(testfile, "r") as reader:
        lines = reader.readlines()
    assert len(lines) == 1
    assert "INFO" in lines[0]

    # test dry run and debug=True
    args2 = mocker.patch("argparse.Namespace")
    args2.dry_run = True
    args2.debug = True
    logutils.setup_logging(args2, testfile)
    with open(testfile, "r") as reader:
        lines = reader.readlines()
    assert len(lines) == 2
    assert "DRY RUN" in lines[-1]
