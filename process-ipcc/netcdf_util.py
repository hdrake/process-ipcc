import os
import netCDF4 as nc
import numpy as np

def far_to_netcdf(ncfile_name, model):
    
    if os.path.isfile(ncfile_name): os.remove(ncfile_name)
    ncdata = nc.Dataset(ncfile_name,"w","NETCDF4")    

    time = ncdata.createDimension('time', model.date.size)
    times = ncdata.createVariable("time", "f8",("time",));
    reference_date = np.datetime64("1990","D")
    times[:] = (model.date-reference_date)/np.array([1]).astype("<m8[D]")
    times.units = 'days since 1990-1-1 0:0:0'
    
    latitude = ncdata.createDimension('latitude', model.lat.size)
    latitudes = ncdata.createVariable("latitude", "f8",("latitude",));
    latitudes[:] = model.lat
    latitudes.units = 'degrees north'
    
    longitude = ncdata.createDimension('longitude', model.lon.size)
    longitudes = ncdata.createVariable("longitude","f8",("longitude",));
    longitudes[:] = model.lon
    longitudes.units = 'degrees east'
    
    pressure = ncdata.createDimension('pressure', model.pres.size)
    pressures = ncdata.createVariable("pressure", "f8",("pressure",));
    pressures[:] = model.pres
    pressures.units = 'hPa'

    return ncdata