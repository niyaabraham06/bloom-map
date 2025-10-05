from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

EARTHDATA_USERNAME = "irfans25"
EARTHDATA_PASSWORD = "Irfanmoh@123"
APPEEARS_API_BASE = "https://appeears.earthdatacloud.nasa.gov/api"

def get_token():
    """
    Logs in to AppEEARS, returns Bearer token. 
    """
    # Basic auth login
    login_url = f"{APPEEARS_API_BASE}/login"
    resp = requests.post(
        login_url,
        auth=(EARTHDATA_USERNAME, EARTHDATA_PASSWORD),
        data={"grant_type": "client_credentials"}
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Login failed: {resp.text}")
    j = resp.json()
    token = j.get("token")
    return token

@app.get("/api/ndvi")
async def api_ndvi(lat: float = Query(...), lon: float = Query(...)):
    # 1. Get token
    token = get_token()

    # 2. Create a point request task
    task_url = f"{APPEEARS_API_BASE}/task"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    # Build the JSON body
    body = {
        "taskType": "point", 
        "params": {
            "dates": [
                {"startDate": "2025-01-01", "endDate": "2025-12-31"}
            ],
            "layers": [
                {"product": "MOD13Q1.061", "bands": ["250m_16_days_NDVI"]}  # example product
            ],
            "geom": {
                "type": "Point",
                "coordinates": [lon, lat]
            }
        }
    }
    resp = requests.post(task_url, headers=headers, json=body)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    task = resp.json()
    task_id = task.get("task_id")

    # 3. Poll until task completes
    status_url = f"{APPEEARS_API_BASE}/task/{task_id}"
    for _ in range(20):
        st = requests.get(status_url, headers={"Authorization": f"Bearer {token}"})
        stj = st.json()
        status = stj.get("status")
        if status == "done":
            break
        time.sleep(3)
    else:
        raise HTTPException(status_code=500, detail="Task not completed in time")

    # 4. Get results (bundle)
    bundle_url = f"{APPEEARS_API_BASE}/bundle/{task_id}"
    bundle_resp = requests.get(bundle_url, headers={"Authorization": f"Bearer {token}"})
    if bundle_resp.status_code != 200:
        raise HTTPException(status_code=bundle_resp.status_code, detail=bundle_resp.text)
    bundle = bundle_resp.json()
    # find NDVI file in bundle, download or parse
    # For simplicity, assume a CSV exists with NDVI
    # This part you must inspect the bundle structure
    files = bundle.get("files", [])
    # pick first file with "ndvi" in name
    ndvi_file = None
    for f in files:
        if "NDVI" in f.get("file_name", ""):
            ndvi_file = f
            break
    if not ndvi_file:
        raise HTTPException(status_code=500, detail="No NDVI file in bundle")

    download_url = ndvi_file.get("url")
    file_resp = requests.get(download_url, headers={"Authorization": f"Bearer {token}"})
    if file_resp.status_code != 200:
        raise HTTPException(status_code=file_resp.status_code, detail="Failed download NDVI file")

    # parse CSV (example) to get NDVI value
    # Assume first data row has NDVI
    content = file_resp.text.splitlines()
    # skip header, take first data row
    if len(content) < 2:
        raise HTTPException(status_code=500, detail="Empty NDVI data")
    header = content[0].split(",")
    data = content[1].split(",")
    # find index of NDVI column
    idx = header.index("Value") if "Value" in header else 1
    ndvi_val = float(data[idx])

    return JSONResponse({"ndvi": ndvi_val, "date": data[0]})
