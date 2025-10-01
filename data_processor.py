import os
import numpy as np
import netCDF4 as nc
import json
import requests
from geojson import Feature, Point, FeatureCollection

# --- CONFIGURATION ---
# NASA data source details (Chlorophyll-a from MODIS-Aqua NRT)
# This example uses a static URL. Replace this with a system to fetch the LATEST NRT file.
NASA_DATA_URL = "https://oceandata.sci.gsfc.nasa.gov/cgi/getfile/A20252652025265.L3m_DAY_CHL_chl_ocx.nc"
LOCAL_NETCDF_FILE = "nasa_nrt_data.nc"
OUTPUT_GEOJSON_FILE = "data/nasa-blooms.json"
CHL_THRESHOLD = 0.5  # Chlorophyll-a concentration threshold for a "bloom" (mg/m³)

import os # Import the os library at the top

# ... (rest of your imports and config) ...

def download_data(url, filename):
    """Downloads the NetCDF file from NASA and checks for size/validity."""
    print(f"Downloading data from: {url}...")
    try:
        # NOTE: For Earthdata access, you often need to provide credentials
        r = requests.get(url, allow_redirects=True, timeout=90)
        r.raise_for_status() # Check for HTTP errors

        with open(filename, 'wb') as f:
            f.write(r.content)
        
        # Check if the downloaded file is suspiciously small (e.g., less than 50 KB)
        # An error/login page is usually small. A NetCDF file is large.
        if os.path.getsize(filename) < 50000: 
             print("WARNING: Downloaded file is too small. It might be an HTML error page.")
             print("Please ensure you have an **Earthdata Login** and use a proper API or NASA tool for data access.")
             return False # Treat as a failure
             
        print("Download successful and file size seems correct.")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"CRITICAL ERROR during download: {e}")
        return False

def process_netcdf_to_geojson(netcdf_file):
    """Reads NetCDF, filters blooms, and converts to GeoJSON."""
    try:
        data = nc.Dataset(netcdf_file)
    except FileNotFoundError:
        print(f"Error: NetCDF file not found at {netcdf_file}")
        return

    # Extract required variables
    lats = data.variables['lat'][:]
    lons = data.variables['lon'][:]
    chl_a = data.variables['chl_ocx'][:]  # Chlorophyll-a array (your intensity)

    # Get metadata for the GeoJSON properties
    satellite_source = data.sensor
    date_range = data.time_coverage_start.split('T')[0]

    features = []
    
    # Iterate through the 2D array (ocean data is gridded)
    # This loop is simplified for a NetCDF file with lat/lon grids
    # In a production environment, vectorization (NumPy) is faster.
    for i in range(len(lats)):
        for j in range(len(lons)):
            # Get the Chlorophyll value at this lat/lon
            intensity = chl_a[i, j] 

            # Step 4: Implement Bloom Threshold (Filter)
            if intensity is not np.ma.masked and intensity > CHL_THRESHOLD:
                # Create the GeoJSON properties dictionary
                properties = {
                    "intensity": float(f"{intensity:.2f}"), # Two decimal places
                    "type": "Phytoplankton Bloom",
                    "date": date_range,
                    "source": satellite_source
                }
                
                # Create a GeoJSON Point feature
                point = Point((float(lons[j]), float(lats[i])))
                features.append(Feature(geometry=point, properties=properties))

    print(f"Found {len(features)} bloom features above the threshold.")
    return FeatureCollection(features)

def save_geojson(geojson_data, output_path):
    """Writes the GeoJSON FeatureCollection to a file."""
    if geojson_data and geojson_data['features']:
        with open(output_path, 'w') as f:
            json.dump(geojson_data, f)
        print(f"Successfully saved bloom data to {output_path}")
    else:
        print("No bloom data to save.")


if __name__ == "__main__":
    if download_data(NASA_DATA_URL, LOCAL_NETCDF_FILE):
        geojson_output = process_netcdf_to_geojson(LOCAL_NETCDF_FILE)
        save_geojson(geojson_output, OUTPUT_GEOJSON_FILE)
    
    print("\n--- Pipeline Complete ---")
    print("If successful, your map is ready to be loaded with real data.")