process-ipcc
==============================
[![Build Status](https://travis-ci.com/hdrake/process-ipcc.svg?branch=master)](https://travis-ci.com/hdrake/process-ipcc)
[![codecov](https://codecov.io/gh/hdrake/process-ipcc/branch/master/graph/badge.svg)](https://codecov.io/gh/hdrake/process-ipcc)
[![License:MIT](https://img.shields.io/badge/License-MIT-lightgray.svg?style=flt-square)](https://opensource.org/licenses/MIT)

---------
## Current quality control status

I would consider the quality of the dataset to be adequate for `tas`, `pr`, `psl`, `uas`, `vas`, and `sfcWind` for FAR, SAR, and TAR and low for everything else. By adequate quality, I mean that the model output is 1) accurately described by its metadata and 2) the data has been properly re-coded from its original format to a CF-compliant Netcdf format, and 3) is ready for (careful) use in scientific projects.

The creation and homogenization of the metadata creation process could probably be improved and the data could be further tested by exploratory data analysis notebooks and unit tests.

---------
## Replication workflow

### Download raw data

Raw data can be downloaded directly from http://www.ipcc-data.org/sim/gcm_monthly/ to `/data/raw/`

Coming soon (?): raw files hosted directly on Zenodo

### Setting up the computing environment

Clone `process-ipcc` repository with
```bash
git clone git@github.com:hdrake/process-ipcc.git
```

Create and activate conda environment with
```bash
conda env create -f environment.yml
conda activate process-ipcc
```
This step may take a few minutes.

Open jupyter-lab instance begin your load one of the notebooks in /notebooks/
```bash
jupyter-lab
```

Setup Google Cloud SDK for pushing cloud-optimized model output to GCS (follow instructions in `../GoogleStorageInfo.txt`).

### Pre-process
Run the commands
```bash
cd scripts
python3 decode_FAR.py
python3 reformat_SAR_and_TAR.py
```

### Push to GCS
Change target bucket in last few lines of `zarrify_and_push_to_gcs.py` to whichever bucket you would like to push to (and for which you are an authenticated user).

Run the commands
```bash
python3 zarrify_and_push_to_gcs.py
```

---------
<p><small>Project based on the <a target="_blank" href="https://github.com/jbusecke/cookiecutter-science-project">cookiecutter science project template</a>.</small></p>
