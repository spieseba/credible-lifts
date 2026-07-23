from pathlib import Path
import requests

url = "https://iwf.sport/results/results-by-events/"
resp = requests.get(url, params={"event_id": 673}, timeout=30)
resp.raise_for_status() # crash loudly on 4xx/5xx

file = Path(__file__).parents[2] / "data" / "raw" / "event_673.html"

file.write_text(resp.text, encoding="utf-8")
print("saved", len(resp.text), "characters")
print(file)

