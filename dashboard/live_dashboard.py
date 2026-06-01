import time
import requests
from rich.console import Console
from rich.table import Table

console = Console()

STORE_ID = "STORE_BLR_002"

while True:
    try:
        response = requests.get(
            f"http://localhost:8000/stores/{STORE_ID}/metrics"
        )

        data = response.json()

        console.clear()

        table = Table(title="Store Intelligence Dashboard")

        table.add_column("Metric")
        table.add_column("Value")

        table.add_row(
            "Unique Visitors",
            str(data["unique_visitors"])
        )

        table.add_row(
            "Conversion Rate",
            str(data["conversion_rate"])
        )

        table.add_row(
            "Queue Depth",
            str(data["queue_depth"])
        )

        table.add_row(
            "Abandonment Rate",
            str(data["abandonment_rate"])
        )

        console.print(table)

    except Exception as e:
        console.print(f"Error: {e}")

    time.sleep(5)