import xarray as xr
import pandas as pd
import numpy as np

def weighted_mean(da, dim=None, weights=None):
    if weights is None:
        return da.mean(dim)
    else:
        if not isinstance(weights,xr.DataArray):
            raise ValueError("weights must be a DataArray")
        total_weights = weights.where(da.notnull()).sum(dim)
        return (da * weights).sum(dim) / total_weights

def weighted_std(da, dim=None, weights=None):
    if weights is None:
        return da.std(dim)
    else:
        if not isinstance(weights,xr.DataArray):
            raise ValueError("weights must be a DataArray")
        total_weights = weights.where(da.notnull()).sum(dim)
        return np.sqrt(
            (da-weighted_mean(da, dim, weights)).sum(dim)**2 / total_weights
            )

def open_dataset(file_path,name=None):
    ds = xr.open_dataset(file_path)
    if name is None: ds.attrs['name'] = file_path.split('.')[-2].split('/')[-1]
    else: ds.attrs['name']=name
    return ds

class Ensemble:
    """
    Represents an ensemble of gridded data sets
    """
    def __init__(self,name,ds_list):
        # Creates a new ensemble Xarray dataset by concatenating 
        # variable data arrays along new dimension 'run'
        self.name = name
        self.ds_dict = dict(zip([run.attrs['name'] for run in ds_list],ds_list))

    def to_common_spatiotemporal_grid(self,coords,**kwargs):
        for ds in self.ds_dict.keys():
            if 'time' in coords:
                kwargs['fill_value'] = np.nan
                self.ds_dict[ds] = self.ds_dict[ds].interp(
                    coords,
                    method="linear",
                    kwargs=kwargs,
                )
            else:
                self.ds_dict[ds] = self.ds_dict[ds].interp(
                    coords,
                    method="nearest",
                    kwargs=kwargs
                )

    def generate_ensemble(self,var_name):
        ds = xr.concat(self.ds_dict.values(),dim='run')
        self.ds = ds.update({'run': ('run', list(self.ds_dict.keys()))})
        self.ds[var_name].attrs["units"] = (
            self.ds_dict[list(self.ds_dict.keys())[0]][var_name].attrs["units"]
        )

    def multi_model_mean(self):
        ds_tmp = weighted_mean(self.ds, dim='run').expand_dims(dim='run')
        ds_tmp.coords['run']=['mmm']
        self.ds = xr.concat([self.ds, ds_tmp],dim='run')

    def calc_trends(self, var_name, x_dim = "time", include_uncertainty = False, include_intercept = False):
        trend_dims = list(self.ds[var_name].dims)
        trend_dims.remove(x_dim)
        trend_shape = [self.ds.dims[dim] for dim in trend_dims]
        
        trend_dim_idx = self.ds[var_name].dims.index(x_dim)
        
        other_idx = list(range(0,len(self.ds[var_name].dims)))
        other_idx.remove(trend_dim_idx)
        reorder_idx = [trend_dim_idx]+other_idx
        
        reordered_dims = list(np.array(list(self.ds[var_name].dims))[reorder_idx])
        
        n_cells = np.product(trend_shape)

        # convert time to days on x-axis
        x = ((self.ds[x_dim]-np.datetime64('1990'))/np.timedelta64(1,'D')).values[:]
        y_arr = self.ds[var_name].transpose(*reordered_dims).values.reshape([x.size,n_cells])
        trend_arr = np.zeros(n_cells)
        trend_unc_arr = np.zeros(n_cells)
        y0_arr = np.zeros(n_cells)
        
        for i in range(n_cells):
            y = y_arr[:,i]
            
            idx = np.logical_and(~np.isnan(x),~np.isnan(y))
            xtmp=x[idx]; ytmp=y[idx]

            if xtmp.size == 0:
                trend_arr[i] = np.nan
                y0_arr[i] = np.nan
            else:
                tmp = np.polyfit(x=xtmp,y=ytmp,deg=1)
                trend_arr[i] = tmp[0]
                y0_arr[i] = tmp[1]
                
            if include_uncertainty:
                ## HFD 08/13/2019 - I don't think this is right...
                # Calculate standard error in regression slope
                yhat = y0_arr[i] + trend_arr[i]*xtmp
                ntot = xtmp.size
                degfree = 2.0
                trend_unc_arr[i] = np.sqrt(
                        np.sum((ytmp - yhat)**2.0) /
                        np.sum((xtmp - np.average(xtmp))**2.0) /
                        (ntot - degfree)
                )

        
        trend_arr *= 365.25 # convert to year^-1 units
        self.ds[var_name+'_trend'] = xr.DataArray(
            trend_arr.reshape(trend_shape),dims=trend_dims
        )
        
        if include_intercept:
            self.ds[var_name+'_trend-y0'] = xr.DataArray(
                y0_arr.reshape(trend_shape),dims=trend_dims
            )
        
        trend_unc_arr *= 365.25 # convert to year^-1 units
        if include_uncertainty:
            self.ds[var_name+'_trend-unc'] = xr.DataArray(
                trend_unc_arr.reshape(trend_shape),dims=trend_dims
            )
            
    def to_default_grid(self,years=[1990,2020],dlon=3.,dlat=3.):
        new_longitude = np.arange(0+dlon/2.,360,dlon)
        new_latitude = np.arange(-90+dlat/2.,90,dlat)
        
        reference_date = np.datetime64("1990","D")
        year = np.repeat(np.arange(years[0], years[1]),12).astype("int").astype("str")
        month = np.tile(np.arange(1,13),year.size//12+1)[0:year.size].astype("str")
        date = np.array(
            [year[i].zfill(4)+"-"+month[i].zfill(2)+"-01"
             for i in range(year.size)]
        ).astype("datetime64")
        new_time = date

        self.to_common_spatiotemporal_grid(
            {'latitude': new_latitude, 'longitude': new_longitude},
            fill_value=None,
        )
        self.to_common_spatiotemporal_grid(
            {'time': new_time},
            fill_value=None,
        )

    def to_default_grid_pressure(self,years=[1990,2020]):
        dlon = 3.; dlat = 3.;
        new_longitude = np.arange(0+dlon/2.,360,dlon)
        new_latitude = np.arange(-90+dlat/2.,90,dlat)
        new_pressure = np.array([950.,800.,650.,500.,350.,250.,175.,125.,100.,50.,25.])
        
        reference_date = np.datetime64("1990","D")
        year = np.repeat(np.arange(years[0], years[1]),12).astype("int").astype("str")
        month = np.tile(np.arange(1,13),year.size//12+1)[0:year.size].astype("str")
        date = np.array(
            [year[i].zfill(4)+"-"+month[i].zfill(2)+"-01"
             for i in range(year.size)]
        ).astype("datetime64")
        new_time = date

        self.to_common_spatiotemporal_grid(
            {'latitude': new_latitude, 'longitude': new_longitude, 'pressure': new_pressure},
            fill_value=None,
        )
        self.to_common_spatiotemporal_grid(
            {'time': new_time},
            fill_value=None,
        )
