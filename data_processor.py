import json
import numpy as np
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape

OUTPUT_FILE = './data/bloom_phenology.json'
RAW_NDVI_FILE = './data/ndvi_series.tif'
SCALE_FACTOR = 1.0

def calculate_bloom_proxy():
    print(f"Starting processing using raw file: {RAW_NDVI_FILE}...")

    try:
        with rasterio.open(RAW_NDVI_FILE) as src:
            ndvi_array = src.read().astype('float32') 
            max_raw_ndvi = np.amax(ndvi_array, axis=0)
            print(f"DEBUG: Highest raw pixel value found: {np.amax(max_raw_ndvi):.0f}")
            data_to_threshold = max_raw_ndvi
            raw_bloom_threshold = 2500 
            blooming_pixels = data_to_threshold >= raw_bloom_threshold

            features = []
            if not np.any(blooming_pixels):
                print(f"DEBUG: No pixels found above the raw {raw_bloom_threshold} threshold.")
                return None

            for geom, val in shapes(blooming_pixels.astype(np.int16), mask=blooming_pixels, transform=src.transform):
                s = shape(geom)
                centroid = s.centroid
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
    if geojson_data and 'features' in geojson_data and geojson_data['features']:
        try:
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
