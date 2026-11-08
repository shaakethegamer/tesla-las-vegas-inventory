"""Tesla new Model 3 Premium inventory monitor. Fail closed on unknown data."""
import hashlib
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

STATE = Path("seen_vins.json")
TOPIC = os.environ.get("NTFY_TOPIC", "").strip()
ZIP = os.environ.get("TESLA_ZIP", "89109")
ENDPOINT = "https://www.tesla.com/inventory/api/v4/inventory-results"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TeslaInventoryWatch/1.0)", "Accept": "application/json"}

def fetch():
    query = {"query": {"model": "m3", "condition": "new", "options": {}, "arrangeby": "Price", "order": "asc", "market": "US", "language": "en", "super_region": "north america", "lng": -115.1398, "lat": 36.1699, "zip": ZIP, "range": 50}, "offset": 0, "count": 200, "outsideOffset": 0, "outsideSearch": False}
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": json.dumps(query, separators=(",", ":"))})
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=25) as response:
        data = json.load(response)
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        raise ValueError("Unexpected Tesla response; refusing to mark inventory as empty")
    return data["results"]

def eligible(car):
    if not isinstance(car, dict):
        return False
    vin = str(car.get("VIN") or car.get("vin") or "").strip().upper()
    if not re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", vin):
        return False
    raw = " ".join(str(car.get(k) or "") for k in ("Model", "model", "TrimName", "trimName", "Trim", "trim", "MarketingName", "marketingName", "Title", "title", "VehicleName", "vehicleName"))
    low = raw.lower()
    # Only explicit Premium trims qualify; unknown trims never trigger an alert.
    if "premium" not in low or "performance" in low or "standard" in low or "base" in low:
        return False
    if any(str(car.get(k, "")).lower() in ("used", "demo", "demonstrator") for k in ("Condition", "condition", "VehicleCondition", "vehicleCondition")):
        return False
    if car.get("IsDemo") is True or car.get("isDemo") is True:
        return False
    return True

def fingerprint(vin):
    return hashlib.sha256(vin.encode()).hexdigest()

def notify(car):
    vin = str(car.get("VIN") or car.get("vin"))
    name = next((str(car[k]) for k in ("TrimName", "trimName", "MarketingName", "marketingName") if car.get(k)), "Model 3 Premium")
    price = car.get("Price") or car.get("price") or car.get("TotalPrice") or "See listing"
    link = "https://www.tesla.com/m3/order/" + urllib.parse.quote(vin)
    message = f"New Tesla Model 3 Premium listing in Las Vegas\n{name}\nPrice: {price}\nVIN: {vin}\n{link}"
    payload = message.encode()
    req = urllib.request.Request("https://ntfy.sh/" + urllib.parse.quote(TOPIC, safe=""), data=payload, headers={"Title": "Tesla Model 3 Premium available", "Click": link, "Tags": "car", "Priority": "high"}, method="POST")
    with urllib.request.urlopen(req, timeout=20) as response:
        if response.status >= 300:
            raise RuntimeError(f"ntfy returned {response.status}")

def main():
    if not TOPIC:
        raise RuntimeError("Set NTFY_TOPIC in GitHub Actions secrets")
    cars = fetch()
    matches = {str(c.get("VIN") or c.get("vin")).upper(): c for c in cars if eligible(c)}
    print(f"Fetched {len(cars)} Tesla listings; {len(matches)} explicitly matched Premium trims")
    previous = set(json.loads(STATE.read_text())) if STATE.exists() else None
    current = {fingerprint(vin) for vin in matches}
    if previous is None:
        print("First run: establishing baseline; no notifications")
    else:
        for vin, car in matches.items():
            if fingerprint(vin) not in previous:
                notify(car)
                print("Notified new matching VIN ending " + vin[-5:])
    STATE.write_text(json.dumps(sorted(current), indent=2) + "\n")

if __name__ == "__main__":
    main()
