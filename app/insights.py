
import re
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF

STOP_PHRASES={"vireo","hello","hi","hii","sir","madam","dear","team","please","kindly","thanks","thank","regards","order","product","issue","tried","expected"}

def repeat_flags(t):
    x=t[t.completed & t.resolved_dt.notna()].copy()
    # A later contact may still be open. Search all contacts after resolution.
    contacts=t.dropna(subset=["customer_id","category","product_sku","created_dt"])
    contacts=contacts.groupby(["customer_id","category","product_sku"])
    next_dates=[]
    for _,r in x.iterrows():
        key=(r.customer_id,r.category,r.product_sku)
        if key in contacts.groups:
            dates=contacts.get_group(key).created_dt
            later=dates[dates>r.resolved_dt]
            next_dates.append(later.min() if not later.empty else pd.NaT)
        else:
            next_dates.append(pd.NaT)
    x["next_created"]=next_dates
    x["repeat_30d"]=x.next_created.le(x.resolved_dt+pd.Timedelta(days=30))
    return x[["ticket_id","repeat_30d"]]

def add_repeat(t):
    rf=repeat_flags(t)
    out=t.copy()
    out["repeat_30d"]=False
    mp=rf.set_index("ticket_id")["repeat_30d"].to_dict()
    out["repeat_30d"]=out.ticket_id.map(mp).astype("boolean").fillna(False)
    return out

def weekly_summary(t):
    cutoff=t.created_dt.max()-pd.Timedelta(days=30)
    eligible=t.completed & t.resolved_dt.le(cutoff)
    t=t.copy()
    t["eligible_repeat"]=eligible
    t["mature_repeat"]=t.repeat_30d & eligible
    g=t.groupby("week_start").agg(
        tickets=("ticket_id","size"),
        completed=("completed","sum"),
        breach_rate=("breach","mean"),
        transfer_rate=("transfers",lambda x:(x>0).mean()),
        repeat_count=("mature_repeat","sum"),
        eligible_count=("eligible_repeat","sum")
    ).reset_index()
    g["repeat_rate"]=g.repeat_count/g.eligible_count.replace(0,np.nan)
    return g

def leaderboard(t, week=None, team=None):
    x=t[t.completed & (t.tier==1)].copy()
    if "closed_week_start" not in x.columns:
        x["closed_week_start"]=x.resolved_dt.dt.to_period("W-SUN").dt.start_time
    if week is not None: x=x[x.closed_week_start==pd.Timestamp(week)]
    if team and team!="All": x=x[x.team==team]
    return (x.groupby(["team","agent_id","name"])
             .size().reset_index(name="tickets_closed")
             .sort_values(["tickets_closed","agent_id"],ascending=[False,True]))

def _clean(s):
    s=re.sub(r"vr\d+"," ",str(s).lower())
    s=re.sub(r"\d+"," ",s)
    return re.sub(r"\s+"," ",s).strip()

def topic_digest(df, n_topics=6):
    docs=df.customer_message.fillna("").map(_clean)
    if len(docs)<20:
        return []
    vec=TfidfVectorizer(stop_words="english",ngram_range=(1,2),min_df=max(3,int(len(docs)*0.01)),
                        max_features=4000,sublinear_tf=True)
    X=vec.fit_transform(docs)
    if X.shape[1]==0: return []
    n_topics=min(n_topics,max(2,X.shape[0]//20))
    model=NMF(n_components=n_topics,random_state=42,init="nndsvda",max_iter=250)
    W=model.fit_transform(X)
    terms=vec.get_feature_names_out()
    result=[]
    for i,comp in enumerate(model.components_):
        inds=comp.argsort()[-7:][::-1]
        keywords=[terms[j] for j in inds if terms[j] not in STOP_PHRASES][:6]
        weights=W[:,i]
        result.append({"topic":i+1,"keywords":keywords,"volume":int((weights>0.10).sum()),
                       "share":float((weights>0.10).mean())})
    return sorted(result,key=lambda r:r["volume"],reverse=True)

def top_category_changes(t, week):
    w=pd.Timestamp(week)
    cur=t[t.week_start==w].category.value_counts()
    prev=t[t.week_start==w-pd.Timedelta(days=7)].category.value_counts()
    rows=[]
    for c in sorted(set(cur.index)|set(prev.index)):
        rows.append((c,int(cur.get(c,0)),int(prev.get(c,0)),int(cur.get(c,0)-prev.get(c,0))))
    return pd.DataFrame(rows,columns=["category","current","previous","change"]).sort_values("change",ascending=False)

def product_repeat_hotspots(t, products, cutoff, min_completed=50):
    mature=t[t.completed & t.resolved_dt.le(cutoff)].dropna(subset=["product_sku","category"])
    out=(mature.groupby(["product_sku","category"]).repeat_30d
         .agg(completed="size",repeats="sum",repeat_rate="mean")
         .reset_index())
    out=out[out.completed>=min_completed].copy()
    # Excess is an investigation aid relative to the stated 10% target.
    out["excess_repeats_vs_target"]=(out.repeats-out.completed*.10).clip(lower=0).round(1)
    names=products.set_index("sku").product_name
    out.insert(0,"product",out.product_sku.map(names).fillna(out.product_sku))
    return out.sort_values(["excess_repeats_vs_target","completed"],ascending=False).head(10)

def channel_sla_exposure(w):
    out=w.groupby("channel").breach.agg(tickets="size",breaches="sum",breach_rate="mean").reset_index()
    out["potential_credit_inr"]=out.breaches*350
    return out.sort_values("potential_credit_inr",ascending=False)

def qa_checks(t):
    checks=[]
    checks.append(("duplicate ticket_id after dedupe", int(t.ticket_id.duplicated().sum()), "0 expected"))
    checks.append(("missing created_at", int(t.created_dt.isna().sum()), "0 expected"))
    checks.append(("completed without resolved_at", int((t.completed & t.resolved_dt.isna()).sum()), "0 expected"))
    checks.append(("negative response minutes", int((t.response_min<0).sum()), "0 expected"))
    checks.append(("negative resolution minutes", int(((t.resolved_dt-t.created_dt).dt.total_seconds()<0).sum()), "0 expected"))
    checks.append(("missing agent ids", int(t.agent_id.isna().sum()), "0 expected"))
    return pd.DataFrame(checks,columns=["check","count","expectation"])
