# BloomWatch Phenology Data Processor
# This script processes local NASA Earth Observation GeoTIFF data (NDVI time series)
# to generate a simplified GeoJSON file for the Leaflet map visualization.

import json
import numpy as np
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape, Point
# NOTE: geopandas and fiona imports are often necessary for complex vector operations,
# but using rasterio.features.shapes() is often enough for simple GeoJSON output.
# If you run into errors, ensure you install geopandas/fiona in your environment.

# Define the output file path where the processed data will be saved
OUTPUT_FILE = './niyaabraham06/bloom-map/bloom-map-69692155a40f0e80eead89e14a3e3660f418b532/data/bloom_phenology.json'

# IMPORTANT: This path points to the GeoTIFF file you placed in the data folder.
# NOTE: I am adjusting the RAW_NDVI_FILE path to point relative to the nested folder
# where the file is actually located, assuming you run this from the parent directory.
RAW_NDVI_FILE = './niyaabraham06/bloom-map/bloom-map-69692155a40f0e80eead89e14a3e3660f418b532/data/ndvi_series.tif' 

# --- WARNING: MODIS NDVI data is often scaled (e.g., value 10000 = NDVI 1.0) ---
# Check the metadata of your GeoTIFF. For MODIS 16-day VI, values are typically scaled by 10000.
SCALE_FACTOR = 10000.0


def calculate_bloom_proxy():
    """
    Reads a GeoTIFF time series, identifies bloom events (high NDVI), 
    and converts the key locations into a GeoJSON FeatureCollection.
    """
    print(f"Starting processing using raw file: {RAW_NDVI_FILE}...")

    try:
        # Open the GeoTIFF file
        with rasterio.open(RAW_NDVI_FILE) as src:
            # Read all bands (assuming each band is a slice in time, e.g., weekly)
            ndvi_array = src.read().astype('float32') 
            profile = src.profile

            # 1. Scale the data to be between -1.0 and 1.0
            scaled_ndvi_array = ndvi_array / SCALE_FACTOR
            
            # 2. ANALYZE PHENOLOGY: Find the pixel-wise maximum NDVI value across the time series.
            max_ndvi = np.amax(scaled_ndvi_array, axis=0)
            
            # 3. DEFINE A THRESHOLD: Identify areas where the peak NDVI is very high (potential intense bloom)
            # 0.80 is a conservative threshold for intense, healthy vegetation/bloom.
            bloom_threshold = 0.80
            blooming_pixels = max_ndvi >= bloom_threshold

            # 4. VECTORIZE: Convert the high-NDVI pixels into GeoJSON point data.
            features = []
            
            # Use rasterio to iterate through the raster and extract geometry and value
            # The mask argument ensures we only look at pixels that passed the threshold.
            for geom, val in shapes(blooming_pixels.astype(np.int16), mask=blooming_pixels, transform=src.transform):
                # Calculate the centroid of the geometry (area of high bloom)
                s = shape(geom)
                centroid = s.centroid

                # Create a GeoJSON Feature
                features.append({
                    "type": "Feature",
                    "geometry": { 
                        "type": "Point", 
                        "coordinates": [centroid.x, centroid.y] 
                    },
                    "properties": {
                        "name": "High Bloom Zone",
                        "intensity": "Very High", 
                        "date": "2024 Bloom Period Peak", 
                        "species_proxy": "Generic Vegetation Bloom",
                        "ndvi_peak": round(val, 2)
                    }
                })

            print(f"Detected {len(features)} potential bloom zones (GeoJSON points).")
            
            # Return the final GeoJSON structure
            return {
                "type": "FeatureCollection",
                "features": features
            }

    except rasterio.RasterioIOError:
        print(f"ERROR: Could not find or open the raw data file at: {RAW_NDVI_FILE}. Using mock data fallback.")
        # --- START MOCK DATA RETURN (Fallback) ---
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": { "type": "Point", "coordinates": [-100.0, 40.0] },
                    "properties": {
                        "name": "Midwest Grassland Peak (Mock)",
                        "intensity": "High",
                        "date": "2025-05-15",
                        "species_proxy": "Grass/Cereal Crop Bloom",
                        "ndvi_peak": 0.85
                    }
                }
            ]
        }
        # --- END MOCK DATA RETURN (Fallback) ---
    except Exception as e:
        print(f"An unexpected error occurred during processing: {e}")
        return None


def save_to_geojson(geojson_data):
    """Saves the generated GeoJSON data to the specified output file."""
    if geojson_data and 'features' in geojson_data and geojson_data['features']:
        try:
            with open(OUTPUT_FILE, 'w') as f:
                json.dump(geojson_data, f, indent=4)
            print(f"Successfully saved bloom data to {OUTPUT_FILE}")
        except Exception as e:
            print(f"ERROR: Failed to save GeoJSON file: {e}")
    else:
        print("Data processing resulted in empty or invalid data. Skipping save.")

if __name__ == "__main__":
    processed_data = calculate_bloom_proxy()
    save_to_geojson(processed_data)
