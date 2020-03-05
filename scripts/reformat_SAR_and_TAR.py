#!/usr/bin/env python
# coding: utf-8


from git import Repo
import os
import numpy as np
import xarray as xr
import pandas as pd
import scipy
import Nio
import datetime
import sys

script_full_path = '/scripts/reformat_SAR_and_TAR.py'

#=================================
# Process SAR models

# Second Assessment Report (SAR) Model Output

load_dir = "../data/raw/SAR/"
save_dir = "../data/interim/SAR/"
os.system(command=f"mkdir -p {save_dir}")

def date_to_datetime(dates,reference_date):
    date = np.array(
        [datestr.split(" ")[0].split("/")[2] + "-" +
         datestr.split(" ")[0].split("/")[0] + "-" +
         datestr.split(" ")[0].split("/")[1]
         for datestr in np.array(dates.values).astype("str")]
    ).astype("datetime64")
    return (date-reference_date)/np.array([1]).astype("<m8[D]")

# Main loop
nexp = 0
for institution in os.listdir(load_dir):
    if ("." in institution): continue
    for file_name in os.listdir(load_dir+institution+"/"):
        nexp+=1
print("Total # of experiments: "+str(nexp))

# Variable metadata copied from http://cfconventions.org/Data/cf-standard-names/27/build/cf-standard-name-table.html
standard_dict = {}
standard_dict['long_name'] = {
    'tas': 'Near-Surface Air Temperature',
    'psl': 'Sea Level Pressure',
    'pr': 'Precipitation',
    'rsds': 'Downwelling Shortwave Flux at Surface',
    'sn': 'Snow Amount',
    'tasmax': 'Maximum Near-Surface Air Temperature',
    'tasmin': 'Minimum Near-Surface Air Temperature',
    'sfcWind': 'Near-Surface Wind Speed'
}
standard_dict['description'] = {
    'tas': 'temperature at 2-meter height',
    'psl': 'not, in general, the same as surface pressure',
    'pr': 'at surface; includes both liquid and solid phases from all types of clouds',
    'rsds': """
    The surface called "surface" means the lower boundary of the atmosphere. 
    "shortwave" means shortwave radiation. Downwelling radiation is radiation from above.
    It does not mean "net downward". Surface downwelling shortwave is the sum of direct
    and diffuse solar radiation incident on the surface, and is sometimes called "global
    radiation". When thought of as being incident on a surface, a radiative flux is
    sometimes called "irradiance". In addition, it is identical with the quantity measured
    by a cosine-collector light-meter and sometimes called "vector irradiance". In
    accordance with common usage in geophysical disciplines, "flux" implies
    per unit area, called "flux density" in physics.
    """,
    'sn': '"Amount" means mass per unit area.',
    'tasmax': 'Monthly-mean daily-maximum temperature at 2-meter height',
    'tasmin': 'Monthly-mean daily-minimum temperature at 2-meter height',
    'sfcWind': """
    'Speed is the magnitude of velocity. Wind is defined as a two-dimensional (horizontal)
    air velocity vector, with no vertical component. (Vertical motion in the atmosphere has
    the standard name upward_air_velocity.) The wind speed is the magnitude of the wind
    velocity.'
    """
}
standard_dict['standard_name'] = {
    'tas': 'air_temperature',
    'psl': 'air_pressure_at_sea_level',
    'pr': 'precipitation_flux',
    'rsds': 'surface_downwelling_shortwave_flux',
    'sn': 'snow_amount',
    'tasmax': 'air_temperature',
    'tasmin': 'air_temperature',
    'sfcWind': 'wind_speed'
}
standard_dict['units'] = {
    'tas': 'K',
    'psl': 'Pa',
    'pr': 'kg m^-2 s^-1',
    'rsds': 'W m^-2',
    'sn': 'kg m^-2',
    'tasmax': 'K',
    'tasmin': 'K',
    'sfcWind': 'm s^-1'
}

