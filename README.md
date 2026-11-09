# ⚽ FPL Player Picker

A free, auto-updating dashboard that predicts every Fantasy Premier League (FPL) player's points for the next gameweek, picks the best XI across all formations, and finds the best-value players to buy.

**🔗 Live app:** https://fpl-player-picker-gmyfzh65eiq26ukuujkheh.streamlit.app/

> Unofficial project. Not affiliated with or endorsed by the Premier League or Fantasy Premier League.

<!-- Add a screenshot of the app here, e.g. ![App screenshot](docs/screenshot.png) -->

## Features

- **Points prediction:** a machine-learning model forecasts each player's points for the upcoming gameweek.
- **Team of the Week:** tries 8 legal formations (3-4-3, 3-5-2, 4-4-2, 4-3-3, 4-5-1, 5-3-2, 5-4-1, 5-2-3), picks the highest-scoring XI, and marks the captain (doubled).
- **Best Value Buys:** ranks players by predicted points per £m, with an interactive chart. The y-axis can be switched between predicted points, total points this season, form, or points per £m, and hovering a dot shows the player.
- **Player Explorer:** filter by team, position, maximum price, minimum predicted points and availability. Shows fixture difficulty, home/away, number of fixtures, and FPL injury news.
- **Automatic updates:** data and predictions refresh daily through GitHub Actions, and the app redeploys on every update.
- **Model transparency:** the app shows a backtest of the model against a simple baseline.
- **Zero cost:** official FPL API, free GitHub, GitHub Actions and Streamlit Community Cloud.

## How it works

```
Official FPL API ──► current season data ─┐
                                          ├─► feature engineering ─► gradient boosting ─► predictions.csv ─► Streamlit app
vaastav dataset ───► 4 past seasons ──────┘                                                  ▲
                                                                          GitHub Actions (daily refresh + retrain)
```

1. **Data**
   - The current season is pulled from the official FPL API (one request per finished gameweek, downloaded incrementally).
   - Past seasons (2022-23 to 2025-26, about 110,000 player-gameweek rows) come from the community dataset [vaastav/Fantasy-Premier-League](https://github.com/vaastav/Fantasy-Premier-League).
   - All seasons are normalised to one row per player per gameweek, which handles double and blank gameweeks.
2. **Features** (computed only from information available before the gameweek, to avoid leakage)
   - Rolling 3- and 5-gameweek averages of points, minutes, BPS, ICT index, expected goal involvements and expected goals conceded
   - Season-to-date average points
   - Position, price, upcoming fixture difficulty (1-5), home/away, and number of fixtures in the gameweek
3. **Model**
   - `HistGradientBoostingRegressor` (scikit-learn), deliberately kept shallow and regularised because FPL points are noisy.
   - Older seasons are down-weighted, since scoring rules have changed over time.
   - Predictions are scaled by FPL's own chance-of-playing flag for injured or doubtful players.
4. **Evaluation**
   - Time-based backtest on the last 3 finished gameweeks, compared with a baseline of "average points over the player's last 3 games".
   - Metrics: MAE, RMSE, and Spearman rank correlation (how well the model orders players, which is what matters for picking a team).
   - In the early-season backtest (GW7-9 of 2026-27), adding past seasons lifted the rank correlation for regular players from about 0.01 to 0.20, against 0.06 for the baseline. This is a small sample, so treat it as indicative rather than conclusive.
5. **Team selection**
   - For each formation, takes the highest-predicted players per position and totals them. The best total wins, with the top scorer as captain.

## Tech stack

Python · pandas · NumPy · scikit-learn · Altair · Streamlit · GitHub Actions · Google Colab (development)

## Project structure

```
fpl-player-picker/
├── app.py                  # Streamlit dashboard
├── update.py               # refresh data, retrain, write predictions
├── build_past.py           # one-off: download past seasons
├── requirements.txt
├── fpl/
│   ├── config.py           # seasons, season weights, schema
│   ├── past.py             # past-season loader (vaastav dataset)
│   ├── data.py             # current-season loader (official FPL API)
│   ├── model.py            # features, training, backtest, prediction
│   └── team.py             # best XI across formations
├── data/
│   ├── history_past.csv    # past seasons (built once)
│   ├── history_current.csv # current season (grows each gameweek)
│   ├── predictions.csv     # latest predictions (read by the app)
│   ├── meta.json           # gameweek info and backtest metrics
│   └── pred_log/           # forecasts saved before each gameweek
└── .github/workflows/update.yml   # daily automatic refresh
```

## Run it locally

```bash
git clone https://github.com/abrarhsnt/fpl-player-picker.git
cd fpl-player-picker
pip install -r requirements.txt
python update.py          # fetch current season, train, write predictions
streamlit run app.py
```

Past seasons are already included in `data/history_past.csv`. To rebuild them, run `python build_past.py`.

## Deployment

- **Hosting:** Streamlit Community Cloud, connected to this repository (`app.py`).
- **Updates:** `.github/workflows/update.yml` runs `update.py` daily at 06:00 UTC and commits the refreshed `data/` folder. Streamlit redeploys automatically.

## New season checklist

1. Add the finished season to `PAST_SEASONS` in `fpl/config.py` and set `CURRENT_SEASON`.
2. Delete `data/history_current.csv`.
3. Run `python build_past.py`, then `python update.py`.

## Limitations

- FPL points are very noisy (goals, cards and rotation), so even good models have modest accuracy. Always combine the predictions with your own judgement and the latest team news.
- The best XI ignores budget and the 3-players-per-club rule, so it is a "dream team", not a transfer plan.
- Each season's player IDs are separate, so players start a new season without carried-over form.
- Price history is approximate for the current season (the current price is used).

## Roadmap

- Budget-aware squad and transfer optimiser (linear programming)
- Separate "will he play" and "points if he plays" models
- Opponent attack and defence strength features
- Accuracy-tracking page built from the saved prediction logs
- Automatic bias correction and model selection

## Data sources and credits

- Official [Fantasy Premier League API](https://fantasy.premierleague.com/api/bootstrap-static/)
- [vaastav/Fantasy-Premier-League](https://github.com/vaastav/Fantasy-Premier-League) for historical season data

## Author

**Md Abrar Hasnat**: [GitHub](https://github.com/abrarhsnt)
