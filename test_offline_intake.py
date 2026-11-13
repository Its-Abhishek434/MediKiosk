import requests
import json
import sys



def test_offline_intake():
    url = "http://127.0.0.1:8000/api/intake/submit"
    payload = {
        "token": "OPD-2026-OFFLINE01",
        "abha_id": "test.offline@abdm",
        "name": "Devendra Mohan (Offline Test)",
        "age": 52,
        "gender": "Male",
        "language": "hi",
        "body_zone": "chest",
        "chief_complaint": "Mild tightness in chest with exertion",
        "socrates": {
            "site": "Retrosternal chest",
            "onset": "Gradual",
            "character": "Tightness",
            "severity": 5
        },
        "vitals": {
            "bp": "130/85 mmHg",
            "hr": "78 bpm",
            "spo2": "97%"
        }
    }
    
    print(f"🚀 Submitting Intake during Simulated Offline/Auth Drop to: {url}")
    print(f"📄 Payload Token: {payload['token']} (Severity: {payload['socrates']['severity']})")
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS: Intake accepted by L1 RAM Cache (PATIENT_STORE) fallback!")
            print(f"🎟️ Assigned Token: {data.get('token')}")
            print(f"🔢 Queue ID: {data.get('queue_id')}")
            print(f"🚦 Priority: {data.get('priority')}")
            print(f"📦 FHIR Bundle ID: {data.get('fhir_bundle_id')}")
            print(f"💬 Message: {data.get('message')}")
            print("\n--- COMPLETE RESPONSE JSON ---")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ FAILED with Status Code {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Request exception: {e}")

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    test_offline_intake()
