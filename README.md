# Xenia Analysis

## Usage
### Install
```bash
conda env create -f environment.yml && echo
conda env list | grep xenia_analysis  # test env was created
conda activate xenia_analysis
```

### Run
see `data/example/` for more on how to organize the input metadata.

to process files run:
```bash
conda activate xenia_analysis
python main.py -i data/example/
```
#### common usage
add data, for example `data/new_h5s`
```bash
conda activate xenia_analysis

# create the details.json the code expect for each data dir
python xenia_analysis/xenio.py -i data/new_h5s/

# process the files and generate (in addition to plot htmls) xslx file
# save the output to dir with suffix "my-new-h5s"
python xenia_analysis/main.py -i data/new_h5s/ --gen-csv --out-dir-suffix "my-new-h5s"

# export - zip the outputs
python xenia_analysis/scripts/export_latest_output.py
```

### Update
```bash
git pull
conda activate xenia_analysis
conda env update -f environment.yml --prune && echo
```
