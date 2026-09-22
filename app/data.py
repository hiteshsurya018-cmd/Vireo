
from pathlib import Path
import pandas as pd

EXPECTED = {
    "tickets": "tickets.csv",
    "agents": "agents.csv",
    "customers": "customers.csv",
    "orders": "orders.csv",
    "products": "products.csv",
}

def _find(data_dir, stem):
    p=Path(data_dir)
    exact=p/(stem+".csv")
    if exact.exists(): return exact
    matches=list(p.rglob(f"*{stem}.csv"))
    if not matches:
        raise FileNotFoundError(f"Could not find {stem}.csv under {data_dir}")
    return matches[0]

def load_tables(data_dir):
    return {k:pd.read_csv(_find(data_dir,k)) for k in EXPECTED}

def prepare(tables):
    t=tables["tickets"].copy()
    # Migration note: the same ticket_id can appear once in each source system.
    # Keep the current-helpdesk row when present; otherwise keep the only row.
    t["_source_rank"]=t["source_system"].map({"legacy_fd":0,"helpdesk":1}).fillna(-1)
    t=t.sort_values(["ticket_id","_source_rank"]).drop_duplicates("ticket_id",keep="last").copy()
    t["created_dt"]=pd.to_datetime(t["created_at"],errors="coerce")
    t["first_dt"]=pd.to_datetime(t["first_response_at"],errors="coerce")
    t["resolved_dt"]=pd.to_datetime(t["resolved_at"],errors="coerce")
    # Policy 3.2 §9: migrated resolution events are UTC; the report uses IST.
    t.loc[t.source_system.eq("legacy_fd"),"resolved_dt"] += pd.Timedelta(hours=5,minutes=30)
    t["completed"]=t["status"].isin(["resolved","closed"])
    targets={"chat":15,"email":480,"voice":120,"social":240}
    t["response_min"]=(t["first_dt"]-t["created_dt"]).dt.total_seconds()/60
    t["breach"]=t.apply(lambda r: bool(pd.notna(r.response_min) and r.response_min>targets.get(r["channel"],10**9)),axis=1)
    t["week_start"]=t["created_dt"].dt.to_period("W-SUN").apply(lambda x:x.start_time)
    t["closed_week_start"]=t["resolved_dt"].dt.to_period("W-SUN").apply(lambda x:x.start_time if pd.notna(x) else pd.NaT)
    t["month"]=t["created_dt"].dt.to_period("M").astype(str)

    a=tables["agents"].copy()
    a["from"]=pd.to_datetime(a["from_date"],errors="coerce")
    a["to"]=pd.to_datetime(a["to_date"],errors="coerce").fillna(pd.Timestamp("2099-12-31"))
    # Resolve roster row by ticket creation date. Fall back to agent_id if the export has no matching date row.
    roster_cols=["name","team","shift","tier","site"]
    records=[]
    for _,r in t.iterrows():
        cand=a[(a.agent_id==r.agent_id)&(a["from"]<=r.created_dt)&(a["to"]>=r.created_dt)]
        if cand.empty: cand=a[a.agent_id==r.agent_id]
        records.append(cand.iloc[0][roster_cols].to_dict() if not cand.empty else {c:None for c in roster_cols})
    roster=pd.DataFrame(records,index=t.index)
    for c in roster_cols: t[c]=roster[c]
    return t, tables
