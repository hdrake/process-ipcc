from decoding import *
from unit_conversion import *
import datetime
import numpy as np

# This file contains hard-coded meta-data for the UKTR, GISS, and GFDL simulations.
# Most of this meta data comes directly from the supplementary text files submitted 
# to the IPCC-DDC simultaneously with the simulation output (also present in the github
# repository for this paper).

# Some of the meta-data was determined by HFD from additional supporting information.
# For example, Rou Stouffer supplied him with the original documentation for the R-15
# GFDL model, which contained a list of the pressure values for the pressure levels.
# HFD tried to document (in comment in this file and the script that processes the data)
# all cases where the meta-data was not supplied via the documentation submitted to the 
# IPCC-DDC.

# Some of the remaining meta-data was determined by HFD after two years of ad-hoc method
# and many hours of trial and error. In particular, the lengths of the header control word,
# headers, and data control words documented here appear to be inconsistent with those
# in the supplementary files documenting the simulation output. HFD discovered the correct
# byte lengths by brute force trying all reasonable combinations until he was able extract
# physically-reasonable values for all variables at all times and at every grid point.
# The counter-intuitive use of negative lengths for header control words or headers is
# simply to account for the fact that the different modelling centers define headers and
# header control words differently. This combination is convenient because it allows the
# exact same decoding function to be used for each of the three models, regardless of the
# ordering of the variables, their definitions of headers and header control words, and
# where they choose to place the data control words.

#=========== GFDL MODEL ==============
## Encoding information
gfdl = cipher("GFDL")
model = gfdl
model.var_list = "../data/raw/FAR/GFDL_1P/add_info_var_list_R15_170"

model.nv = 170
model.nx = 48
model.ny = 40
model.dims = (model.nv, model.nx, model.ny)

model.data_cw_dim = 0

model.nbytes_header_cw = 20
model.nbytes_header = 392
model.nbytes_data_cw = 8
model.bytes_per_data_entry = 4

## Grid information from documentation
# grid longitude
model.lon = np.arange(0,360,7.5)

# grid latitude
model.lat = np.array([-86.5980, -82.1909, -77.7578, -73.3188, -68.8776, -64.4353, -59.9925, -55.5492, -51.1057, -46.6620, -42.2183, -37.7744, -33.3305, -28.8865, -24.4425, -19.9984, -15.5543, -11.1102, -6.6662, -2.2220, 2.2220, 6.6662, 11.1102, 15.5543, 19.9984, 24.4425, 28.8865, 33.3305, 37.7744, 42.2183, 46.6620, 51.1057, 55.5492, 59.9925, 64.4353, 68.8776, 73.3188, 77.7578, 82.1909, 86.5980])

# sigma and pressure values of the vertical coordinate from the 9-level model 
# documentation shared by Ron Stouffer.
model.sigm = np.array([0.025, 0.095, 0.205, 0.350, 0.515, 0.680, 0.830, 0.940, 0.990])
model.pres = np.array([25.33, 96.26, 207.7, 354.6, 521.8, 689.0, 841.0, 952.4, 1013.])

# time grid constructed according to notes from the IPCC-DDC: decadal-means starting in 1950
model.year =  (np.array([(tt+1)*10-5 for tt in range(10)])+1950).astype("str")
model.date = model.year.astype("datetime64")

# dictionary relating GFDL variable names to CF-convention names
model.output_names = {
    "T1 - T9": "ta",
    "T9" : "tas",
    "U9" : "uas",
    "V9" : "vas",
    "PRECIP" : "pr",
    "SOILM" : "mrso",
    "SNWDPT" : "snd",
    "SWTOP" : "rsdt",
    "LWTOP" : "rlut",
    "SWBOT" : "rss",
    "LWBOT" : "rls"
}