for institution in os.listdir(load_dir):
    if ("." == institution[0]): continue
    stop = 0
    for var_name in os.listdir(load_dir+institution+"/"):
        if ("." == var_name[0]): continue
        for file_name in os.listdir(load_dir+institution+"/"+var_name+"/"):
            if ("." == file_name[0]): continue
                
            run_name = str.split(file_name,"_")[0]
            
            print("\n"+institution+"/"+var_name+"/"+file_name, end="")

            # Load data into xarray dataset using PyNio engine
            ds = xr.open_dataset(load_dir+institution+"/"+var_name+"/"+file_name,engine="pynio", decode_times=True)
            
            # Make coordinates CF-compliant
            var_change_dict = {}
            var_change_dict[list(ds.dims)[0]] = 'latitude'
            var_change_dict[list(ds.dims)[1]] = 'longitude'
            var_change_dict[list(ds.dims)[2]] = 'time'
            ds = ds.rename(var_change_dict)
            ds.coords['latitude'].attrs['axis']='Y'
            ds.coords['latitude'].attrs['standard_name'] = 'latitude'
            ds.coords['longitude'].attrs['axis']='X'
            ds.coords['longitude'].attrs['standard_name'] = 'longitude'
            ds.coords['time'].attrs['long_name'] = 'time'
            ds.coords['time'].attrs['axis'] = 'T'
            ds = ds.drop(['initial_time0_encoded','initial_time0'])

            # Give temperature variable to standard names and description
            var_names = ds.variables.keys()
            for nam in var_names:
                if not(("latitude" in nam) or ("longitude" in nam) or ("time" in nam)):
                    ds = ds.rename({nam:var_name})

            # Convert precipitation data from kg/m^2/day to kg/m^2/s
            if var_name == "pr":
                ds[var_name] /= (24.*60.*60.)
                        
            for attrs_name in list(standard_dict.keys()):
                ds[var_name].attrs[attrs_name] = standard_dict[attrs_name][var_name]
                
            ds[var_name] = ds[var_name].where(ds[var_name]!=-999., np.nan)
            
            #=========================================
            # Quality control measures
            
            # Fix MPIfM latitudes
            if institution == "MPIfM":
                ds['latitude'].values = ds['latitude'].values[::-1]
            # Ignore GFDL mean sea level pressure because it is actually surface pressure
            if var_name == "psl":
                if "GFDL" in institution:
                    ds.close()
                    continue
            #=========================================
            
            # Declare CF-convention compliance
            ds.attrs['Conventions'] = 'CF-1.7'

            # Metadata 
            ds.attrs['title'] = 'Projections from a Second Assessment Report model'
            ds.attrs['institution'] = institution
            ds.attrs['modelling_center'] = ds[var_name].attrs['center']
            if 'model' in ds.attrs:
                ds.attrs['source'] = ds[var_name].attrs['model']
            else: 
                ds.attrs['source'] = 'N/A'

            # Generate data provenance entry:
            # time stamp, command line arguments, environment, and hash for git commit
            time_stamp = datetime.datetime.now().strftime("%a %b %d %H:%M:%S %Y")
            args = " ".join(sys.argv)
            exe = sys.executable
            git_hash = Repo(os.getcwd()+'/..').head.commit.hexsha[0:7]
            history_entry = ("{time_stamp}: {exe} {args} {script_full_path} (Git hash: {git_hash})"
                     .format(time_stamp=time_stamp,
                             exe=exe,
                             args=args,
                             script_full_path=script_full_path,
                             git_hash = git_hash))
            ds.attrs['history'] = history_entry

            # Write xarray dataset to netCDF4 file
            ncfile_name = save_dir+run_name+"_"+var_name+".nc"

            try: ds.to_netcdf(ncfile_name, mode='w', encoding={'time':{'units':'days since 1990-01-01 0:0:0'}})
            except: 'Got some error w/ respect to time units that disqualified this run.'
            ds.close()

#=================================
# Process TAR models

# Third Assessment Report (TAR) Model Output
load_dir = "../data/raw/TAR/"
save_dir = "../data/interim/TAR/"
os.system(command=f"mkdir -p {save_dir}")

# Main loop
nexp = 0
for institution in os.listdir(load_dir):
    if ("." in institution): continue
    for file_name in os.listdir(load_dir+institution+"/"):
        nexp+=1
print("\nTotal # of experiments: "+str(nexp))

