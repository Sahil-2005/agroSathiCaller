import json, os

FILE = "data/calls.json"

def save_answer(call_id, key, value):
    os.makedirs("data", exist_ok=True)

    if os.path.exists(FILE):
        data = json.load(open(FILE))
    else:
        data = {}

    data.setdefault(call_id, {})[key] = value
    json.dump(data, open(FILE, "w"), indent=2)
