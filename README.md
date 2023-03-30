# jisc-wrangler

:construction: This tool is under construction :construction:

![GitHub](https://img.shields.io/github/license/Living-with-Machines/alto2txt) ![PyPI](https://img.shields.io/pypi/v/alto2txt) [![DOI](https://zenodo.org/badge/259340615.svg)](https://zenodo.org/badge/latestdoi/259340615) [![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

A command line tool for restructuring data in the JISC 19th Century British Library Newspaper collection.

#  Prerequisites :paperclip:

- Python >= 3.8
- [poetry](https://python-poetry.org/docs/)

To use **jisc_alto2txt_wrangler** you will need to have used [alto2txt](https://living-with-machines.github.io/alto2txt/#/) on the files processed by **jisc_plain_wrangler**.

#  Installation :gear:

1. Clone this repo: `git clone https://github.com/Living-with-machines/jisc-wrangler.git`
2. Navigate into the repo: `cd jisc-wrangler`
3. Initialise a poetry shell: `poetry shell`
4. Install dependencies: `poetry install`

#  Usage :clipboard:

## jisc_plain_wrangler

```
jisc_plain_wrangler.py -h
usage: jisc_plain_wrangler.py [-h] [--working_dir WORKING_DIR] [--dry-run] [--debug] input_dir output_dir

Restructure mangled & duplicated JISC newspaper XML files

positional arguments:
  input_dir             Input directory containing mangled JISC data
  output_dir            Output directory to which clean JISC data are written

optional arguments:
  -h, --help            show this help message and exit
  --working_dir WORKING_DIR
                        Working directory to which temporary & log files are written
  --dry-run             Perform a dry run (don't copy any files)
  --debug               Run in debug mode (verbose logging)

```

[jisc_plain_wrangler.py](jisc_wrangler/jisc_plain_wrangler.py) takes an input directory (`input_dir`) that contains mangled and duplicated JISC data file paths and restructures them, writing the output to a new location (`output_dir`).

```bash
python jisc_plain_wrangler.py /path/to/input/dir /path/to/output/dir
```

[jisc_plain_wrangler.py](jisc_wrangler/jisc_plain_wrangler.py) will produce temporary files and a log file as it runs, the locations of which can be set using the `--working_dir` argument.

### Example

Say you have some XML data saved in a file called `WO1_BNWL_1874_01_01-0001-001.xml`. This represents a standard and logical way of organising newspaper XML files based on their publication dates. However, in many cases these files are stored on mangled file paths. This file, for example, is stored at:

`'0001_Job2001-Final Delivery   12$17$2006 at 12$49 PM/0001_$$Fileserver7$disk15$Job2001-masterfiles/2001-0289/Delivery/WO1/BNWL/1874/01/01/service/WO1_BNWL_1874_01_01-0001-001.xml'`

Aside from the white spaces and special characters, the directory structure is not suitable for the XML files to be processed using [alto2txt](https://living-with-machines.github.io/alto2txt/#/).

[jisc_plain_wrangler.py](jisc_wrangler/jisc_plain_wrangler.py) used the file name to reconstruct these paths to one that follows the format [expected by alto2txt](https://github.com/Living-with-machines/alto2txt/blob/main/README.md#process-types) and copies the file to this location, leaving the original structure unaltered.

Say this file path is located in a directory called `jisc-input`, [jisc_plain_wrangler.py](jisc_wrangler/jisc_plain_wrangler.py) will find the file and save it under a new path in a specified output directory:

```console
python jisc_plain_wrangler.py jisc-input jisc-output --working_dir jisc-logs
```

The output in the terminal looks like this:

```
>>> This is JISC Wrangler <<<
Logging to the current directory at:
%s /jisc-logs/jw.log
Processing 1 unique title code directory...
100%|█████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 358.21it/s]
```

The input directory, `jisc-input` remains unaltered, whilst the previously empty directory `jisc-output` now has the file name as the directory structure:

```
jisc-output/
└── BNWL
    └── 1874
        └── 01
            └── 01
                └── WO1_BNWL_1874_01_01-0001-001.xml

4 directories, 1 file
```

`jisc-logs` now contains a log file and a directory continuing the running logs with the date and time the command was ran:

```
jisc-logs/
├── jw.log
└── jw_2023-03-30_11h-12m-10s

1 directory, 1 file
```

- `jw.log` logs every action [jisc_plain_wrangler.py](jisc_wrangler/jisc_plain_wrangler.py) made
- `jw_yyyy-mm-dd_hh-mm-ss` contains three possible output files:
    - `unmatched.txt`: lists files that do not match any of the directory patterns.
    - `ignored.txt` : lists files that are ignored by [jisc_plain_wrangler.py](jisc_wrangler/jisc_plain_wrangler.py).
    - `duplicates.txt` : lists files that have already been processed and are in the output directory.

Note: in this example these files are empty and so have not been created.

 The resulting file structure is now fit for use with alto2txt. 

## jisc_alto2txt_wrangler

[jisc_alto2txt_wrangler.py](jisc_wrangler/jisc_alto2txt_wrangler.py) is a command line tool for replacing 4-character title codes with 7-digit NLP codes in the metadata XML files generated by executing [alto2txt](https://living-with-machines.github.io/alto2txt/#/) on the files processed by `jisc_plain_wrangler.py`. Only the XML content of the _metadata.xml files produced by [alto2txt](https://living-with-machines.github.io/alto2txt/#/) is modified. Specifically, the value of the "id" attribute associated with the "publication" element is changed from a **4-character title** code to a **7-digit NLP code**.File structure and names are unchanged (i e. duplicated in the output), to ensure that paths and files quoted to in the metadata XML remain valid.




# Copyright :copyright:

## Software

Copyright 2022 The Alan Turing Institute, British Library Board, Queen Mary University of London, University of Exeter, University of East Anglia and University of Cambridge.

See [LICENSE](LICENSE) for more details.

# Funding and Acknowledgements

This software has been developed as part of the [Living with Machines](https://livingwithmachines.ac.uk) project.

This project, funded by the UK Research and Innovation (UKRI) Strategic Priority Fund, is a multidisciplinary collaboration delivered by the Arts and Humanities Research Council (AHRC), with The Alan Turing Institute, the British Library and the Universities of Cambridge, East Anglia, Exeter, and Queen Mary University of London. Grant reference: AH/S01179X/1

> Last updated 2023-02-21
[^1]: For a more detailed description see: https://www.coloradohistoricnewspapers.org/forum/what-is-metsalto/