for institution in os.listdir(load_dir):
    if ("." == institution[0]): continue
    stop = 0
    for var_name in os.listdir(load_dir+institution+"/"):
        if ("." == var_name[0]): continue
        for file_name in os.listdir(load_dir+institution+"/"+var_name+"/"):
            if ("." == file_name[0]): continue
                
            run_name = str.split(file_name,"_")[0]+"_"+str.split(file_name,"_")[1]+"-"+str.split(file_name,"_")[2]
            
            print("\n"+institution+"/"+var_name+"/"+file_name, end="")

            # Load data into xarray dataset using PyNio engine
            ds = xr.open_dataset(load_dir+institution+"/"+var_name+"/"+file_name,engine="pynio",decode_times=True)

            # Make coordinates CF-compliant
            var_change_dict = {}
            var_change_dict[list(ds.dims)[0]] = 'latitude'
            var_change_dict[list(ds.dims)[1]] = 'longitude'
            var_change_dict[list(ds.dims)[2]] = 'time'
            ds = ds.rename(var_change_dict)
            ds.coords['latitude'].attrs['axis']='Y'
            ds.coords['latitude'].attrs['standard_name'] = 'latitude'
            ds.coords['longitude'].attrs['axis']='X'
            ds.coords['longitude'].attrs['standard_name'] = 'longitude'
            ds.coords['time'].attrs['long_name'] = 'time'
            ds.coords['time'].attrs['axis'] = 'T'
            ds = ds.drop(['initial_time0_encoded','initial_time0'])
            
            # Give temperature variable to standard names and description
            var_names = ds.variables.keys()
            for nam in var_names:
                if not(("latitude" in nam) or ("longitude" in nam) or ("time" in nam)):
                    ds = ds.rename({nam:var_name})

            for attrs_name in list(standard_dict.keys()):
                ds[var_name].attrs[attrs_name] = standard_dict[attrs_name][var_name]
                
            # Convert precipitation data from kg/m^2/day (is this really the units?) to kg/m^2/s
            if var_name == "pr":
                ds[var_name] /= (24.*60.*60.)
                
            ds[var_name] = ds[var_name].where(ds[var_name]!=-999., np.nan)

            #=========================================
            # Quality control measures
            
            # Fix EH4OPYC latitudes
            if institution == "MPIfM":
                ds['latitude'].values = ds['latitude'].values[::-1]
            # Convert mean sea level pressure units from mbar to Pa for some models
            if (var_name == "psl"):
                if ("CCCma" in institution) or ("CCSR" in institution) or ("CSIRO" in institution):
                    ds[var_name] *= 100.
            # Ignore GFDL mean sea level pressure because it is actually surface pressure
            if var_name == "psl":
                if "GFDL" in institution:
                    ds.close()
                    continue
            
            #=========================================
            
            # Declare CF-convention compliance
            ds.attrs['Conventions'] = 'CF-1.7'

            # Metadata 
            ds.attrs['title'] = 'Projections from a Third Assessment Report model'
            ds.attrs['institution'] = institution
            ds.attrs['modelling_center'] = ds[var_name].attrs['center']
            if 'model' in ds.attrs:
                ds.attrs['source'] = ds[var_name].attrs['model']
            else: 
                ds.attrs['source'] = 'N/A'

            # Generate data provenance entry:
            # time stamp, command line arguments, environment, and hash for git commit
            time_stamp = datetime.datetime.now().strftime("%a %b %d %H:%M:%S %Y")
            args = " ".join(sys.argv)
            exe = sys.executable
            git_hash = Repo(os.getcwd()+'/..').head.commit.hexsha[0:7]
            history_entry = ("{time_stamp}: {exe} {args} {script_full_path} (Git hash: {git_hash})"
                     .format(time_stamp=time_stamp,
                             exe=exe,
                             args=args,
                             script_full_path=script_full_path,
                             git_hash = git_hash))
            ds.attrs['history'] = history_entry

            # Write xarray dataset to netCDF4 file
            ncfile_name = save_dir+run_name+"_"+var_name+".nc"
            try: ds.to_netcdf(ncfile_name, mode='w', encoding={'time':{'units':'days since 1990-01-01 0:0:0'}})
            except: 'Got some error w/ respect to time units that disqualified this run.'
            ds.close()





