# Xenia Analysis

## Install
```
conda env create -f environment.yml
conda env list | grep xenia_analysis  # test env was created
conda activate xenia_analysis
```

## Update
```
git pull
conda activate xenia_analysis
conda env update -f environment.yml --prune
```

## Run
```
conda activate xenia_analysis
python main.py
```