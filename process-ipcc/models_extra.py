from decoding import *
from unit_conversion import *
import datetime
import numpy as np

#=========== GISS MODEL (Control Run) ==============
## Encoding information
giss_ctl = cipher("GISS-CTL")
model = giss_ctl

model.var_list = None

model.nx = 36
model.ny = 24
model.nv = 8
model.nm = 12
model.nt = 100

model.dims = (model.nx, model.ny, model.nv, model.nm, model.nt)

model.data_cw_dim = 1

model.nheader = 1
model.ndata = 144

## Grid information from documentation
model.lon = np.arange(0,360,10)
model.lat = np.arange(-90,91,7.826)

# pressure variables for calculating T(p) from geopotential height
pres = np.array([1000., 850, 700, 500, 300, 100, 30])
model.pres = ((pres[:-1]+pres[1:])/2.) # pressure at cell faces
model.dp = (pres[0:-1]-pres[1:]) # pressure grid spacing
model.pres_height_offset = np.array([0, 1500, 3000, 5600, 9500, 16400, 24000])

# time grid constructed according to notes from the IPCC-DDC: decadal-means starting in 1950
model.date = np.array([np.datetime64(datetime.date(year, month, 15))
                 for year in range(1858,1958) for month in range(1,13)])

# dictionary relating GFDL variable names to CF-convention names
model.output_names = {
    "COMPOSITE SURFACE AIR TEMPERATURE" : "tas"
}

# dictionary of functions 
model.unit_conversions = {
    "COMPOSITE SURFACE AIR TEMPERATURE" : C_to_K
}

model.variable_idx = {
    "tas" : 5
}
model.variable_units = {
    "tas" : "C"
}