
import struct
import netCDF4 as nc
import numpy as np
import os
import sys

sys.path.append("../process-ipcc")
import decoding as de
import models
import netcdf_util

load_dir = "../data/raw/FAR/"
save_dir = "../data/interim/FAR/"

os.system(command = f"mkdir -p {save_dir}")

# GFDL decadal mean
model = models.gfdl
nt = 10
V = np.zeros((nt,)+model.dims)
for t_idx in range(nt):
    with open(load_dir+"GFDL_1P/IPCC_DDC_FAR_GFDL_R15TR1P_D_1/ann.dec."+str((t_idx+1)*10), "rb") as binary_file:
        # Read the whole file at once
        bytes = binary_file.read()
    
    Vtmp = np.zeros(model.dims)
    for idx in range(Vtmp.size):
        
        # get index of flattened array
        unravel_idx = np.unravel_index(idx, model.dims)
        
        # get first index of data entry in binary file
        # note: function parameters are different for each model!
        byte_idx = model.get_byte_index(unravel_idx)
        
        # unpack binary data which are saved as 32-bit floats
        Vtmp[unravel_idx] = (
            struct.unpack(">f",bytes[byte_idx:byte_idx+4])[0]
        )

    V[t_idx,...] = Vtmp
    
# swap dimensions to standard order
V = V.swapaxes(2,3)

print("Processing ",model.name," files.")
# Create Netcdf files for a few variables of interest, defined at the very top of the notebook.
for far_name in list(model.output_names.keys()):
    var_name = model.output_names[far_name]
    print("- saving",var_name,end=" ")
    
    # Create netCDF4 file and resave the output to it
    ncfile_name = save_dir+var_name+"_decadal_FAR_GFDL-1P.nc"
    ncdata = netcdf_util.far_to_netcdf(ncfile_name, model)
    
    # read meta-data from GFDL documentation text file (submitted to IPCC-DDC w/ data)
    var = model.variables[var_name]
    
    # special case: variables with pressure dimension
    if var.last_index > var.first_index:
        nlev = var.last_index-var.first_index+1
        ncvar = ncdata.createVariable(var_name,'f8',('time','pressure','latitude','longitude',))
        for p in range(nlev):
            ncvar[:,p,:,:] = V[:,var.first_index + p,:,:]
        ncvar.description = var.description.strip()
        ncvar.units = var.units
        
    else:
        ncvar = ncdata.createVariable(var_name,'f8',('time','latitude','longitude',))
        ncvar[:,:,:] = np.squeeze(V[:,var.first_index,:,:])
        ncvar.description = var.description.strip()
        ncvar.units = var.units

        # apply mask to ocean for soil moisture content
        # HFD 05/30/19: I think this ends up masking some very moist parts of land.
        # This is where a proper land/ocean mask would be helpful.
        if var_name == "mrso":
            tmp = V[:,var.first_index,:,:]
            tmp[tmp == 15.] = np.nan
            ncvar[:,:,:] = tmp
        
    # apply unit conversion if necessary
    if far_name in list(model.unit_conversions.keys()):
        convert_units = model.unit_conversions[far_name]
        convert_units(ncvar)
        print("(converted units)")
    else:
        print("")
    
    # exceptions
    if var_name == "tas": ncvar.units = "K" # from "degrees K" to just "K"
    
    ncdata.setncattr("institution",model.name)
    ncdata.close()


# UKTR decadal mean
model = models.uktr
model.nt = 3

Vmonth = np.zeros((model.nt,)+model.dims)
# loop through files for each decadal-mean
for t_idx in range(model.nt):
    with open(load_dir+"UKTR_1P/IPCC_DDC_FAR_UKTR_1P_D_1/trans_years"+model.file_years[t_idx]+".bin", "rb") as binary_file:
        # Read the whole file at once
        bytes = binary_file.read()
    
    Vtmp = np.zeros(model.dims)
    for idx in range(Vtmp.size):
        # get index of flattened array
        unravel_idx = np.unravel_index(idx, model.dims)
        
        # get first index of data entry in binary file
        # note: function parameters are different for each model!
        byte_idx = model.get_byte_index(unravel_idx)
        
        # unpack binary data which are saved as 32-bit floats
        Vtmp[unravel_idx] = (
            struct.unpack(">f",bytes[byte_idx:byte_idx+4])[0]
        )
    Vmonth[t_idx,...] = Vtmp

# swap dimensions to give (nv, nt, nm, ny, nx)
Vmonth = np.transpose(Vmonth, (3, 0, 4, 2, 1))
    
