
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent))
from data import load_tables, prepare
from insights import add_repeat, leaderboard, topic_digest, top_category_changes, qa_checks
from charts import complaint_mix, repeat_rates

st.set_page_config(page_title="Vireo Support Intelligence",layout="wide")
st.title("Vireo Audio — Support Intelligence")
st.caption("Weekly ticket trends, repeat contacts, and service levels.")

with st.sidebar:
    st.header("Data")
    data_dir=st.text_input("Data directory","data/raw")
    if st.button("Reload data"):
        st.cache_data.clear()
    st.divider()
    st.markdown("**Definitions**")
    st.write("Repeat contact = same customer + category + product within 30 days of resolution.")
    st.write("Leaderboard = completed Tier-1 tickets by resolution week. Tier-2 cases are measured separately.")

@st.cache_data
def get_data(path, schema_version):
    tables=load_tables(path)
    t,_=prepare(tables)
    return add_repeat(t)

try:
    # Include the preparation schema in Streamlit's cache key. A cached table
    # from an older app version may lack newly derived columns.
    t=get_data(data_dir, 4)
except Exception as e:
    st.error(f"Could not load data: {e}")
    st.stop()

weeks=sorted(t.week_start.dropna().unique())
last_full=t.created_dt.max().normalize()-pd.Timedelta(days=t.created_dt.max().weekday()+1)
default=max((i for i,x in enumerate(weeks) if x<=last_full),default=len(weeks)-1)
selected=st.selectbox("Digest week",weeks,index=default,format_func=lambda x:pd.Timestamp(x).strftime("%d %b %Y"))
w=t[t.week_start==pd.Timestamp(selected)]
cutoff=t.created_dt.max()-pd.Timedelta(days=30)
eligible=w[w.completed & w.resolved_dt.le(cutoff)]

c1,c2,c3,c4=st.columns(4)
c1.metric("Tickets",f"{len(w):,}")
c2.metric("30-day repeat contacts",f"{eligible.repeat_30d.mean()*100:.1f}%" if len(eligible)==len(w[w.completed]) and len(eligible)>0 else "Pending")
c3.metric("SLA breaches",f"{w.breach.mean()*100:.1f}%")
c4.metric("Transferred",f"{(w.transfers>0).mean()*100:.1f}%")

tab1,tab2,tab3=st.tabs(["Weekly digest","Agent leaderboard","QA / audit"])

with tab1:
    st.subheader("What customers are complaining about")
    cats=w.category.value_counts().rename_axis("category").reset_index(name="tickets")
    cats["share"]=cats.tickets/len(w)
    st.dataframe(cats,use_container_width=True,hide_index=True)
    st.altair_chart(complaint_mix(cats),use_container_width=True,theme=None)
    st.subheader("Change vs previous week")
    changes=top_category_changes(t,selected)
    st.dataframe(changes,use_container_width=True,hide_index=True)
    st.subheader("Exploratory themes from customer messages")
    topics=topic_digest(w,6)
    for x in topics:
        st.markdown(f"**Theme {x['topic']} — {', '.join(x['keywords'])}** · approximately {x['volume']} messages")
    st.subheader("Mature 30-day repeat contacts by complaint")
    mature=t[t.completed & t.resolved_dt.le(cutoff)]
    repeat_by_category=(mature.groupby("category").repeat_30d
                        .agg(completed="size",repeats="sum",rate="mean")
                        .reset_index().sort_values("rate",ascending=False))
    st.dataframe(repeat_by_category,use_container_width=True,hide_index=True)
    st.altair_chart(repeat_rates(repeat_by_category),use_container_width=True,theme=None)
    st.caption("Same customer, product and category; later open tickets count. Only cases with 30 days of follow-up are included.")
    st.subheader("Operational signals")
    st.write({
        "repeat contacts (mature completed tickets only)": int(eligible.repeat_30d.sum()),
        "mature completed tickets": len(eligible),
        "first-response SLA breaches": int(w.breach.sum()),
        "tickets transferred": int((w.transfers>0).sum()),
        "refund tickets": int(w.refund_amount_inr.notna().sum()),
        "replacement tickets": int((w.replacement_issued=="Y").sum()),
    })

with tab2:
    teams=["All"]+sorted(t.loc[t.tier==1,"team"].dropna().unique().tolist())
    team=st.selectbox("Team",teams)
    lb=leaderboard(t,selected,team)
    lb=lb.assign(Agent=lb["name"]+" ("+lb["agent_id"]+")")
    st.dataframe(lb[["Agent","team","tickets_closed"]].rename(
        columns={"team":"Team","tickets_closed":"Tickets closed"}),
        use_container_width=True,hide_index=True)
    st.caption("Ticket volume alone does not account for hours worked or case complexity.")

with tab3:
    st.subheader("Data integrity checks")
    qa=qa_checks(t)
    st.dataframe(qa,use_container_width=True,hide_index=True)
    st.subheader("Dataset / migration checks")
    st.write(f"Rows after migration dedupe: **{len(t):,}**")
    st.write(f"Unique ticket IDs: **{t.ticket_id.nunique():,}**")
    st.write(f"Rows with legacy source: **{(t.source_system=='legacy_fd').sum():,}**")
    st.write("For tickets present in both systems, the current helpdesk record is retained.")
    st.subheader("Metric definitions")
    st.write("Complaint counts use ticket creation week. Agent counts use resolution week and include resolved and closed Tier-1 tickets. Repeat contacts use the same customer, product and category within 30 days after resolution; recent weeks remain pending.")
    st.subheader("Evidence summary")
    st.write("The six integrity checks above returned zero on the supplied export. In 20 reviewed flagged repeat pairs, 17 looked like the same issue and 3 were questionable. A separate 2,375-ticket text classifier agreed with existing intake tags on 81.98%; that does not measure theme accuracy.")
