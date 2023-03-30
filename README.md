# jisc-wrangler
A command line tool for restructuring data in the JISC 19th Century British Library Newspaper collection.

:construction: This tool is under construction :construction:


## Prerequisites

- Python >= 3.8
- [poetry](https://python-poetry.org/docs/)

## Installation

1. Clone this repo: `git clone https://github.com/Living-with-machines/jisc-wrangler.git`
2. Navigate into the repo: `cd jisc-wrangler`
3. Initialise a poetry shell: `poetry shell`
4. Install dependencies: `poetry install`

## Usage

### `jisc_wrangler_plain.py`

`jisc_wrangler_plain.py` is a command line tool for restructuring mangled and duplicated JISC newspaper XML files. The tool takes an input directory (`input_dir`) that contains mangled JISC data, restructures it and saves the output to a new location (`output_dir`).

```
python jisc_plain_wrangler.py /path/to/input/dir /path/to/output/dir
```

`jisc_plain_wrangler.py` will produce temporary files and a log file as it runs, the location of which can be set using the `--working-dir` argument.

For a full list of the tools runtime parameters run `python jisc_plain_wrangler.py --help`.

[An example run through. Also build some tests.]

```
python jisc_wrangler.py /path/to/input/dir /path/to/output/dir [--working_dir /path/to/working/dir] [--dry-run] [--debug]
```

### `jisc_alto2txt_wrangler.py`