# annual mean
days_in_month = [31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
days_in_year = np.sum(days_in_month)
V = np.zeros((model.nv,model.nt,model.ny,model.nx))
for t_idx in range(model.nt):
    for m_idx in range(12):
        V[:,t_idx,:,:] += Vmonth[:,t_idx,m_idx,:,:]*days_in_month[m_idx]/days_in_year

print("Processing ",model.name," files.")
# Create Netcdf files for a few variables of interest, defined at the very top of the notebook.
for far_name in list(model.output_names.keys()):
    var_name = model.output_names[far_name]
    print("- saving",var_name,end=" ")
    
    # UKTR-specific meta-data for order of variables in binary
    idx = model.var_shortnames.index(far_name)

    ncfile_name = save_dir+var_name+"_decadal_FAR_UKTR-1P.nc"
    ncdata = netcdf_util.far_to_netcdf(ncfile_name, model)
    
    ncvar = ncdata.createVariable(var_name,'f8',('time','latitude','longitude',))

    # Soil moisture is special case because it contains both sea ice and soil moisture data.
    # Someone at the Met Office thought they were very clever... took HFD weeks to decode this... Thank you for CF conventions
    if far_name == "SOILM":
        soil_moisture = np.copy(V[0,:,:,:])
        soil_moisture[soil_moisture >= 99.9] = np.nan
        ncvar[:,:,:] = soil_moisture
    elif far_name == "SEAICE":
        sea_ice_conc = np.copy(V[0,:,:,:])
        sea_ice_conc[sea_ice_conc <= 100.] = 0
        ncvar[:,:,:] = sea_ice_conc*1.e-3 # convert from per-thousand to fraction
        
    # read UKTR-specific meta-data from hard-coded variables
    else:
        ncvar[:,:,:] = V[model.var_idx[idx],:,:,:]
    ncvar.description = model.var_descriptions[idx]
    ncvar.units = model.var_units[idx]
    
    # unit conversion
    if far_name in list(model.unit_conversions.keys()):
        convert_units = model.unit_conversions[far_name]
        convert_units(ncvar)
        print("(converted units)")
    else:
        print("")
    
    ncdata.setncattr("institution",model.name)
    ncdata.close()

# GISS decadal mean
model = models.giss

Vmonth = np.zeros(model.dims)
with open(load_dir+"GISS_1P/IPCC_DDC_FAR_GISS_SCA_DATA_1/10yr_climo_1960-2059.bin", "rb") as binary_file:
    bytes = binary_file.read()

    # Read meta data from the header for later
    lines = []
    for i in range(model.nv):
        lines.append(bytes[
            4+(model.nbytes_data_cw + model.nx*model.ny*model.bytes_per_data_entry)*i:
            4+(model.nbytes_data_cw + model.nx*model.ny*model.bytes_per_data_entry)*i+80
        ].decode("UTF-8"))
    
    # read data byte by byte
    for idx in range(Vmonth.size):
        # get index of flattened array
        unravel_idx = np.unravel_index(idx, model.dims)

        # get first index of data entry in binary file
        # note: function parameters are different for each model!
        byte_idx = model.get_byte_index(unravel_idx)

        # unpack binary data which are saved as 32-bit floats (4 bytes)
        Vmonth[unravel_idx] = (
            struct.unpack(">f",bytes[byte_idx:byte_idx+4])[0])
        
# swap dimensions to give (nv, nt, nm, ny, nx)
Vmonth = np.transpose(Vmonth, (2, 4, 3, 1, 0))
    
# annual mean
days_in_month = [31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
days_in_year = np.sum(days_in_month)
V = np.zeros((model.nv,model.nt,model.ny,model.nx))
for t_idx in range(model.nt):
    for m_idx in range(12):
        V[:,t_idx,:,:] += Vmonth[:,t_idx,m_idx,:,:]*days_in_month[m_idx]/days_in_year

# The documentation seems to give the wrong grid since the Greenwich Meridian is at lon=180 instead of lon=0
model.lon = np.roll(np.mod(model.lon-180.,360),model.nx//2) # fixed longitude
V = np.roll(V,model.nx//2,axis=-1) # fixed variables according to longitude shift

# express all pressures in terms of meters
for i in range(len(model.pres_height_offset)):
    V[7+i:7+(i+1),:,:,:] += model.pres_height_offset[i]
    
# GISS-specific function for extracting usable meta data from header string
variables = models.get_variable_info(lines)

print("Processing ",model.name," files.")
# Create Netcdf files for a few variables of interest
for far_name in list(model.output_names.keys()):

    var_name = model.output_names[far_name]
    print("- saving",var_name,end=" ")

    ncfile_name = save_dir+var_name+"_decadal_FAR_GISS-SCA-1P.nc"
    ncdata = netcdf_util.far_to_netcdf(ncfile_name, model)
        
    # GISS-specific object containing variable meta-data
    var = variables[far_name]
    
    # special case of variables that depend on pressure
    if (var.last_index > var.first_index):
        
        # convert geopotential height into approximate temperature using hydrostatic balance finite difference
        if "1000 MB GEOPOTENTIAL HEIGHT" in var.name:
            # use the hydrostatic balance equation to solve for the temperature of each layer
            dz = V[var.first_index:var.last_index,:,:,:]-V[var.first_index+1:var.last_index+1,:,:,:]
            Tf = -model.pres[:,np.newaxis,np.newaxis,np.newaxis]*9.81/287.*dz/model.dp[:,np.newaxis,np.newaxis,np.newaxis]

            ncvar = ncdata.createVariable(var_name,'f8',('time','pressure','latitude','longitude',))
            ncvar[:,:,:,:] = Tf.swapaxes(0,1)[:,:,:,:]
            ncvar.description = var.description[8:]
            ncvar.units = var.units

    # surface (or otherwise spatially 2D variables)
    else:
        ncvar = ncdata.createVariable(var_name,'f8',('time','latitude','longitude',))
        ncvar[:,:,:] = V[var.first_index,:,:,:]
        ncvar.description = var.description
        ncvar.units = var.units

    # unit conversions
    if var.name in list(model.unit_conversions.keys()):
        convert_units = model.unit_conversions[var.name]
        convert_units(ncvar)
        print("(converted units)")
    else:
        print("")
    

    # sign convention for toa longwave flux
    if var_name == "rlut": ncvar[...] = -ncvar[...]

    # calculate surface longwave flux from net flux and solar flux
    if var_name == "rls": # note: rls variable for GISS is actually net flux
        
        inv_map = {v: k for k, v in model.output_names.items()}
        rss_var = variables[inv_map['rss']]
        # note sign convention on longwave flux
        ncvar[...] = -(V[var.first_index,:,:,:] - V[rss_var.first_index,:,:,:])

    ncdata.setncattr("institution",model.name)
    ncdata.close()
