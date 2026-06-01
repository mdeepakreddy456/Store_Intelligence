import json
import time
import requests

API_URL = "http://localhost:8000/events/ingest"

with open("pipeline/output/events.jsonl", "r") as file:
    for line in file:
        event = json.loads(line)

        response = requests.post(
            API_URL,
            json=[event]
        )

        print(response.json())

        time.sleep(2)