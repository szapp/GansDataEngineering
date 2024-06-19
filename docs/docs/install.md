# Installation

Download or clone the [repository](https://github.com/szapp/GansDataEngineering), navigate to the root directory and run the following command from the command-line.

```bash
pip install -r requirements.txt
```

Alternatively, install the package for outside of the directory with

```bash
pip install -e .
```

No further setup is necessary.
The SQL database with all tables will be created by the pipeline given that an MySQL instance exists.
Find the created database schema in [usage](usage.md).
