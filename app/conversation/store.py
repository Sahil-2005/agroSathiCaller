# import json, os

# FILE = "data/calls.json"

# def save_answer(call_id, key, value):
#     os.makedirs("data", exist_ok=True)

#     if os.path.exists(FILE):
#         data = json.load(open(FILE))
#     else:
#         data = {}

#     data.setdefault(call_id, {})[key] = value
#     json.dump(data, open(FILE, "w"), indent=2)


import json
import os

FILE = "data/calls.json"

def save_answer(call_id, key, value):
    os.makedirs("data", exist_ok=True)

    data = {}

    # ✅ Safely load existing data
    if os.path.exists(FILE):
        try:
            with open(FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
        except json.JSONDecodeError:
            # File exists but is corrupted/empty
            data = {}

    # ✅ Ensure call entry exists
    if call_id not in data:
        data[call_id] = {}

    # ✅ Save answer
    data[call_id][key] = value

    # ✅ Write back safely
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
