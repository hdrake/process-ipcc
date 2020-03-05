#!/usr/bin/env python
# coding: utf-8

import os
import xarray as xr
import pandas as pd

experiment_id_dict = {
    "1pctCO2": {"FAR":"1P", "SAR":"GG"},
    "historical": {"FAR":"1P", "SAR":"GS", "TAR":"SRES-A2"},
    "piControl": {"FAR":"CI", "SAR":"CI"}
}
source_id_attrs = {"FAR": "institution", "SAR": "institution", "TAR": "institution"}

activity_ids = ["FAR","SAR","TAR"]
variable_ids = ["tas", "psl", "pr", "rsds", "sn", "sic", "tasmax", "tasmin", "uas", "vas", "sfcWind"]
table_id = "Amon"

push_to_cloud = True

stop = 0
for activity_id in activity_ids:
    
    os.system(command=f"mkdir -p ../data/zarr/{activity_id}/")
    
    fs_dict = {
        "activity_id": [],
        "institution_id": [],
        "source_id": [],
        "experiment_id": [],
        "member_id": [], 
        "table_id": [], 
        "variable_id": [], 
        "grid_label": [], 
        "zstore": [],
        "dcpp_init_year": []
    }
    
    path_to_nc = f"../data/interim/{activity_id}/"
    for experiment_id in experiment_id_dict.keys():
        for variable_id in variable_ids:
            for ncfile in os.listdir(path_to_nc):
                if activity_id not in experiment_id_dict[experiment_id]: continue # experiment doesn't exist
                if experiment_id_dict[experiment_id][activity_id] not in ncfile: continue # wrong experiment

                ds = xr.open_dataset(path_to_nc+ncfile, decode_cf=False)
                
                if variable_id not in ds.data_vars: continue # wrong variable

                # Write to zarr
                institution_id = ds.attrs[source_id_attrs[activity_id]]

                # If different source_id and member_id for a single institution (as in SAR)
                if activity_id == 'SAR':
                    source_id = institution_id+'-'+str(ncfile[2:4])
                    member_id = f"r{ncfile[7:8]}i1p1f1"                    
                else:
                    source_id = institution_id
                    member_id = "r1i1p1f1"
                
                zarr_name = f"{institution_id}/{source_id}/{experiment_id}/{member_id}/{table_id}/{variable_id}/gn/"
                path_to_zarr = f"../data/zarr/{activity_id}/"+zarr_name

                ds.to_zarr(path_to_zarr, mode='w', consolidated=True)

                fs_dict["activity_id"].append(activity_id)
                fs_dict["institution_id"].append(institution_id)
                fs_dict["source_id"].append(source_id)
                fs_dict["experiment_id"].append(experiment_id)
                fs_dict["member_id"].append(member_id)
                fs_dict["table_id"].append(table_id)
                fs_dict["variable_id"].append(variable_id)
                fs_dict["grid_label"].append("gn")
                fs_dict["zstore"].append(f"gs://ipcc-{activity_id.lower()}/{activity_id}/"+zarr_name)
                fs_dict["dcpp_init_year"].append("NaN")
                print(zarr_name)

    # Write csv catalog to Zarr data folder
    df = pd.DataFrame.from_dict(fs_dict)
    path_to_csv = f"../data/zarr/{activity_id}/pangeo-{activity_id.lower()}.csv"
    df.to_csv(path_to_csv, index=False)

    # Write catalog json to Zarr data folder
    os.system(command=f"cp ../catalogs/pangeo-{activity_id.lower()}.json ../data/zarr/{activity_id}/")   
    
    if push_to_cloud:
        print(f"\nPush {activity_id} data to Google Cloud storage:")
        transfer_command = f"../data/zarr/{activity_id} gs://ipcc-{activity_id.lower()}/"
        gsutil_command = f"gsutil -m cp -r {transfer_command}"
        print(gsutil_command+"\n\n")
        os.system(command=gsutil_command)
        os.system(command=f"gsutil -m cp ../data/zarr/{activity_id}/pangeo-{activity_id.lower()}.json  gs://ipcc-{activity_id.lower()}")
        os.system(command=f"gsutil -m cp ../data/zarr/{activity_id}/pangeo-{activity_id.lower()}.csv  gs://ipcc-{activity_id.lower()}")
