# football_forecasts

Predictive models for football — probabilistic forecasts, honestly backtested. Where
[`football_metrics`](../football_metrics) measures *what happened*, these forecast *what will happen*.

Each forecaster is published as a **fully-baked demo notebook**: every figure and number is the output of a
real end-to-end run on StatsBomb open data, with an honest backtest and a limits section that says out loud
what a small sample cannot support. The pipelines behind them (event adapters, feature builders, trained
weights, simulators) power a live production deployment and are not distributed here.

| Sub-project | Forecasts | Notebook |
| :--- | :--- | :--- |
| [`champion_model/`](./champion_model) | Knockout-tournament champion, from the group stage only | [`champion_prediction.ipynb`](./champion_model/champion_prediction.ipynb) |

**Roadmap:** final-score prediction, next-goal momentum.