# dictionary of unit conversion functions
model.unit_conversions = {
    "U9" : cm_per_s_to_m_per_s,
    "V9" : cm_per_s_to_m_per_s,
    "PRECIP" : cm_per_day_to_kg_per_m_squared_s,
    "PSTAR" : dyne_per_cm_squared_to_Pa,
    "SNWDPT" : cm_to_m,
    "SOILM" : cm_to_kg_per_m_squared,
    "SWTOP" : ly_per_min_to_W_per_m_squared,
    "LWTOP" : ly_per_min_to_W_per_m_squared,
    "SWBOT" : ly_per_min_to_W_per_m_squared,
    "LWBOT" : ly_per_min_to_W_per_m_squared
}


# Open supplementary info file and read variable meta-data
f = open(model.var_list,"r")
lines = f.readlines()

model.variables = {}
for line in lines:
    tmp_variable = far_variable()
    
    try:
        # characters 0:9 give index of variable
        tmp_variable.first_index = np.int(line[0:9].split('-')[0])-1
        try:
            tmp_variable.last_index = np.int(line[0:9].split('-')[1])-1
        except:
            tmp_variable.last_index = tmp_variable.first_index
    except: pass # ignore lines that do not fit the format for variables

    tmp_variable.name = line[9:21].strip()
    tmp_variable.description = line[21:59].strip()
    tmp_variable.units = line[59:].split('\n')[0]
    
    # If line corresponds to a variable, append the variable meta data
    if tmp_variable.name in model.output_names:
        model.variables[gfdl.output_names[tmp_variable.name]] = tmp_variable
        
    # Add near-surface values of fields with pressure dimension as own variables
    if (" - " in tmp_variable.name):
        surface_name = tmp_variable.name.split("-")[1].strip()
        if (surface_name in gfdl.output_names):
            surface_variable = far_variable()
            surface_variable.first_index = tmp_variable.last_index
            surface_variable.last_index = tmp_variable.last_index
            surface_variable.name = surface_name
            surface_variable.description = tmp_variable.description+". Near-surface value."
            surface_variable.units = tmp_variable.units
            model.variables[model.output_names[surface_variable.name]] = surface_variable

#=========== UKTR MODEL ==============
## Encoding information
uktr = cipher("UKTR")
model = uktr

model.var_list = None

model.nx = 96
model.ny = 72
model.nv = 4
model.nm = 12
model.dims = (model.nx, model.ny, model.nv, model.nm)

model.data_cw_dim = 1

model.nbytes_header_cw = 12
model.nbytes_header = -16 # truncates first part of data_cw at beginning of file
model.nbytes_data_cw = 16+256
model.bytes_per_data_entry = 4

## Grid information from documentation
# grid longitude
model.lon = np.arange(1.875, 360, 3.75)

# grid latitude
model.lat = np.arange(88.75,-90,-2.5)

# all variables for uktr are surface or near-surface, so just use surface pressure
model.pres = np.array([1013.])

# time grid constructed according to notes from the IPCC-DDC: decadal-means starting in 1950
model.file_years = ["1-10","51-60","66-75"]
model.year =  (np.array([5,55,70])+1950).astype("str")
model.date = model.year.astype("datetime64")

# dictionary relating UKTR variable names to CF-convention names
model.output_names = {
    "SAT": "tas",
    "PRECIP" : "pr",
    "SOILM" : "mrso",
    "SEAICE" : "sic",
}

# dictionary of functions 
model.unit_conversions = {
    "PRECIP" : mm_per_day_to_kg_per_m_squared_s,
    "SOILM" : cm_to_kg_per_m_squared
}

# hard-coded variable metadata for the UKTR runs
# HFD came up with this metadata in an ad-hoc method by looking at plots
# and guessing which of the four variables in the documentation corresponded to which of the four indices.
# Eventually, I realized the Soil Moisture data also included sea ice, which presumably was a useful way
# someone at the UK Met Office found to save on data storage space by putting a land-only variable and
# an ocean-only variable in the same array.
model.var_shortnames = ["SOILM", "SEAICE", "PRECIP", "SAT", "SOLRAD"]
model.var_idx = [0,0,1,2,3]
model.var_descriptions = ["Soil Moisture",
                         "Sea Ice Concentration",
                         "Precipitation",
                         "Surface Air Temperature",
                         "Surface Solar Radiation"]
