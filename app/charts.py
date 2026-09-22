"""Small, consistent charts for the weekly support review."""

import altair as alt
import pandas as pd

TEAL = "#0f766e"
BLUE = "#2563eb"
ORANGE = "#ea580c"
SLATE = "#94a3b8"


def ticket_trend(summary, selected, last_full):
    data = summary[summary.week_start.le(min(pd.Timestamp(selected), last_full))].tail(12).copy()
    data["selected"] = data.week_start.eq(pd.Timestamp(selected))
    bars = alt.Chart(data).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X("week_start:T", title="Week beginning", axis=alt.Axis(format="%d %b", labelAngle=0)),
        y=alt.Y("tickets:Q", title="Tickets", scale=alt.Scale(zero=True)),
        color=alt.condition("datum.selected", alt.value(ORANGE), alt.value(TEAL)),
        tooltip=[alt.Tooltip("week_start:T", title="Week", format="%d %b %Y"),
                 alt.Tooltip("tickets:Q", title="Tickets"),
                 alt.Tooltip("breach_rate:Q", title="SLA breach rate", format=".1%")],
    )
    return bars.properties(height=230)


def complaint_mix(cats):
    data=cats.sort_values("tickets",ascending=False)
    return alt.Chart(data).mark_bar(cornerRadiusEnd=4,color=BLUE).encode(
        y=alt.Y("category:N", sort="-x", title=None),
        x=alt.X("tickets:Q", title="Tickets"),
        tooltip=[alt.Tooltip("category:N", title="Complaint"),
                 alt.Tooltip("tickets:Q", title="Tickets"),
                 alt.Tooltip("share:Q", title="Share", format=".1%")],
    ).properties(height=310)


def repeat_rates(by_category):
    data=by_category.copy()
    bars=alt.Chart(data).mark_bar(cornerRadiusEnd=4,color=TEAL).encode(
        y=alt.Y("category:N",sort="-x",title=None),
        x=alt.X("rate:Q",title="30-day repeat-contact proxy",axis=alt.Axis(format=".0%")),
        tooltip=[alt.Tooltip("category:N",title="Complaint"),
                 alt.Tooltip("completed:Q",title="Mature cases"),
                 alt.Tooltip("repeats:Q",title="Repeat contacts"),
                 alt.Tooltip("rate:Q",title="Repeat rate",format=".1%")],
    )
    target=alt.Chart(pd.DataFrame({"target":[0.10]})).mark_rule(
        color=ORANGE,strokeDash=[5,4],strokeWidth=2
    ).encode(x="target:Q")
    return (bars+target).properties(height=310)


def product_hotspots(hotspots):
    data=hotspots.copy()
    data["label"]=data.product_sku+" · "+data.category
    return alt.Chart(data).mark_bar(cornerRadiusEnd=4,color=ORANGE).encode(
        y=alt.Y("label:N",sort="-x",title=None),
        x=alt.X("excess_repeats_vs_target:Q",title="Repeat contacts above 10% target"),
        tooltip=[alt.Tooltip("product:N",title="Product"),
                 alt.Tooltip("category:N",title="Complaint"),
                 alt.Tooltip("completed:Q",title="Mature cases"),
                 alt.Tooltip("repeats:Q",title="Repeats"),
                 alt.Tooltip("repeat_rate:Q",title="Repeat rate",format=".1%")],
    ).properties(height=290)


def category_movement(changes):
    data=changes.copy()
    data["direction"]=data.change.ge(0)
    return alt.Chart(data).mark_bar(cornerRadiusEnd=3).encode(
        y=alt.Y("category:N",sort="-x",title=None),
        x=alt.X("change:Q",title="Tickets vs previous week"),
        color=alt.condition("datum.direction",alt.value(ORANGE),alt.value(TEAL)),
        tooltip=[alt.Tooltip("category:N",title="Complaint"),
                 alt.Tooltip("current:Q",title="This week"),
                 alt.Tooltip("previous:Q",title="Previous week"),
                 alt.Tooltip("change:Q",title="Change")],
    ).properties(height=310)


def channel_breaches(by_channel):
    return alt.Chart(by_channel).mark_bar(cornerRadiusEnd=4,color=ORANGE).encode(
        y=alt.Y("channel:N",sort="-x",title=None),
        x=alt.X("breach_rate:Q",title="First-response breach rate",axis=alt.Axis(format=".0%")),
        tooltip=[alt.Tooltip("channel:N",title="Channel"),
                 alt.Tooltip("tickets:Q",title="Tickets"),
                 alt.Tooltip("breaches:Q",title="Breaches"),
                 alt.Tooltip("breach_rate:Q",title="Breach rate",format=".1%"),
                 alt.Tooltip("potential_credit_inr:Q",title="Potential credit (Rs)",format=",.0f")],
    ).properties(height=170)
