
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent))
from data import load_tables, prepare
from insights import (add_repeat, weekly_summary, leaderboard, topic_digest,
                      top_category_changes, product_repeat_hotspots,
                      weekly_action_queue, channel_sla_exposure, qa_checks)
from charts import (ticket_trend, complaint_mix, repeat_rates,
                    product_hotspots, category_movement, channel_breaches)

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
    return add_repeat(t), tables["products"]

try:
    # Include the preparation schema in Streamlit's cache key. A cached table
    # from an older app version may lack newly derived columns.
    t,products=get_data(data_dir, 3)
except Exception as e:
    st.error(f"Could not load data: {e}")
    st.stop()

summary=weekly_summary(t)
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
    st.subheader("Weekly ticket volume")
    trend_rows=summary[summary.week_start.le(min(pd.Timestamp(selected),last_full))].tail(12)
    st.dataframe(trend_rows,use_container_width=True,hide_index=True)
    st.altair_chart(ticket_trend(summary,selected,last_full),use_container_width=True,theme=None)
    st.subheader("What customers are complaining about")
    cats=w.category.value_counts().rename_axis("category").reset_index(name="tickets")
    cats["share"]=cats.tickets/len(w)
    st.dataframe(cats,use_container_width=True,hide_index=True)
    st.altair_chart(complaint_mix(cats),use_container_width=True,theme=None)
    st.subheader("Mature 30-day repeat contacts by complaint")
    mature=t[t.completed & t.resolved_dt.le(cutoff)]
    repeat_by_category=(mature.groupby("category").repeat_30d
                        .agg(completed="size",repeats="sum",rate="mean")
                        .reset_index().sort_values("rate",ascending=False))
    st.dataframe(repeat_by_category,use_container_width=True,hide_index=True)
    st.altair_chart(repeat_rates(repeat_by_category),use_container_width=True,theme=None)
    st.caption("Same customer, product and category; later open tickets count. Only cases with 30 days of follow-up are included.")
    st.subheader("Product complaint hotspots")
    hotspots=product_repeat_hotspots(t,products,cutoff)
    st.dataframe(hotspots,use_container_width=True,hide_index=True)
    st.altair_chart(product_hotspots(hotspots),use_container_width=True,theme=None)
    st.caption("Groups with at least 50 completed cases. Excess repeats are the count above the 10% target.")
    st.subheader("Emerging themes from customer messages")
    topics=topic_digest(w,6)
    for x in topics:
        st.markdown(f"**Theme {x['topic']} — {', '.join(x['keywords'])}** · {x['volume']} tickets")
    st.subheader("Change vs previous week")
    changes=top_category_changes(t,selected)
    st.dataframe(changes,use_container_width=True,hide_index=True)
    st.altair_chart(category_movement(changes),use_container_width=True,theme=None)
    st.subheader("Weekly action queue")
    st.dataframe(weekly_action_queue(t,selected,cutoff),use_container_width=True,hide_index=True)
    st.caption("Sorted by weekly increase. Repeat rates use mature cases; SLA and transfer rates use this week.")
    st.subheader("First-response SLA by channel")
    channel_sla=channel_sla_exposure(w)
    st.dataframe(channel_sla,use_container_width=True,hide_index=True)
    st.altair_chart(channel_breaches(channel_sla),use_container_width=True,theme=None)
    st.caption("Potential credits use Rs 350 per breach. Credits are issued when tickets resolve.")
    st.subheader("Operational signals")
    st.write({
        "repeat-contact definition": "same customer + category + product within 30 days",
        "repeat contacts (mature completed tickets only)": int(eligible.repeat_30d.sum()),
        "mature completed tickets": len(eligible),
        "refund tickets": int(w.refund_amount_inr.notna().sum()),
        "replacement tickets": int((w.replacement_issued=="Y").sum()),
        "transfers": int((w.transfers>0).sum()),
    })

with tab2:
    teams=["All"]+sorted(t.loc[t.tier==1,"team"].dropna().unique().tolist())
    team=st.selectbox("Team",teams)
    lb=leaderboard(t,selected,team)
    st.dataframe(lb,use_container_width=True,hide_index=True)
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
