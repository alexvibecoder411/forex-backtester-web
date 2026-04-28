"""
backend/services/analytics_service.py
Computes all performance stats from trade results.
"""

import pandas as pd


def compute_stats(trades: list[dict]) -> dict:
    if not trades:
        return {"overall": {}, "per_pair": {}, "per_provider": {}}

    df = pd.DataFrame(trades)

    overall = _stats(df, "Overall")

    per_pair = {}
    if "pair" in df.columns:
        for pair, g in df.groupby("pair"):
            per_pair[str(pair)] = _stats(g, str(pair))

    per_provider = {}
    if "provider" in df.columns:
        for prov, g in df.groupby("provider"):
            per_provider[str(prov)] = _stats(g, str(prov))

    return {"overall": overall, "per_pair": per_pair, "per_provider": per_provider}


def _stats(df: pd.DataFrame, label: str) -> dict:
    total   = len(df)
    wins    = int((df["outcome"] == "WIN").sum())
    losses  = int((df["outcome"] == "LOSS").sum())
    be      = int((df["outcome"] == "BREAKEVEN").sum())
    pending = int((df["outcome"] == "PENDING").sum())

    win_rate = round(wins / (wins + losses) * 100, 1) if (wins + losses) > 0 else 0.0

    pips_col  = df["pips"].fillna(0)
    total_pips = round(float(pips_col.sum()), 1)
    total_usd  = round(float(df["usd_pnl"].fillna(0).sum()), 2) if "usd_pnl" in df.columns else 0.0

    win_pips  = df[df["outcome"] == "WIN"]["pips"]
    loss_pips = df[df["outcome"] == "LOSS"]["pips"]
    avg_win   = round(float(win_pips.mean()),  1) if len(win_pips)  > 0 else 0.0
    avg_loss  = round(abs(float(loss_pips.mean())), 1) if len(loss_pips) > 0 else 0.0
    rr        = round(avg_win / avg_loss, 2) if avg_loss > 0 else 0.0

    gross_p = float(pips_col[pips_col > 0].sum())
    gross_l = abs(float(pips_col[pips_col < 0].sum()))
    pf      = round(gross_p / gross_l, 2) if gross_l > 0 else 0.0

    equity = pips_col.cumsum().tolist()
    max_dd, max_cl = _drawdown(equity, df["outcome"].tolist())

    return {
        "label":                   label,
        "total_trades":            total,
        "wins":                    wins,
        "losses":                  losses,
        "breakevens":              be,
        "pending":                 pending,
        "win_rate":                win_rate,
        "total_pips":              total_pips,
        "total_usd":               total_usd,
        "avg_win_pips":            avg_win,
        "avg_loss_pips":           avg_loss,
        "rr_ratio":                rr,
        "profit_factor":           pf,
        "max_drawdown_pips":       round(max_dd, 1),
        "max_consecutive_losses":  max_cl,
        "equity_curve":            [round(v, 1) for v in equity],
    }


def _drawdown(equity: list, outcomes: list) -> tuple[float, int]:
    peak  = equity[0] if equity else 0
    max_dd = 0.0
    for v in equity:
        if v > peak: peak = v
        dd = peak - v
        if dd > max_dd: max_dd = dd

    max_cl = cur_cl = 0
    for o in outcomes:
        if o == "LOSS": cur_cl += 1; max_cl = max(max_cl, cur_cl)
        else:           cur_cl = 0

    return max_dd, max_cl