model.var_units = ["cm", "1", "mm day^-1", "K", "W m^-2"]


#=========== GISS MODEL ==============
## Encoding information
giss = cipher("GISS")
model = giss

model.var_list = None

model.nx = 36
model.ny = 24
model.nv = 56
model.nm = 12
model.nt = 10 # HFD 07/26/19: This should be generalized so that it works for SCB too (which has model.nt = 7)!!!

model.dims = (model.nx, model.ny, model.nv, model.nm, model.nt)

model.data_cw_dim = 1

model.nbytes_header_cw = -4 # 64 + 16+4 - nbytes_data_cw
model.nbytes_header = 0
model.nbytes_data_cw = 88 # 64+4 + 16+4
model.bytes_per_data_entry = 4

## Grid information from documentation
model.lon = np.arange(0,360,10)
model.lat = np.arange(-90,91,7.826)

# pressure variables for calculating T(p) from geopotential height
pres = np.array([1000., 850, 700, 500, 300, 100, 30])
model.pres = ((pres[:-1]+pres[1:])/2.) # pressure at cell faces
model.dp = (pres[0:-1]-pres[1:]) # pressure grid spacing
model.pres_height_offset = np.array([0, 1500, 3000, 5600, 9500, 16400, 24000])

# time grid constructed according to notes from the IPCC-DDC: decadal-means starting in 1950
model.year = (np.array([(tt+1)*10-5 for tt in range(model.nt)])+1960).astype("str")
model.date = model.year.astype("datetime64")

# dictionary relating GFDL variable names to CF-convention names
model.output_names = {
    "1000 MB GEOPOTENTIAL HEIGHT": "ta",
    "COMPOSITE SURFACE AIR TEMPERATURE" : "tas",
    "U COMPON OF COMPOSITE SURFACE AIR WIND" : "uas",
    "V COMPON OF COMPOSITE SURFACE AIR WIND" : "vas",
    "PRECIPITATION" : "pr",
    "TOTAL CLOUD COVER" : "clt",
    "COMPOSITE SNOW DEPTH" : "snd",
    "OCEAN ICE COVERAGE" : "sic",
    "NET SOLAR RADIATION AT P0" : "rsdt",
    "NET THERMAL RADIATION AT P0" : "rlut",
    "COMPOSITE NET SOLAR RADIATION AT SURFCE" : "rss",
    "COMPOSITE NET RADIATION AT SURFACE" : "rls",
}

# dictionary of functions 
model.unit_conversions = {
    "OCEAN ICE COVERAGE" : percent_to_fraction,
    "COMPOSITE SNOW DEPTH" : kg_per_m_squared_to_m,
    "PRECIPITATION" : mm_per_day_to_kg_per_m_squared_s,
    "TOTAL CLOUD COVER" : percent_to_fraction,
    "COMPOSITE SURFACE AIR TEMPERATURE" : C_to_K
}

# simple variable meta data container
class data_variable:
    name = ''
    description = ''
    units = ''
    first_index = None
    last_index = None

# simple function for parsing binary file header string for variable meta-data
def get_variable_info(lines):
    variables = {}

    vv = 0
    line_i = 0
    for line in lines:
        variable = data_variable()

        name_str = line[0:40].strip()
        description_str = line[0:40].strip()+'  '+line[58:].strip()
        units_str = line[40:58].strip()[1:-1]

        if (7 <= line_i <= 13):
            variable.first_index = 7
            variable.last_index = 13
            units_str = 'm'
            if (line_i == 7): vv += 1
            else: pass
        else:
            variable.first_index = line_i
            variable.last_index = line_i
            vv += 1

        variable.name = name_str
        variable.description = description_str
        variable.units = units_str

        if not(8 <= line_i <= 13): variables[variable.name] = variable
        line_i += 1
    return variables
