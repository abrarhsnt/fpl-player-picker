"""Download past seasons from vaastav/Fantasy-Premier-League and normalise to one row per player per gameweek."""
import numpy as np, pandas as pd
from .config import PAST_SEASONS, HIST_COLS

RAW = "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data"
POS = {"GK": 1, "GKP": 1, "DEF": 2, "MID": 3, "FWD": 4}
NUM = ["minutes", "bps", "ict_index", "expected_goal_involvements",
       "expected_goals_conceded", "total_points", "value"]


def load_season(season):
    m = pd.read_csv(f"{RAW}/{season}/gws/merged_gw.csv", low_memory=False)
    fx = pd.read_csv(f"{RAW}/{season}/fixtures.csv")[["id", "team_h_difficulty", "team_a_difficulty"]]
    m = m.merge(fx.rename(columns={"id": "fixture"}), on="fixture", how="left")
    home = m.was_home.astype(str).str.lower().eq("true")
    m["fix_diff"] = np.where(home, m.team_h_difficulty, m.team_a_difficulty)
    m["fix_home"] = home.astype(int)
    for c in NUM:
        m[c] = pd.to_numeric(m[c], errors="coerce") if c in m else np.nan
    g = m.groupby(["element", "GW"]).agg(
        pos=("position", "first"), price=("value", "last"), minutes=("minutes", "sum"),
        bps=("bps", "sum"), ict_index=("ict_index", "sum"),
        expected_goal_involvements=("expected_goal_involvements", "sum"),
        expected_goals_conceded=("expected_goals_conceded", "sum"),
        total_points=("total_points", "sum"), fix_diff=("fix_diff", "mean"),
        fix_home=("fix_home", "mean"), n_fix=("fix_home", "size")).reset_index()
    g["pos_id"] = g.pos.map(POS)
    g = g.dropna(subset=["pos_id"])
    g["price"] = g.price / 10
    g["season"] = season
    g["pid"] = season + "_" + g.element.astype(str)
    g = g.rename(columns={"GW": "gw"})
    return g[HIST_COLS]


def build(path="data/history_past.csv"):
    parts = []
    for s in PAST_SEASONS:
        try:
            d = load_season(s)
            print(f"{s}: {len(d):,} rows")
            parts.append(d)
        except Exception as e:
            print(f"{s}: skipped ({e})")
    out = pd.concat(parts, ignore_index=True)
    out.to_csv(path, index=False)
    print(f"saved {len(out):,} rows -> {path}")
