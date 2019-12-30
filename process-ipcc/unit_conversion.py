# Some hard-coded functions for converting FAR variable units to CF-compliant units

def cm_per_s_to_m_per_s(ncvar):
    ncvar[...] = ncvar[...] * 1.e-2
    ncvar.units = "m s^-1"

def dyne_per_cm_squared_to_Pa(ncvar):
    ncvar[...] = ncvar[...] * 1.e-5 * (1.e2)**2
    ncvar.units = "Pa"

def cm_per_day_to_kg_per_m_squared_s(ncvar):
    rho_water = 1.e3 # density of water in kg m^-3
    sec_in_day = 60.*60.*24. # length of day in seconds
    ncvar[...] = ncvar[...] * 1.e-2 * sec_in_day**-1 * rho_water
    ncvar.units = "kg m^-2 s^-1"

def cm_to_m(ncvar):
    ncvar[...] = ncvar[...] * 1.e-2
    ncvar.units = "m"

def percent_to_fraction(ncvar):
    ncvar[...] = ncvar[...] * 1.e-2
    ncvar.units = "1"

def identity(ncvar):
    pass

def mm_per_day_to_kg_per_m_squared_s(ncvar):
    rho_water = 1.e3 # density of water in kg m^-3
    sec_in_day = 60.*60.*24. # length of day in seconds
    ncvar[...] = ncvar[...] * 1.e-3 * sec_in_day**-1 * rho_water
    ncvar.units = "kg m^-2 s^-1"
    
def cm_to_kg_per_m_squared(ncvar):
    rho_water = 1.e3 # density of water in kg m^-3
    ncvar[...] = ncvar[...] * 1.e-2 * rho_water
    ncvar.units = "kg m^-2"
    
def kg_per_m_squared_to_m(ncvar):
    rho_water = 1.e3 # density of water in kg m^-3
    ncvar[...] = ncvar[...] * rho_water**-1
    ncvar.units = "m"
    
def C_to_K(ncvar):
    ncvar[...] = ncvar[...] + 273.15
    ncvar.units = "K"
    
def ly_per_min_to_W_per_m_squared(ncvar):
    to_W_hour_per_min_m_squared = 11.622
    ncvar[...] = ncvar[...] * to_W_hour_per_min_m_squared * 60.
    ncvar.units = "W m^-2"