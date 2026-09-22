"""Small, consistent charts for the weekly support review."""

import altair as alt
import pandas as pd

TEAL = "#0f766e"
BLUE = "#2563eb"
ORANGE = "#ea580c"


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
