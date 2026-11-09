"""Current season from the official FPL API. Incremental: only new finished gameweeks are downloaded."""
import os, time, requests, pandas as pd
from .config import CURRENT_SEASON, HIST_COLS

BASE = "https://fantasy.premierleague.com/api"
HEADERS = {"User-Agent": "Mozilla/5.0"}
POS = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}
STAT_COLS = ["minutes", "bps", "ict_index", "expected_goal_involvements",
             "expected_goals_conceded", "total_points"]


def get(path):
    r = requests.get(f"{BASE}/{path}", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def fetch(data_dir="data"):
    b = get("bootstrap-static")
    teams = pd.DataFrame(b["teams"])[["id", "name", "short_name"]].rename(
        columns={"id": "team", "name": "team_name", "short_name": "team_short"})
    pl = pd.DataFrame(b["elements"])
    players = pl[["id", "web_name", "team", "element_type", "now_cost",
                  "chance_of_playing_next_round"]].rename(
        columns={"id": "player", "element_type": "pos_id"})
    players["price"] = players.now_cost / 10
    players["pos"] = players.pos_id.map(POS)
    players = players.merge(teams, on="team").drop(columns="now_cost")

    events = b["events"]
    finished = [e["id"] for e in events if e["finished"]]
    nxt = next((e["id"] for e in events if e.get("is_next")), None)

    fx = pd.DataFrame(get("fixtures")).dropna(subset=["event"])
    home = fx[["team_h", "event", "team_h_difficulty"]].rename(
        columns={"team_h": "team", "event": "gw", "team_h_difficulty": "fix_diff"})
    home["fix_home"] = 1
    away = fx[["team_a", "event", "team_a_difficulty"]].rename(
        columns={"team_a": "team", "event": "gw", "team_a_difficulty": "fix_diff"})
    away["fix_home"] = 0
    tfix = pd.concat([home, away]).groupby(["team", "gw"]).agg(
        n_fix=("fix_diff", "size"), fix_diff=("fix_diff", "mean"),
        fix_home=("fix_home", "mean")).reset_index()
    tfix["gw"] = tfix["gw"].astype(int)

    hp = os.path.join(data_dir, "history_current.csv")
    old = pd.read_csv(hp) if os.path.exists(hp) else pd.DataFrame(columns=HIST_COLS)
    done = set(old["gw"])
    rows = []
    for gw in [g for g in finished if g not in done]:
        for e in get(f"event/{gw}/live")["elements"]:
            s = {k: e["stats"].get(k) for k in STAT_COLS}
            s.update(player=e["id"], gw=gw)
            rows.append(s)
        print(f"fetched GW{gw}")
        time.sleep(0.3)
    hist = old
    if rows:
        new = pd.DataFrame(rows)
        for c in STAT_COLS:
            new[c] = pd.to_numeric(new[c], errors="coerce")
        new = new.merge(players[["player", "team", "pos_id", "price"]], on="player")
        new = new.merge(tfix, on=["team", "gw"])          # inner join drops blank gameweeks
        new["season"] = CURRENT_SEASON
        new["pid"] = CURRENT_SEASON + "_" + new.player.astype(str)
        hist = pd.concat([old, new[HIST_COLS]], ignore_index=True)

    os.makedirs(data_dir, exist_ok=True)
    hist.to_csv(hp, index=False)
    return hist, players, tfix, (max(finished) if finished else 0), nxt
