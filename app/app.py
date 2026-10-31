from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

DATA = Path(__file__).parent / "data"

st.set_page_config(page_title="Retail demand forecasting & inventory optimizer", layout="wide")


@st.cache_data
def load_data():
    weekly = pd.read_csv(DATA / "weekly.csv", parse_dates=["week"], dtype={"StockCode": str})
    next_week = pd.read_csv(DATA / "next_week.csv", dtype={"StockCode": str})
    sweep = pd.read_csv(DATA / "policy_sweep.csv")
    return weekly, next_week, sweep


weekly, next_week, sweep = load_data()
next_week_date = (weekly["week"].max() + pd.Timedelta(weeks=1)).date()

st.title("Retail demand forecasting & inventory optimizer")
st.caption(
    "UCI Online Retail data (Dec 2010 - Dec 2011), top 60 products by number of orders. "
    "Forecast = exponentially weighted average; ranges come from the product set's recent forecast errors."
)

# ---------- sidebar ----------
labels = (next_week["StockCode"] + " - " + next_week["description"].fillna("")).tolist()
choice = st.sidebar.selectbox("Product", labels)
code = next_week.loc[labels.index(choice), "StockCode"]
level = st.sidebar.selectbox(
    "Target service level (chance that demand is covered)",
    [50, 60, 70, 80, 90, 95, 98],
    index=4,
    format_func=lambda x: f"{x}%",
)
on_hand = st.sidebar.number_input("Units on hand now", min_value=0, value=0, step=10)

tab1, tab2, tab3 = st.tabs(["Product forecast", "Policy comparison", "About"])

# ---------- tab 1: product view ----------
with tab1:
    d = weekly[weekly["StockCode"] == code].sort_values("week")
    row = next_week[next_week["StockCode"] == code].iloc[0]
    st.subheader(f"{code} - {row['description']}")
    st.caption(
        f"Demand pattern in the last 12 weeks (for reporting only, computed after the fact): "
        f"{d['group'].iloc[0].replace('_', ' ')}"
    )

    s_level = float(row[f"s_{level}"])
    order_qty = max(s_level - on_hand, 0)
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Forecast, week of {next_week_date}", f"{row['forecast']:.0f} units")
    c2.metric(f"Order-up-to level ({level}% service)", f"{s_level:.0f} units")
    c3.metric("Suggested order now", f"{order_qty:.0f} units")

    fig, ax = plt.subplots(figsize=(10, 3.4))
    ax.plot(d["week"], d["actual"], marker="o", markersize=3, label="actual demand")
    ax.plot(d["week"], d["forecast"], linestyle="--", label="1-week-ahead forecast")
    t = d.dropna(subset=["lower"])
    ax.fill_between(t["week"], t["lower"], t["upper"], alpha=0.25, label="80% range (last 12 weeks)")
    ax.set_ylabel("units per week")
    ax.legend(loc="upper left")
    fig.autofmt_xdate()
    st.pyplot(fig)

    st.markdown("**Last 12 weeks: actual demand vs forecast range**")
    t = t.assign(inside_range=(t["actual"] >= t["lower"]) & (t["actual"] <= t["upper"]))
    show = t[["week", "actual", "forecast", "lower", "upper", "inside_range"]].copy()
    show["week"] = show["week"].dt.date
    st.dataframe(show.round(0), hide_index=True)

# ---------- tab 2: policy comparison ----------
with tab2:
    h = st.radio("Forecast horizon / lead time (weeks)", [1, 2], horizontal=True)
    s = sweep[sweep["horizon"] == h]
    fig, ax = plt.subplots(figsize=(10, 3.8))
    for name, g in s.groupby("policy"):
        ax.plot(g["stock_cover"], g["fill_rate"], marker="o", label=name)
    mark = s[(s["policy"] == "interval-based") & ((s["param"] - level / 100).abs() < 1e-6)]
    if len(mark):
        ax.scatter(mark["stock_cover"], mark["fill_rate"], s=220, facecolors="none", edgecolors="red",
                   label=f"selected: {level}%")
    ax.set_xlabel("stock held (weeks of demand)")
    ax.set_ylabel("share of demand served (fill rate)")
    ax.legend()
    ax.set_title("Backtest over the last 12 weeks, all 60 products")
    st.pyplot(fig)

    naive = s[s["policy"] == "naive (last week)"].iloc[0]
    iv = s[s["policy"] == "interval-based"].sort_values("stock_cover")
    matched = float(np.interp(naive["stock_cover"], iv["stock_cover"], iv["fill_rate"]))
    if len(mark):
        m = mark.iloc[0]
        st.info(
            f"Backtest over the last 12 weeks, all 60 products: at the {level}% level the model-based rule "
            f"served {m['fill_rate']:.1%} of demand holding {m['stock_cover']:.2f} weeks of stock. "
            f"Naive ordering (hold last week's demand) served {naive['fill_rate']:.1%} "
            f"holding {naive['stock_cover']:.2f} weeks. "
            f"At the same stock as naive, the model-based rule would have served about {matched:.1%}: "
            f"most of the gap above comes from holding more stock."
        )
    st.dataframe(s.drop(columns="horizon"), hide_index=True)

# ---------- tab 3: about ----------
with tab3:
    st.markdown(
        """
**What this does.** Forecasts weekly demand per product and turns the forecast into an order-up-to level.

**Method.** Weekly demand per product (bulk order lines capped); an exponentially weighted average as the point
forecast; a safety margin taken from the 8 most recent weeks of forecast errors; a weekly inventory simulation
over the last 12 weeks to compare ordering policies.

**What the backtest shows.**
- A pooled gradient-boosting model did not beat simple baselines on this one year of data.
- At the same service level, the interval-based rule needs about the same stock as a flat percentage buffer.
- Compared with naive ordering at the same stock, the forecast-based rule serves a few points more demand.

**Limitations.** One year of data and a test period containing the pre-Christmas peak; ramping products are
under-forecast; the simulation assumes lost sales, no ordering costs and orders arriving in time.
        """
    )