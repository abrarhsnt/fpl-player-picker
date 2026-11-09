CURRENT_SEASON = "2026-27"
# Past seasons come from the free vaastav/Fantasy-Premier-League dataset.
# At the start of a new season: add the finished season here, set CURRENT_SEASON,
# delete data/history_current.csv, rerun build_past.py then update.py.
PAST_SEASONS = ["2022-23", "2023-24", "2024-25", "2025-26"]
# Older seasons count less (scoring rules changed, e.g. defensive-contribution points in 2025-26).
SEASON_WEIGHT = {"2022-23": 0.4, "2023-24": 0.6, "2024-25": 0.8}
HIST_COLS = ["pid", "season", "gw", "pos_id", "price", "minutes", "bps", "ict_index",
             "expected_goal_involvements", "expected_goals_conceded", "total_points",
             "fix_diff", "fix_home", "n_fix"]
