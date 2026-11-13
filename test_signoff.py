import requests
import json
import sys

def test_signoff():
    url = "http://127.0.0.1:8000/api/doctor/sign-off/OPD-2026-K028"
    print(f"🚀 Sending POST request to: {url}")
    
    try:
        response = requests.post(url, timeout=10)
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS: Encounter Signed & Sealed successfully!")
            print(f"📦 Bundle ID: {data.get('bundle_id')}")
            print(f"🔐 Canonical Hash: {data.get('canonical_hash')}")
            print(f"🔑 Algorithm: {data.get('algorithm')}")
            print(f"🕒 Timestamp: {data.get('timestamp')}")
            print("\n--- FHIR R4 JSON BUNDLE ---")
            print(json.dumps(data.get("bundle", {}), indent=2, ensure_ascii=False))
        else:
            print(f"❌ FAILED with Status Code {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    test_signoff()
