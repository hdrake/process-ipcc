process-ipcc
==============================
[![Build Status](https://travis-ci.com/hdrake/process-ipcc.svg?branch=master)](https://travis-ci.com/hdrake/process-ipcc)
[![codecov](https://codecov.io/gh/hdrake/process-ipcc/branch/master/graph/badge.svg)](https://codecov.io/gh/hdrake/process-ipcc)
[![License:MIT](https://img.shields.io/badge/License-MIT-lightgray.svg?style=flt-square)](https://opensource.org/licenses/MIT)

--------
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

---------
### Download raw data

Raw data can be downloaded directly from http://www.ipcc-data.org/sim/gcm_monthly/ to `/data/raw/`

Coming soon (?): raw files hosted directly on Zenodo

---------
### Setup Google Cloud SDK for pushing cloud-optimized model output to GCS

Follow instructions in `../GoogleStorageInfo.txt`.

---------
<p><small>Project based on the <a target="_blank" href="https://github.com/jbusecke/cookiecutter-science-project">cookiecutter science project template</a>.</small></p>
