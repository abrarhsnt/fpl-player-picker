"""Run after every gameweek: refresh current-season data, retrain on all seasons, write predictions."""
import json, os, datetime
import pandas as pd
from fpl.data import fetch
from fpl.model import predict

if not os.path.exists("data/history_past.csv"):
    raise SystemExit("Run `python build_past.py` first (downloads past seasons once).")
past = pd.read_csv("data/history_past.csv")
cur, players, tfix, last_gw, next_gw = fetch("data")
if not next_gw:
    raise SystemExit("Season over or not started - nothing to predict.")
hist = pd.concat([past, cur], ignore_index=True)
preds, meta = predict(hist, players, tfix, last_gw, next_gw)
preds.to_csv("data/predictions.csv", index=False)
os.makedirs("data/pred_log", exist_ok=True)   # forecasts saved BEFORE games, for later accuracy tracking
preds[["player", "player_name", "pred"]].to_csv(f"data/pred_log/gw{next_gw}.csv", index=False)
meta.update(last_gw=int(last_gw), next_gw=int(next_gw),
            updated=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
json.dump(meta, open("data/meta.json", "w"))
print("Done:", meta)
