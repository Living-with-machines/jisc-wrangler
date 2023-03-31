# jisc-wrangler

:construction: This tool is under construction :construction:

![tests](https://github.com/Living-with-Machines/jisc-wrangler/actions/workflows/test.yml/badge.svg)
![GitHub](https://img.shields.io/github/license/Living-with-Machines/alto2txt) [![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

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

# jisc_plain_wrangler

[jisc_plain_wrangler.py](jisc_wrangler/jisc_plain_wrangler.py) is command line tool that organises the file paths of JISC data files into a format that can be used by [alto2txt](https://living-with-machines.github.io/alto2txt/#/).

## Usage :clipboard:

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

The tool takes an input directory (`input_dir`) that contains mangled and duplicated JISC data file paths and restructures them, writing the output to a new location (`output_dir`). As it runs, [jisc_plain_wrangler.py](jisc_wrangler/jisc_plain_wrangler.py) will produce temporary files and a log file, the locations of which can be set using the `--working_dir` argument.

```bash
python jisc_plain_wrangler.py /path/to/input/dir /path/to/output/dir --working_dir /path/to/working_dir
```

## Example

Say you have some XML data saved in a file called `WO1_BNWL_1874_01_01-0001-001.xml`. This represents a standard and logical way of organising newspaper XML files based on their publication dates. However, in many cases such files are stored on mangled file paths. This file, for example, is stored at:

`'0001_Job2001-Final Delivery   12$17$2006 at 12$49 PM/0001_$$Fileserver7$disk15$Job2001-masterfiles/2001-0289/Delivery/WO1/BNWL/1874/01/01/service/WO1_BNWL_1874_01_01-0001-001.xml'`

Aside from the white spaces and special characters that make this path tricky to process, the directory structure is not suitable for the XML files to be processed using [alto2txt](https://living-with-machines.github.io/alto2txt/#/).

[jisc_plain_wrangler.py](jisc_wrangler/jisc_plain_wrangler.py) uses the file name to reconstruct these paths to one that follows the format [expected by alto2txt](https://github.com/Living-with-machines/alto2txt/blob/main/README.md#process-types) and copies the file to this location, leaving the original structure unaltered.

Say this file path is located in a directory called `jisc-input`, [jisc_plain_wrangler.py](jisc_wrangler/jisc_plain_wrangler.py) will find the file and save it under a new path in a specified output directory:

```console
python jisc_plain_wrangler.py jisc-input jisc-output --working_dir jisc-logs
```

The output in the terminal looks like this:

```
>>> This is JISC Wrangler <<<
Logging to the working directory at: /jisc-logs/jw_2023-03-31_11h-35m-11s/jw.log
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

`jisc-logs` now contains a log file and a directory containing the running logs with the date and time the command was ran:

```
jisc-logs/
└── jw_2023-03-31_11h-35m-11s
    └── jw.log

1 directory, 1 file
```

- `jw_yyyy-mm-dd_hh-mm-ss` contains 4 possible output files:
    - `jw.log` logs every action [jisc_plain_wrangler.py](jisc_wrangler/jisc_plain_wrangler.py) made
    - `unmatched.txt`: lists files that do not match any of the directory patterns.
    - `ignored.txt` : lists files that are ignored by [jisc_plain_wrangler.py](jisc_wrangler/jisc_plain_wrangler.py).
    - `duplicates.txt` : lists files that have already been processed and are in the output directory.

Note: in this example these files are empty and so have not been created.

The resulting file structure is now fit for use with alto2txt. 

# jisc_alto2txt_wrangler

[jisc_alto2txt_wrangler.py](jisc_wrangler/jisc_alto2txt_wrangler.py) is a command line tool for replacing 4-character title codes with 7-digit NLP codes in the metadata XML files generated by executing [alto2txt](https://living-with-machines.github.io/alto2txt/#/) on the files processed by `jisc_plain_wrangler.py`. 

## Usage :clipboard:

```
jisc_alto2txt_wrangler.py
usage: jisc_alto2txt_wrangler.py [-h] [--working_dir WORKING_DIR] [--dry-run] [--debug] input_dir output_dir

Replace publication IDs in JISC alto2txt output

positional arguments:
  input_dir             Input directory containing JISC alto2txt output
  output_dir            Output directory to which updated alto2txt output is written

optional arguments:
  -h, --help            show this help message and exit
  --working_dir WORKING_DIR
                        Working directory to which temporary & log files are written
  --dry-run             Perform a dry run (don't copy any files)
  --debug               Run in debug mode (verbose logging)
```

The tool takes an input directory (`input_dir`) which contains `_metadata.xml` and `.txt` files outputed by `alto2txt`, modifies the title codes and saves the output to a new location (`output_dir`). As it runs, [jisc_alto2txt_wrangler.py](jisc_wrangler/jisc_alto2txt_wrangler.py) will produce temporary files and a log file, the locations of which can be set using the `--working_dir` argument.


```bash
python jisc_alto2txt_wrangler.py /path/to/input/dir /path/to/output/dir --working_dir /path/to/working_dir
```

## Example

Say you ran [alto2txt](https://living-with-machines.github.io/alto2txt/#/) on the file structure created in the previous example, this would spit out 2 new files:

- WO1_BNWL_1874_01_01-0001-001_metadata.xml
- WO1_BNWL_1874_01_01-0001-001.txt

Assuming these are in the directory created before (`jisc-output`) along side the copied xml file from `jisc_plain_wrangler`, we would process these files by proving this output directory as the *input directory* for `jisc_alto2txt_wrangler.py`. We need to specify a new **empty** directory to store the results in and a working directory for the log and temporary files produced (otherwise it will default to `.`). 

```console
python jisc_alto2txt_wrangler.py jisc-output jisc-alto2txt-output --working_dir jisc-alto2txt-logs
```
The output in the terminal looks like this:

```
>>> This is JISC alto2txt Wrangler <<<
Logging to the working directory at: jisc-alto2txt-logs/jw_alto2txt.log
Processing 1 metadata files
100%|█████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 606.90it/s]
```

The input directory `jisc-output` remains unaltered, whilst the previously empty directory `jisc-alto2txt-output` now has the same directory structure as `jisc_plain_wrangler.py`, but with the new files in:

```
jisc-alto2txt-output/
└── BNWL
    └── 1874
        └── 01
            └── 01
                ├── WO1_BNWL_1874_01_01-0001-001.txt
                └── WO1_BNWL_1874_01_01-0001-001_metadata.xml

4 directories, 2 files
```

The `_metadata.xml` file differs from original in that the xml version tag is removed and the publication id is replaced with a 7-digit NLP: "BNWL" -> "0000038".

The `.txt` file is just copied over from `jisc-output` and is unchanged from the original.


`jisc-alto2txt-logs` now contains a log file:

```
jisc-alto2txt-logs/
└── jw_alto2txt.log

0 directories, 1 file
```

# Copyright :copyright:

## Software

Copyright 2022 The Alan Turing Institute, British Library Board, Queen Mary University of London, University of Exeter, University of East Anglia and University of Cambridge.

See [LICENSE](LICENSE) for more details.

# Funding and Acknowledgements

This software has been developed as part of the [Living with Machines](https://livingwithmachines.ac.uk) project.

This project, funded by the UK Research and Innovation (UKRI) Strategic Priority Fund, is a multidisciplinary collaboration delivered by the Arts and Humanities Research Council (AHRC), with The Alan Turing Institute, the British Library and the Universities of Cambridge, East Anglia, Exeter, and Queen Mary University of London. Grant reference: AH/S01179X/1

> Last updated 2023-02-21
[^1]: For a more detailed description see: https://www.coloradohistoricnewspapers.org/forum/what-is-metsalto/
