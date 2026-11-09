"""Predict points per player for the next gameweek (trained on past seasons + current season)."""
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from .config import CURRENT_SEASON, SEASON_WEIGHT

ROLL = ["total_points", "minutes", "bps", "ict_index",
        "expected_goal_involvements", "expected_goals_conceded"]
BASE = ["pos_id", "price", "fix_diff", "fix_home", "n_fix"]


def build_features(hist, players, tfix, next_gw):
    fut = players[["player", "team", "pos_id", "price"]].copy()
    fut["gw"] = next_gw
    fut = fut.merge(tfix, on=["team", "gw"], how="left")
    fut["n_fix"] = fut.n_fix.fillna(0)
    fut["season"] = CURRENT_SEASON
    fut["pid"] = CURRENT_SEASON + "_" + fut.player.astype(str)
    df = pd.concat([hist, fut[[c for c in hist.columns if c in fut.columns]]], ignore_index=True)
    df = df.sort_values(["pid", "gw"])
    g = df.groupby("pid")
    feats = list(BASE)
    for c in ROLL:
        for w in (3, 5):
            name = f"{c}_r{w}"
            df[name] = g[c].transform(lambda s: s.shift(1).rolling(w, min_periods=1).mean())
            feats.append(name)
    df["pts_season_avg"] = g["total_points"].transform(lambda s: s.shift(1).expanding().mean())
    feats.append("pts_season_avg")
    df["w"] = df.season.map(SEASON_WEIGHT).fillna(1.0)
    return df, feats


def _model():
    return HistGradientBoostingRegressor(max_iter=150, learning_rate=0.03, max_depth=3,
                                         min_samples_leaf=50, l2_regularization=1.0,
                                         random_state=42)


def _fit(d, feats):
    return _model().fit(d[feats], d.total_points, sample_weight=d.w)


def evaluate(train, feats, last_gw):
    """Backtest on the last 3 finished gameweeks of the current season."""
    cut = last_gw - 2
    is_val = (train.season == CURRENT_SEASON) & (train.gw >= cut)
    tr, va = train[~is_val], train[is_val].copy()
    m = _fit(tr, feats)
    va["p"] = m.predict(va[feats])
    va["b"] = va.total_points_r3.fillna(0)
    reg = va[va.minutes_r3 >= 60]
    err = lambda d, c: d[c] - d.total_points
    mae = lambda d, c: round(float(err(d, c).abs().mean()), 3)
    rmse = lambda d, c: round(float(np.sqrt((err(d, c) ** 2).mean())), 3)
    rc = lambda d, c: round(float(d[c].corr(d.total_points, method="spearman")), 3)
    return dict(mae=mae(va, "p"), baseline_mae=mae(va, "b"),
                rmse=rmse(va, "p"), baseline_rmse=rmse(va, "b"),
                mae_reg=mae(reg, "p"), baseline_mae_reg=mae(reg, "b"),
                rank_corr_reg=rc(reg, "p"), baseline_rank_corr_reg=rc(reg, "b"))


def predict(hist, players, tfix, last_gw, next_gw):
    df, feats = build_features(hist, players, tfix, next_gw)
    train = df[df.total_points.notna()]
    meta = evaluate(train, feats, last_gw) if last_gw >= 3 else {}
    model = _fit(train, feats)
    fut = df[(df.season == CURRENT_SEASON) & (df.gw == next_gw)].copy()
    sp = (df[(df.season == CURRENT_SEASON) & df.total_points.notna()]
          .groupby("pid").total_points.sum().rename("season_pts"))
    fut = fut.merge(sp, on="pid", how="left")
    fut["season_pts"] = fut.season_pts.fillna(0).astype(int)
    fut["player"] = fut.pid.str.split("_").str[1].astype(int)
    fut["pred"] = np.clip(model.predict(fut[feats]), 0, None)
    fut = fut.merge(players[["player", "player_name", "team_name", "team_short", "pos",
                             "chance_of_playing_next_round", "news"]], on="player")
    fut["pred"] = (fut.pred * fut.chance_of_playing_next_round.fillna(100) / 100).round(2)
    fut["form"] = fut.total_points_r3.round(2)
    fut["value"] = (fut.pred / fut.price).round(3)
    cols = ["player", "player_name", "team_name", "team_short", "pos", "price", "pred",
            "season_pts", "value", "form", "fix_diff", "fix_home", "n_fix",
            "chance_of_playing_next_round", "news"]
    return fut[cols].sort_values("pred", ascending=False), meta
