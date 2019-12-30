import numpy as np
    
class far_variable():
    pass
    
class cipher:
    def __init__(self,name):
        self.name = name
        self.var_list = None
        
    def get_byte_index(self,idx):
        baseline_idx = self.bytes_per_data_entry
        byte_idx = self.nbytes_header_cw + self.nbytes_header + self.nbytes_data_cw
        for (ndim, dim_idx) in zip(self.dims, list(range(len(self.dims)))):
            byte_idx += baseline_idx * idx[dim_idx]
            
            baseline_idx *= self.dims[dim_idx]
            if dim_idx == self.data_cw_dim:
                baseline_idx += self.nbytes_data_cw
                
        return byte_idx