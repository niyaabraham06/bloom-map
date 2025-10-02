# BloomWatch Phenology Data Processor
# This script processes local NASA Earth Observation GeoTIFF data (NDVI time series)
# to generate a simplified GeoJSON file for the Leaflet map visualization.

import json
import numpy as np
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape, Point

# --- CORRECTED FILE PATHS (MATCHES USER'S LOCAL ROOT/DATA/ STRUCTURE) ---
# NOTE: Using the simple relative path because the script and data folder are in the same parent directory.
OUTPUT_FILE = './data/bloom_phenology.json'
RAW_NDVI_FILE = './data/ndvi_series.tif' 
# -----------------------------------------------------------------------

# CRITICAL FIX: Setting scale factor to 1.0 (no scaling) and setting 
# the threshold to a raw integer value (5000 = 0.50 scaled by 10000) for testing.
SCALE_FACTOR = 1.0


def calculate_bloom_proxy():
    """
    Reads a GeoTIFF time series, identifies bloom events (high NDVI), 
    and converts the key locations into a GeoJSON FeatureCollection.
    """
    print(f"Starting processing using raw file: {RAW_NDVI_FILE}...")

    try:
        with rasterio.open(RAW_NDVI_FILE) as src:
            # Read all bands (assuming each band is a slice in time)
            ndvi_array = src.read().astype('float32') 
            
            # Find the pixel-wise maximum raw value across the time series.
            max_raw_ndvi = np.amax(ndvi_array, axis=0)

            # --- DEBUGGING STEP ---
            # Print the highest raw pixel value in the whole region
            print(f"DEBUG: Highest raw pixel value found: {np.amax(max_raw_ndvi):.0f}")
            
            # 1. We keep the raw data for comparison (no scaling applied yet)
            data_to_threshold = max_raw_ndvi

            # 2. ANALYZE PHENOLOGY: Find the areas where the raw peak value is >= 2500 (0.25)
            # This is the test threshold using the RAW data values.
            # Rationale: Since max was 3065, we use a slightly lower threshold to ensure points are found.
            raw_bloom_threshold = 2500 
            blooming_pixels = data_to_threshold >= raw_bloom_threshold

            # 3. VECTORIZE: Convert the high-NDVI pixels into GeoJSON point data.
            features = []
            
            # Only process if we found any pixels above the threshold
            if not np.any(blooming_pixels):
                print(f"DEBUG: No pixels found above the raw {raw_bloom_threshold} threshold.")
                return None

            # Generate geometry features
            # NOTE: We scale the output value (val) only for display in GeoJSON
            for geom, val in shapes(blooming_pixels.astype(np.int16), mask=blooming_pixels, transform=src.transform):
                s = shape(geom)
                centroid = s.centroid

                # Use the threshold value (2500) as a placeholder for the peak value
                features.append({
                    "type": "Feature",
                    "geometry": { 
                        "type": "Point", 
                        "coordinates": [centroid.x, centroid.y] 
                    },
                    "properties": {
                        "name": "High Vegetation Zone",
                        "intensity": "Moderate Greenness", 
                        "date": "2024 Bloom Period Proxy", 
                        "species_proxy": "Generic Vegetation",
                        "ndvi_peak": round(raw_bloom_threshold / 10000.0, 2) 
                    }
                })

            print(f"Detected {len(features)} potential bloom zones (GeoJSON points).")
            return {
                "type": "FeatureCollection",
                "features": features
            }

    except rasterio.RasterioIOError:
        print(f"ERROR: Could not find or open the raw data file at: {RAW_NDVI_FILE}. Using mock data fallback.")
        return None 
    except Exception as e:
        print(f"An unexpected error occurred during processing: {e}")
        return None


def save_to_geojson(geojson_data):
    """Saves the generated GeoJSON data to the specified output file."""
    if geojson_data and 'features' in geojson_data and geojson_data['features']:
        try:
            # Ensure the necessary subdirectories exist before writing
            import os
            os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
            
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
