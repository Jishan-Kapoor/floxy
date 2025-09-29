from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
import statistics

# --- 1. FastAPI app initialization (Global Instance) ---
app = FastAPI()

# --- 2. FORCEFULLY ENABLE CORS MIDDLEWARE ---
# This must be the first thing applied to the app instance.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows ALL origins for the * Access-Control-Allow-Origin: * header
    allow_credentials=True,
    allow_methods=["POST", "GET"], # Allows POST and GET methods
    allow_headers=["*"],
)
# --- END CORS SETUP ---


# --- 3. Data Models ---
class Query(BaseModel):
    regions: List[str]
    threshold_ms: int

# --- 4. Telemetry Data (Pure Python Structure) ---
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

def parse_telemetry_data(csv_data):
    """Parses the CSV string into a dictionary of regions -> records."""
    data = {}
    lines = csv_data.strip().split('\n')[1:]
    for line in lines:
        parts = line.split(',')
        if len(parts) == 4:
            region = parts[1].lower()
            latency = int(parts[2])
            is_up = 1 if parts[3] == 'UP' else 0
            
            if region not in data:
                data[region] = []
            
            data[region].append({'latency': latency, 'is_up': is_up})
    return data

TELEMETRY_RECORDS = parse_telemetry_data(TELEMETRY_DATA_CSV)


def calculate_p95(data: List[int]) -> float:
    """Calculates the 95th percentile latency using pure Python."""
    if not data:
        return 0.0
    data_sorted = sorted(data)
    index = int(0.95 * len(data_sorted))
    if index >= len(data_sorted):
        index = len(data_sorted) - 1
    
    return float(data_sorted[index])


# --- 5. REQUIRED POST ENDPOINT: /app/latency ---
@app.post("/app/latency") 
async def get_deployment_metrics(query: Query) -> Dict[str, Any]:
    results = {}
    threshold = query.threshold_ms
    
    for region in query.regions:
        region_key = region.lower()
        records = TELEMETRY_RECORDS.get(region_key)

        if not records:
            results[region] = {"error": "Region not found in telemetry data."}
            continue

        latencies = [r['latency'] for r in records]
        uptimes = [r['is_up'] for r in records]

        # Calculate metrics
        avg_latency = round(statistics.mean(latencies), 2)
        p95_latency = round(calculate_p95(latencies), 2)
        avg_uptime = round(statistics.mean(uptimes), 4)
        breaches = sum(1 for latency in latencies if latency > threshold)

        results[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": int(breaches)
        }
        
    return results

# --- 6. Vercel Health Check Endpoint ---
@app.get("/")
def read_root():
    # This path is working, so the app is starting up correctly.
    return {"message": "eShopCo Metrics Service is Ready."}

