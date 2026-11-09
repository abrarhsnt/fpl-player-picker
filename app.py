import json
import pandas as pd
import streamlit as st
from fpl.team import best_xi

st.set_page_config(page_title="FPL Player Picker", page_icon="⚽", layout="wide")


@st.cache_data(ttl=1800)
def load():
    return pd.read_csv("data/predictions.csv"), json.load(open("data/meta.json"))


p, meta = load()
st.title("⚽ FPL Player Picker")
st.caption(f"Predictions for GW{meta['next_gw']} · data through GW{meta['last_gw']} · updated {meta['updated']} · unofficial, not affiliated with the Premier League")
if meta.get("rank_corr_reg") is not None:
    with st.expander("Model accuracy (backtest on last 3 gameweeks)"):
        st.write(f"Rank correlation (regular players): **{meta['rank_corr_reg']}** vs baseline {meta['baseline_rank_corr_reg']}")
        st.write(f"MAE (regular players): **{meta['mae_reg']}** vs baseline {meta['baseline_mae_reg']} · RMSE: **{meta['rmse']}** vs {meta['baseline_rmse']}")
        st.caption("Baseline = average points of the player's last 3 games.")

with st.sidebar:
    st.header("Filters")
    teams = st.multiselect("Team", sorted(p.team_name.unique()))
    pos = st.multiselect("Position", ["GKP", "DEF", "MID", "FWD"])
    max_price = st.slider("Price under (£m)", 3.5, float(p.price.max()), float(p.price.max()), 0.1)
    min_pred = st.slider("Min predicted points", 0.0, float(p.pred.max()), 0.0, 0.5)
    fit_only = st.checkbox("Only fully fit players (no injury flag)")

f = p[(p.price <= max_price) & (p.pred >= min_pred)]
if teams: f = f[f.team_name.isin(teams)]
if pos: f = f[f.pos.isin(pos)]
if fit_only: f = f[f.chance_of_playing_next_round.isna() | (f.chance_of_playing_next_round == 100)]

t1, t2, t3 = st.tabs(["🏆 Team of the Week", "💰 Best Value Buys", "🔎 Player Explorer"])

with t1:
    formation, total, xi, all_f = best_xi(p)
    cap = xi.loc[xi.pred.idxmax(), "web_name"]
    st.subheader(f"Best formation: {formation} — {total} predicted pts (captain {cap} doubled)")
    for position in ["FWD", "MID", "DEF", "GKP"]:
        row = xi[xi.pos == position]
        cols = st.columns(max(len(row), 1))
        for c, (_, r) in zip(cols, row.iterrows()):
            c.metric(f"{r.web_name} ({r.team_short})", f"{r.pred}", f"£{r.price}m", delta_color="off")
    st.bar_chart(pd.Series(all_f, name="Total predicted pts"))

with t2:
    st.caption("Predicted points per £m, using the sidebar filters. Raise 'Min predicted points' to skip bench players.")
    v = f[f.pred > 0].sort_values("value", ascending=False).head(20)
    st.dataframe(v[["web_name", "team_short", "pos", "price", "pred", "value", "form"]], hide_index=True, use_container_width=True)
    st.scatter_chart(f, x="price", y="pred", color="pos")

with t3:
    st.dataframe(f.drop(columns=["player", "team_short"]), hide_index=True, use_container_width=True)
