import json
import requests

API_URL = "http://localhost:8000/events/ingest"
EVENTS_FILE = "pipeline/output/events.jsonl"


def ingest_events():
    batch = []

    with open(EVENTS_FILE, "r") as f:
        for line in f:
            event = json.loads(line.strip())
            batch.append(event)

            # send in batches of 500
            if len(batch) == 500:
                response = requests.post(API_URL, json=batch)
                print(response.json())
                batch = []

    # send remaining
    if batch:
        response = requests.post(API_URL, json=batch)
        print(response.json())

    print("Finished ingesting events!")


if __name__ == "__main__":
    ingest_events()