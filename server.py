from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import random
import os

app = FastAPI()

# Allow your frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint to serve GeoJSON
@app.get("/geojson")
async def get_geojson():
    # Example: generate random bloom points
    features = []
    for _ in range(10):
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    round(random.uniform(75.0, 75.1), 6),
                    round(random.uniform(9.9, 10.0), 6)
                ]
            },
            "properties": {
                "name": "High Vegetation Zone",
                "intensity": "Moderate Greenness",
                "date": "2024 Bloom Period Proxy",
                "species_proxy": "Generic Vegetation",
                "ndvi_peak": round(random.uniform(0.2, 0.4), 2)
            }
        })

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    return geojson

# Endpoint to serve index.html
@app.get("/")
async def root():
    file_path = os.path.join(os.path.dirname(__file__), "index.html")
    return FileResponse(file_path)
