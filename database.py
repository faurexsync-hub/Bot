import json, os
from datetime import datetime

DATA_FILE  = "data.json"
STATS_FILE = "stats.json"
SCHED_FILE = "scheduled.json"

def _load(f, default):
    try:
        if os.path.exists(f):
            with open(f, encoding="utf-8") as fp:
                return json.load(fp)
    except:
        pass
    return default.copy()

def _save(f, obj):
    with open(f, "w", encoding="utf-8") as fp:
        json.dump(obj, fp, ensure_ascii=False, indent=2)

def get_data():
    return _load(DATA_FILE, {
        "replies": {},
        "default_reply": "Xabaringiz qabul qilindi! Tez orada javob beramiz.",
        "welcome": "Salom! Fuzzy botga xush kelibsiz!",
        "users": {}, "blocked": [],
        "spam_limit": 5, "spam_tracker": {},
        "active": True
    })

def save_data(d): _save(DATA_FILE, d)

def get_stats():
    return _load(STATS_FILE, {
        "total": 0, "today": 0,
        "date": str(datetime.now().date()),
        "counts": {}
    })

def save_stats(s): _save(STATS_FILE, s)

def get_sched(): return _load(SCHED_FILE, [])
def save_sched(p): _save(SCHED_FILE, p)
