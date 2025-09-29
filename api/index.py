from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
import io

# FastAPI app initialization
app = FastAPI()
# FastAPI app initialization
app = FastAPI()

# Enable CORS for all origins and POST/GET methods
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # THIS IS THE CRITICAL LINE
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# Enable CORS for all origins and POST/GET methods
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# Define the structure of the incoming request body
class Query(BaseModel):
    regions: list[str]
    threshold_ms: int

# --- Telemetry Data (Hardcoded) ---
TELEMETRY_DATA_CSV = """
timestamp,region,latency_ms,uptime_status
2025-01-01 08:00:00,us-east,150,UP
2025-01-01 08:00:05,emea,160,UP
2025-01-01 08:00:10,apac,185,UP
2025-01-01 08:00:15,us-west,140,UP
2025-01-01 08:00:20,emea,175,UP
2025-01-01 08:00:25,apac,165,UP
2025-01-01 08:00:30,us-east,155,UP
2025-01-01 08:00:35,emea,190,DOWN
2025-01-01 08:00:40,apac,150,UP
2025-01-01 08:00:45,us-west,145,UP
2025-01-01 08:00:50,emea,160,UP
2025-01-01 08:01:00,us-east,170,UP
"""

# --- ROBUST DATA LOADING BLOCK ---
try:
    df = pd.read_csv(io.StringIO(TELEMETRY_DATA_CSV))
    # Safer way to convert 'UP'/'DOWN' to numeric 1/0 using .astype(int)
    df['is_up'] = (df['uptime_status'] == 'UP').astype(int)
except Exception as e:
    # If loading fails, create a safe, empty DataFrame structure to avoid a total crash
    print(f"CRITICAL: Failed to load telemetry data. Error: {e}")
    df = pd.DataFrame(columns=['region', 'latency_ms', 'is_up'])
# --- END ROBUST DATA LOADING BLOCK ---


@app.post("/metrics")
async def get_deployment_metrics(query: Query):
    # This check now relies on the safe initialization above. 
    # If the loading failed, the DataFrame will be safe but empty,
    # and regions will simply not be found, which is a better error path.
    
    results = {}
    
    for region in query.regions:
        # Filter for the requested region (ensure region name is lowercase for matching)
        region_df = df[df['region'] == region.lower()]

        if region_df.empty:
            # Check for empty because the requested region might not be in the data
            results[region] = {"error": "Region not found in telemetry data or data failed to load."}
            continue

        # Calculate the required metrics:
        
        # 1. Average Latency (mean)
        avg_latency = round(region_df['latency_ms'].mean(), 2)
        
        # 2. 95th Percentile Latency (p95)
        # Using numpy.quantile ensures calculation even with few samples
        p95_latency = round(region_df['latency_ms'].quantile(0.95), 2)
        
        # 3. Average Uptime (mean of the is_up column)
        avg_uptime = round(region_df['is_up'].mean(), 4)
        
        # 4. Breaches (count where latency > threshold)
        breaches = (region_df['latency_ms'] > query.threshold_ms).sum()

        # Compile the result for the current region
        results[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": int(breaches)
        }
        
    return results

# Required root endpoint for Vercel deployment health checks
@app.get("/")
def read_root():
    return {"message": "eShopCo Metrics Service is Ready."}
