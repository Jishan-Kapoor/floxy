import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add the parent directory to the sys.path to allow for absolute imports
# This is a robust way to handle imports in a testing context, especially for Vercel
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.index import app

# --- Test Client Initialization ---
# This client allows us to send requests to the FastAPI app without running a live server.
client = TestClient(app)

# --- Test Case for the /app/latency Endpoint ---
def test_get_deployment_metrics_success():
    """
    Tests the /app/latency endpoint with a valid request.
    It verifies that the API returns a 200 OK status and that the response body
    is structured as expected with correct calculations for a known region.
    """
    # 1. Define the request payload
    # This simulates a client asking for metrics for the 'us-east' region with a 200ms threshold.
    payload = {
        "regions": ["us-east"],
        "threshold_ms": 200
    }

    # 2. Send a POST request to the endpoint
    response = client.post("/app/latency", json=payload)

    # 3. Assert the response status code is 200 (OK)
    assert response.status_code == 200

    # 4. Parse the JSON response
    data = response.json()

    # 5. Validate the structure and content of the response
    # Checks if the primary key 'us-east' is in the response.
    assert "us-east" in data

    # Retrieves the metrics for the 'us-east' region.
    metrics = data["us-east"]

    # Verifies that all expected metric keys are present.
    expected_keys = ["avg_latency", "p95_latency", "avg_uptime", "breaches"]
    for key in expected_keys:
        assert key in metrics

    # Validates the calculated values against expected results.
    # These values are pre-calculated from the static CSV data for 'us-east'.
    assert metrics["avg_latency"] == 158.33
    assert metrics["p95_latency"] == 170.0
    assert metrics["avg_uptime"] == 1.0
    assert metrics["breaches"] == 0

# --- Test Case for a Non-Existent Region ---
def test_get_deployment_metrics_region_not_found():
    """
    Tests the API's response when a requested region does not exist in the telemetry data.
    The API should return a 200 OK status but include an error message for the specific region.
    """
    # 1. Define a payload with a region that is not in the dataset
    payload = {
        "regions": ["antarctica"],
        "threshold_ms": 100
    }

    # 2. Send the request
    response = client.post("/app/latency", json=payload)

    # 3. Assert the status code is still 200
    assert response.status_code == 200

    # 4. Parse the response
    data = response.json()

    # 5. Check for the 'antarctica' key and the nested error message
    assert "antarctica" in data
    assert "error" in data["antarctica"]
    assert data["antarctica"]["error"] == "Region not found in telemetry data."

# --- Test Case for the Root Health Check Endpoint ---
def test_read_root():
    """
    Tests the root endpoint (GET /) to ensure it's responsive.
    This is a basic health check to confirm the service is running.
    """
    # 1. Send a GET request to the root path
    response = client.get("/")

    # 2. Assert the status is 200 OK
    assert response.status_code == 200

    # 3. Verify the health check message
    assert response.json() == {"message": "eShopCo Metrics Service is Ready."}