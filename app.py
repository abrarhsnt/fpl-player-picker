import json
import altair as alt
import pandas as pd
import streamlit as st
from fpl.team import best_xi

st.set_page_config(page_title="FPL Player Picker", page_icon="⚽", layout="wide")


@st.cache_data(ttl=1800)
def load():
    p = pd.read_csv("data/predictions.csv")
    p["news"] = p["news"].fillna("")

    def venue(x):
        if pd.isna(x): return "No fixture"
        return "Home" if x == 1 else "Away" if x == 0 else "Home & Away"

    def avail(c):
        return "Fit" if pd.isna(c) or c == 100 else f"{int(c)}% chance"

    p["venue"] = p.fix_home.map(venue)
    p["availability"] = p.chance_of_playing_next_round.map(avail)
    return p, json.load(open("data/meta.json"))


p, meta = load()
NAMES = {"player_name": "Player", "team_name": "Team", "pos": "Pos", "price": "Price (£m)",
         "pred": "Predicted pts", "season_pts": "Season pts", "value": "Pts per £m",
         "form": "Form (avg last 3 GWs)", "fix_diff": "Difficulty (1-5)", "n_fix": "Fixtures",
         "venue": "Venue", "availability": "Availability", "news": "News"}


def show(df, cols, **kw):
    st.dataframe(df[cols].rename(columns=NAMES), hide_index=True, width="stretch", **kw)


st.title("⚽ FPL Player Picker")
st.caption(f"Predictions for GW{meta['next_gw']} · data through GW{meta['last_gw']} · updated {meta['updated']} · unofficial, not affiliated with the Premier League")
if meta.get("rank_corr_reg") is not None:
    with st.expander("Model accuracy (backtest on last 3 gameweeks)"):
        st.write(f"Rank correlation (regular players): **{meta['rank_corr_reg']}** vs baseline {meta['baseline_rank_corr_reg']}")
        st.write(f"MAE (regular players): **{meta['mae_reg']}** vs baseline {meta['baseline_mae_reg']} · RMSE: **{meta['rmse']}** vs {meta['baseline_rmse']}")
        st.caption("Baseline = average points of the player's last 3 games. Rank correlation: 1 = perfect ordering, 0 = random.")
with st.expander("What do the columns mean?"):
    st.markdown("""
- **Predicted pts**: model's expected points for the next gameweek (already reduced for injury doubts).
- **Difficulty (1-5)**: FPL's rating of the opponent for that gameweek: 1 = easiest, 5 = hardest. Averaged in a double gameweek.
- **Fixtures**: number of matches in the gameweek (0 = blank, 2 = double).
- **Venue**: Home or Away for that gameweek.
- **Availability**: FPL's injury/suspension flag. *Fit* = no concern flagged; otherwise FPL's chance of playing (0%, 25%, 50%, 75%). The model scales its prediction by it. See *News* for the reason.
- **Pts per £m**: predicted points divided by price.
""")

with st.sidebar:
    st.header("Filters")
    teams = st.multiselect("Team", sorted(p.team_name.unique()))
    pos = st.multiselect("Position", ["GKP", "DEF", "MID", "FWD"])
    max_price = st.slider("Price under (£m)", 3.5, float(p.price.max()), float(p.price.max()), 0.1)
    min_pred = st.slider("Min predicted points", 0.0, float(p.pred.max()), 0.0, 0.5)
    fit_only = st.checkbox("Only fully fit players")

f = p[(p.price <= max_price) & (p.pred >= min_pred)]
if teams: f = f[f.team_name.isin(teams)]
if pos: f = f[f.pos.isin(pos)]
if fit_only: f = f[f.availability == "Fit"]

t1, t2, t3 = st.tabs(["🏆 Team of the Week", "💰 Best Value Buys", "🔎 Player Explorer"])

with t1:
    formation, total, xi, all_f = best_xi(p)
    cap = xi.pred.idxmax()
    c1, c2, c3 = st.columns(3)
    c1.metric("Best formation", formation)
    c2.metric("Predicted total (captain doubled)", total)
    c3.metric("Squad cost", f"£{xi.price.sum():.1f}m")
    xi = xi.assign(o=xi.pos.map({"GKP": 0, "DEF": 1, "MID": 2, "FWD": 3})).sort_values(["o", "pred"], ascending=[True, False])
    xi["player_name"] = [n + " (C)" if i == cap else n for i, n in zip(xi.index, xi.player_name)]
    show(xi, ["pos", "player_name", "team_name", "price", "pred", "fix_diff", "venue", "availability"])
    st.caption("Best XI ignores budget and the 3-players-per-club rule. Totals by formation:")
    st.bar_chart(pd.Series(all_f, name="Total predicted pts").sort_values(ascending=False))

with t2:
    st.caption("Predicted points per £m, using the sidebar filters. Raise 'Min predicted points' to skip bench players.")
    v = f[f.pred > 0].sort_values("value", ascending=False).head(20)
    show(v, ["player_name", "team_name", "pos", "price", "pred", "value", "season_pts", "form", "availability"])
    YOPTS = {"Predicted points (next GW)": "pred", "Total points this season": "season_pts",
             "Form (avg last 3 GWs)": "form", "Points per £m": "value"}
    ylabel = st.selectbox("Chart Y axis", list(YOPTS))
    ycol = YOPTS[ylabel]
    chart = alt.Chart(f).mark_circle(size=80, opacity=0.8).encode(
        x=alt.X("price:Q", title="Price (£m)", scale=alt.Scale(zero=False)),
        y=alt.Y(f"{ycol}:Q", title=ylabel),
        color=alt.Color("pos:N", title="Position"),
        tooltip=[alt.Tooltip("player_name:N", title="Player"), alt.Tooltip("team_name:N", title="Team"),
                 alt.Tooltip("pos:N", title="Pos"), alt.Tooltip("price:Q", title="Price (£m)"),
                 alt.Tooltip("pred:Q", title="Predicted pts"), alt.Tooltip("season_pts:Q", title="Season pts"),
                 alt.Tooltip("form:Q", title="Form")]).interactive()
    st.altair_chart(chart, width="stretch")
    st.caption("Hover (or tap) a dot to see the player.")

with t3:
    show(f.sort_values("pred", ascending=False),
         ["player_name", "team_name", "pos", "price", "pred", "season_pts", "value", "form",
          "fix_diff", "n_fix", "venue", "availability", "news"])
