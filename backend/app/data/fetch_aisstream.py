import asyncio, websockets, ssl, certifi, json, os
from datetime import datetime, timezone
from dotenv import load_dotenv
import csv 
from pathlib import Path

load_dotenv()
AIS_URL = "wss://stream.aisstream.io/v0/stream"
AISSTREAM_API_KEY = os.getenv("AISSTREAM_API_KEY")

OUT_CSV = Path("data/raw/aisstream_live.csv") 
OUT_CSV.parent.mkdir(parents=True, exist_ok=True) 
CSV_FIELDS = [ "mmsi","ship_name","timestamp","lat","lon","sog","cog","nav_status","raw_json" ]

if not OUT_CSV.exists():
    with OUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()

def append_row_csv(record: dict):
    """
    Record must contain keys matching CSV_FIELDS.
    raw_json should be a JSON string of the full message for audit.
    """
    with OUT_CSV.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writerow(record)

BUFFER_SIZE = 100
buffer = []

def flush_buffer():
    if not buffer:
        return
    with OUT_CSV.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writerows(buffer)
    buffer.clear()


async def listen_aisstream():
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    while True:
        try:
            async with websockets.connect(AIS_URL, ssl=ssl_context) as ws:
                sub = {
                    "APIKey": AISSTREAM_API_KEY,  # official key name
                    "BoundingBoxes": [[[35, -75], [40, -70]]],
                    "FilterMessageTypes": ["PositionReport"]
                }

                await ws.send(json.dumps(sub))
                print("Connected to AISStream feed... (subscribed)")

                async for msg in ws:
                    data = json.loads(msg)
                    if data.get("MessageType") != "PositionReport":
                        continue

                    report = data["Message"]["PositionReport"]
                    record = {}
                    meta = data.get("MetaData", {})

                    record["mmsi"] = report.get("UserID")
                    record["lat"] = report.get("Latitude")
                    record["lon"] = report.get("Longitude")
                    record["sog"] = report.get("Sog")
                    record["cog"] = report.get("Cog")
                    record["ship_name"] = meta.get("ShipName", "Unknown")
                    record["timestamp"] = meta.get("time_utc", datetime.now(timezone.utc).isoformat())
                    record["nav_status"] = meta.get("NavStatus", "Unknown")
                    record["raw_json"] = msg

                    buffer.append(record)
                    if len(buffer) >= BUFFER_SIZE:
                        flush_buffer()

        except websockets.ConnectionClosed as e:
            print(f"Connection closed ({e.code}: {e.reason}), retrying in 10s...")
            await asyncio.sleep(10)
        except Exception as e:
            print("Error:", e)
            await asyncio.sleep(10)

asyncio.run(listen_aisstream())
