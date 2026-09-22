
import argparse, json
from pathlib import Path
import pandas as pd
import sys
sys.path.insert(0,str(Path(__file__).parents[1]/"app"))
from data import load_tables, prepare
from insights import (add_repeat, weekly_summary, leaderboard, topic_digest,
                      qa_checks, top_category_changes)

p=argparse.ArgumentParser()
p.add_argument("--data-dir",required=True)
p.add_argument("--out-dir",default="outputs")
args=p.parse_args()
out=Path(args.out_dir); out.mkdir(parents=True,exist_ok=True)
tables=load_tables(args.data_dir)
t,_=prepare(tables)
t=add_repeat(t)
ws=weekly_summary(t)
ws.to_csv(out/"weekly_metrics.csv",index=False)
latest=sorted(t.week_start.dropna().unique())[-1]
latest=max(x for x in t.week_start.dropna().unique() if x+pd.Timedelta(days=7)<=t.created_dt.max())
w=t[t.week_start==latest]
pd.DataFrame(topic_digest(w,6)).to_csv(out/"latest_themes.csv",index=False)
leaderboard(t,latest,"All").to_csv(out/"latest_agent_leaderboard.csv",index=False)
qa_checks(t).to_csv(out/"qa_checks.csv",index=False)
top_category_changes(t,latest).to_csv(out/"latest_category_changes.csv",index=False)
cutoff=t.created_dt.max()-pd.Timedelta(days=30)
eligible=t[t.completed & t.resolved_dt.le(cutoff)]
rate=float(eligible.repeat_30d.mean())
value=650*13*(rate-.10)*290
summary={
 "rows_after_migration_dedupe":int(len(t)),
 "unique_ticket_ids":int(t.ticket_id.nunique()),
 "completed_tickets":int(t.completed.sum()),
 "repeat_contact_rate":rate,
 "repeat_contact_n":int(eligible.repeat_30d.sum()),
 "repeat_eligible_n":int(len(eligible)),
 "sla_breach_rate":float(t.breach.mean()),
 "transfer_rate":float((t.transfers>0).mean()),
 "duplicate_ticket_ids_in_source":int((pd.read_csv(next(Path(args.data_dir).glob("*tickets.csv"))).ticket_id.duplicated()).sum()),
 "business_goal":f"Reduce 30-day repeat-contact proxy from {rate:.1%} to 10.0%, worth about Rs {value:,.0f} per quarter at 650 contacts/week and Rs 290/contact."
}
json.dump(summary,open(out/"run_summary.json","w"),indent=2)
print(json.dumps(summary,indent=2))
