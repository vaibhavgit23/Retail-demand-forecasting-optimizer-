# Retail-demand-forecasting-optimizer-
An end-to-end machine learning project for retail demand forecasting and inventory optimization using time-series analysis, predictive modeling, and a Streamlit dashboard to support data-driven inventory decisions.
## Problem
Retailers lose money from stockouts (lost sales) and overstock (cash locked in unsold goods). This project forecasts weekly product demand with uncertainty ranges and recommends when and how much to reorder.

## Data
UCI Online Retail dataset: 541,909 transactions, 1 Dec 2010 to 9 Dec 2011, 4,070 products.

## Data cleaning
- Cancelled invoices moved to a separate returns table (demand = purchases only)
- Removed stock adjustments, non-product codes and duplicates
- Trimmed to 52 full weeks (6 Dec 2010 to 4 Dec 2011)
- Kept rows with missing CustomerID, since demand does not depend on customer identity
- Details and reasoning: `notebooks/02_cleaning.ipynb`

## Success metrics
- Forecast accuracy: MAE and WAPE versus naive and moving-average baselines
- Uncertainty quality: coverage of prediction intervals
- Business impact: reduction in stockouts and excess stock in a simulation
- Validation: time-based split, last 8-12 weeks held out

## Progress log
- Day 1: repo setup, data loaded, problem defined
- Day 2: cleaned data, separated returns, trimmed to 52 full weeks
- Day 3: built weekly demand table for the top 60 products; separated bulk orders (10% of units) from regular demand