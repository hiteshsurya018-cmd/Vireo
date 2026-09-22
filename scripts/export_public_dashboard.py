"""Write an aggregate-only snapshot for the public Vercel dashboard."""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "app"))
from data import load_tables, prepare
from insights import add_repeat, channel_sla_exposure, leaderboard, product_repeat_hotspots


def clean_number(value):
    return None if pd.isna(value) else round(float(value), 5)


def build_snapshot(data_dir):
    tables = load_tables(data_dir)
    t, _ = prepare(tables)
    t = add_repeat(t)
    as_of = t.created_dt.max()
    cutoff = as_of - pd.Timedelta(days=30)
    last_full = as_of.normalize() - pd.Timedelta(days=as_of.weekday() + 1)
    mature = t[t.completed & t.resolved_dt.le(cutoff)]

    category_repeats = (
        mature.groupby("category").repeat_30d
        .agg(completed="size", repeats="sum", rate="mean")
        .reset_index().sort_values("rate", ascending=False)
    )
    hotspots = product_repeat_hotspots(t, tables["products"], cutoff, 50)
    weeks = []
    for week in sorted(t.week_start.dropna().unique()):
        if week > last_full:
            continue
        w = t[t.week_start.eq(week)]
        prior = t[t.week_start.eq(week - pd.Timedelta(days=7))]
        eligible = w[w.completed & w.resolved_dt.le(cutoff)]
        full_repeat_window = len(eligible) == int(w.completed.sum()) and len(eligible) > 0
        cats = w.category.value_counts().to_dict()
        prev_cats = prior.category.value_counts().to_dict()
        changes = [
            {"category": name, "tickets": int(count), "change": int(count - prev_cats.get(name, 0))}
            for name, count in sorted(cats.items(), key=lambda x: x[1], reverse=True)
        ]
        channels = channel_sla_exposure(w)
        agents = leaderboard(t, week, "All").sort_values("tickets_closed", ascending=False).head(10)
        weeks.append({
            "week": week.strftime("%Y-%m-%d"),
            "tickets": int(len(w)),
            "completed": int(w.completed.sum()),
            "sla_breaches": int(w.breach.sum()),
            "sla_rate": clean_number(w.breach.mean()),
            "transfers": int((w.transfers > 0).sum()),
            "repeat_rate": clean_number(eligible.repeat_30d.mean()) if full_repeat_window else None,
            "categories": changes,
            "channels": [
                {"channel": r.channel, "tickets": int(r.tickets), "breaches": int(r.breaches),
                 "rate": clean_number(r.breach_rate), "potential_credit": int(r.potential_credit_inr)}
                for r in channels.itertuples()
            ],
            # Public view uses IDs rather than employee names.
            "agents": [
                {"agent": r.agent_id, "team": r.team, "closed": int(r.tickets_closed)}
                for r in agents.itertuples()
            ],
        })

    return {
        "meta": {
            "as_of": as_of.strftime("%Y-%m-%d"),
            "last_full_week": last_full.strftime("%Y-%m-%d"),
            "unique_tickets": int(len(t)),
            "duplicate_ids_removed": int(len(tables["tickets"]) - len(t)),
            "mature_completed": int(len(mature)),
            "mature_repeats": int(mature.repeat_30d.sum()),
            "repeat_rate": clean_number(mature.repeat_30d.mean()),
            "target_rate": 0.10,
            "quarterly_value_inr": round(650 * 13 * (float(mature.repeat_30d.mean()) - 0.10) * 290),
        },
        "category_repeats": [
            {"category": r.category, "completed": int(r.completed), "repeats": int(r.repeats),
             "rate": clean_number(r.rate)} for r in category_repeats.itertuples()
        ],
        "product_hotspots": [
            {"product": r.product, "sku": r.product_sku, "category": r.category,
             "completed": int(r.completed), "repeats": int(r.repeats),
             "rate": clean_number(r.repeat_rate), "excess": clean_number(r.excess_repeats_vs_target)}
            for r in hotspots.itertuples()
        ],
        "weeks": weeks,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/raw")
    parser.add_argument("--out", default="web/data.json")
    args = parser.parse_args()
    destination = Path(args.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    snapshot = build_snapshot(args.data_dir)
    destination.write_text(json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {destination} ({len(snapshot['weeks'])} full weeks; aggregate data only)")
