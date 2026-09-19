# Local Mock Gateway Testing & Setup Guide

This guide contains precise instructions on how to provision, configure, and execute integration tests against your local Flask-based API Gateway mock server (`mock_gateway.py`).

---

## 🛠️ 1. Environment Setup

### Native Host Configuration
If you choose to run the mock microservice directly on your local machine instead of Docker Compose:

1. **Initialize and Activate Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS / Linux
   # venv\Scripts\activate.bat  # Windows CMD
   ```

2. **Install Core Runtime Dependencies:**
   ```bash
   pip install flask requests
   ```

3. **Launch the Gateway Process:**
   ```bash
   python mock_gateway.py
   ```
   *The mock infrastructure will spin up and bind locally to `http://localhost:8080`.*

### Containerized Configuration
If utilizing the orchestrated Docker footprint:
```bash
docker compose up --build mock-api-gateway
```

---

## 📊 2. API Endpoint Specification

### Ingress Target
* **URL:** `http://localhost:8080/telemetry`
* **HTTP Method:** `POST`
* **Content-Type:** `application/json`

### Expected Request Payload
```json
{
  "employee_id": "EMP101",
  "cohort_id": "cohort-togaf-alpha",
  "submission_text": "Evaluating architecture verification models to prevent model bias and hallucinations."
}
```

---

## 🧪 3. Verification Test Suite

You can execute validation diagnostics against the proxy gateway using the automated test configurations detailed below.

### Option A: Terminal CLI Validation (`cURL`)

Execute a manual data injection test directly from your command shell to verify schema routing:

```bash
curl -X POST http://localhost:8080/telemetry \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "EMP101",
    "cohort_id": "cohort-togaf-alpha",
    "submission_text": "Routine audit loop verification to check for systemic validation anomalies."
  }'
```

#### Expected Valid Response Layer (200 OK):
```json
{
  "calculated_score": 88,
  "rag_context_retrieved": 3,
  "rolling_60_day_avg": 89.42,
  "status": "Processed"
}
```

### Option B: Automated Python Integration Test File (`test_mock_gateway.py`)

Create a local testing validation asset named `test_mock_gateway.py` to assert scoring rules programmatically:

```python
# test_mock_gateway.py
import requests

TARGET_URL = "http://localhost:8080/telemetry"

def test_skepticism_marker_logic():
    print("🧪 Running Test Case 1: High Score Rule Validation...")
    payload = {
        "employee_id": "EMP001",
        "cohort_id": "cohort-upskill-01",
        "submission_text": "Enforcing data integrity checking mechanisms to prevent AI hallucination."
    }
    response = requests.post(TARGET_URL, json=payload)
    data = response.json()
    
    assert response.status_code == 200, f"Expected HTTP 200, got {response.status_code}"
    assert data["calculated_score"] >= 80, f"Expected high score threshold, got {data['calculated_score']}"
    print("✅ Test Passed: High competency boundary verified successfully.")

def test_standard_submission_logic():
    print("\n🧪 Running Test Case 2: Standard Baseline Range Validation...")
    payload = {
        "employee_id": "EMP002",
        "cohort_id": "cohort-upskill-01",
        "submission_text": "Deploying standard cloud server resource arrays for standard compute loops."
    }
    response = requests.post(TARGET_URL, json=payload)
    data = response.json()
    
    assert response.status_code == 200
    assert 50 <= data["calculated_score"] <= 75, f"Expected standard score tracking range, got {data['calculated_score']}"
    print("✅ Test Passed: Standard baseline engine metrics verified successfully.")

if __name__ == '__main__':
    try:
        test_skepticism_marker_logic()
        test_standard_submission_logic()
        print("\n🎉 Integration verification complete: Mock gateway fully operational.")
    except AssertionError as error:
        print(f"\n❌ Verification Boundary Failed: {error}")
    except Exception as network_error:
        print(f"\n❌ Target Endpoint Unreachable: {network_error}")
```

Execute this automated test script inside your active virtual environment run state:
```bash
python test_mock_gateway.py
```