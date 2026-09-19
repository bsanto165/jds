# mock_gateway.py
import json
import random
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/telemetry', methods=['POST'])
def mock_telemetry_ingress():
    try:
        # Intercept payload data loop
        body = request.get_json(force=True)
        employee_id = body.get('employee_id', 'UNKNOWN')
        cohort_id = body.get('cohort_id', 'UNKNOWN')
        submission_text = body.get('submission_text', '')

        # Basic keyword evaluation check mirroring your Lambda engine logic
        has_skepticism_marker = any(k in submission_text.lower() for k in ["verify", "audit", "hallucination", "bias"])
        
        # Calculate mock score logic
        calculated_score = random.randint(80, 98) if has_skepticism_marker else random.randint(50, 75)
        
        # Dynamic mock trend simulation
        rolling_avg = calculated_score + random.uniform(-3, 3)
        rolling_avg = max(0.0, min(100.0, rolling_avg))

        print(f"📥 [Mock GW] Received telemetry for {employee_id} ({cohort_id})")

        return jsonify({
            'status': 'Processed',
            'calculated_score': calculated_score,
            'rolling_60_day_avg': round(rolling_avg, 2),
            'rag_context_retrieved': random.randint(1, 4)
        }), 200

    except Exception as e:
        print(f"❌ [Mock GW] Parsing Error: {str(e)}")
        return jsonify({'error': 'Malformed request body'}), 400

if __name__ == '__main__':
    # Listen on port 8080 to match docker network maps
    app.run(host='0.0.0.0', port=8080)
