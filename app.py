
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# --------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Malaysia FinTech Explorer",
    page_icon="📊",
    layout="wide",
)

st.title("🇲🇾 Malaysia FinTech Explorer")
st.caption(
    "Explore Malaysian payment-system activity using "
    "monthly data from the official dataset."
)

# --------------------------------------------------
# 2. LOAD AND CLEAN DATA
# --------------------------------------------------

DATA_FILE = Path(
    "data/fintech/malaysia_payment_systems_2016_2026.csv"
)


@st.cache_data
def load_data(file_path):
    data = pd.read_csv(file_path)

    data["date"] = pd.to_datetime(
        data["date"], errors="coerce"
    )
    data["volume"] = pd.to_numeric(
        data["volume"], errors="coerce"
    )
    data["value"] = pd.to_numeric(
        data["value"], errors="coerce"
    )

    data["system"] = data["system"].astype(str).str.lower()

    data = data.dropna(
        subset=["date", "volume", "value", "system"]
    )

    # Keep the requested period.
    data = data[
        (data["date"] >= "2016-01-01")
        & (data["date"] <= "2026-12-31")
    ]

    # Aggregate duplicate records, if any.
    data = (
        data.groupby(["date", "system"], as_index=False)
        .agg(
            volume=("volume", "sum"),
            value=("value", "sum"),
        )
        .sort_values("date")
    )

    return data


if not DATA_FILE.exists():
    st.error(
        f"Data file not found: {DATA_FILE}\n\n"
        "Check that app.py is in your project root "
        "and that the CSV exists in data/fintech/."
    )
    st.stop()

df = load_data(str(DATA_FILE))

if df.empty:
    st.error("The CSV contains no usable records.")
    st.stop()

# --------------------------------------------------
# 3. SIDEBAR FILTERS
# --------------------------------------------------

st.sidebar.header("Dashboard Filters")

available_systems = sorted(df["system"].unique())

selected_systems = st.sidebar.multiselect(
    "Payment systems",
    options=available_systems,
    default=available_systems,
    help="Select one or more systems to compare.",
)

min_date = df["date"].min().date()
max_date = df["date"].max().date()

selected_dates = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

exclude_rentas = st.sidebar.checkbox(
    "Exclude RENTAS from comparisons",
    value=False,
    help=(
        "RENTAS handles high-value payments, "
        "so its scale can dominate charts."
    ),
)

# Handle incomplete date selection.
if isinstance(selected_dates, (tuple, list)):
    if len(selected_dates) == 2:
        start_date, end_date = selected_dates
    else:
        st.warning("Please select both a start and end date.")
        st.stop()
else:
    start_date = selected_dates
    end_date = selected_dates

if start_date > end_date:
    st.error("The start date must be before the end date.")
    st.stop()

# Apply the selected filters.
filtered = df[
    (df["date"].dt.date >= start_date)
    & (df["date"].dt.date <= end_date)
    & (df["system"].isin(selected_systems))
].copy()

if exclude_rentas:
    filtered = filtered[
        filtered["system"] != "rentas"
    ].copy()

if filtered.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

st.sidebar.caption(
    f"Showing {filtered['date'].min():%b %Y} "
    f"to {filtered['date'].max():%b %Y}"
)


# Calculate year-on-year growth using the full dataset.
growth_data = df.sort_values(["system", "date"]).copy()

growth_data["volume_previous_year"] = (
    growth_data.groupby("system")["volume"].shift(12)
)

growth_data["volume_yoy_pct"] = (
    growth_data["volume"]
    .div(growth_data["volume_previous_year"])
    .sub(1)
    .mul(100)
)

growth_data["value_previous_year"] = (
    growth_data.groupby("system")["value"].shift(12)
)

growth_data["value_yoy_pct"] = (
    growth_data["value"]
    .div(growth_data["value_previous_year"])
    .sub(1)
    .mul(100)
)


# --------------------------------------------------
# 4. SUMMARY METRICS
# --------------------------------------------------

total_volume = filtered["volume"].sum()
total_value = filtered["value"].sum()
system_count = filtered["system"].nunique()
month_count = filtered["date"].dt.to_period("M").nunique()

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Transactions",
    f"{total_volume:,.0f}",
)

col2.metric(
    "Total Transaction Value",
    f"{total_value:,.0f}",
)

col3.metric(
    "Payment Systems",
    f"{system_count}",
)

col4.metric(
    "Months Covered",
    f"{month_count}",
)

st.caption(
    "Metrics reflect the selected filters. Transaction value "
    "uses the source dataset's original unit; verify its "
    "official metadata before labelling it as RM."
)

st.divider()

# --------------------------------------------------
# 5. MONTHLY TRANSACTION VOLUME
# --------------------------------------------------

st.subheader("Monthly Transaction Volume")

monthly_volume = (
    filtered.groupby(
        [pd.Grouper(key="date", freq="MS"), "system"],
        as_index=False,
    )["volume"]
    .sum()
)

fig_volume = px.line(
    monthly_volume,
    x="date",
    y="volume",
    color="system",
    markers=True,
    title="Transaction Count by Month",
    labels={
        "date": "Month",
        "volume": "Number of Transactions",
        "system": "Payment System",
    },
)

fig_volume.update_layout(
    hovermode="x unified",
    legend_title_text="Payment System",
)

st.plotly_chart(fig_volume, use_container_width=True)

# --------------------------------------------------
# 6. MONTHLY TRANSACTION VALUE
# --------------------------------------------------

st.subheader("Monthly Transaction Value")

monthly_value = (
    filtered.groupby(
        [pd.Grouper(key="date", freq="MS"), "system"],
        as_index=False,
    )["value"]
    .sum()
)

fig_value = px.line(
    monthly_value,
    x="date",
    y="value",
    color="system",
    markers=True,
    title="Transaction Value by Month",
    labels={
        "date": "Month",
        "value": "Transaction Value (source unit)",
        "system": "Payment System",
    },
)

fig_value.update_layout(
    hovermode="x unified",
    legend_title_text="Payment System",
)

st.plotly_chart(fig_value, use_container_width=True)


# --------------------------------------------------
# YEAR-ON-YEAR GROWTH ANALYSIS
# --------------------------------------------------

st.divider()
st.subheader("Year-on-Year Growth Analysis")

growth_filtered = growth_data[
    (growth_data["date"].dt.date >= start_date)
    & (growth_data["date"].dt.date <= end_date)
    & (growth_data["system"].isin(selected_systems))
].copy()

if exclude_rentas:
    growth_filtered = growth_filtered[
        growth_filtered["system"] != "rentas"
    ]

growth_filtered = growth_filtered.dropna(
    subset=["volume_yoy_pct"]
)

if not growth_filtered.empty:
    fig_growth = px.line(
        growth_filtered,
        x="date",
        y="volume_yoy_pct",
        color="system",
        markers=True,
        title="Monthly Transaction Volume Growth vs Same Month Last Year",
        labels={
            "date": "Month",
            "volume_yoy_pct": "Growth (%)",
            "system": "Payment System",
        },
    )

    # Zero means no growth; negative values mean a decline.
    fig_growth.add_hline(
        y=0,
        line_dash="dash",
        line_color="gray",
    )

    fig_growth.update_layout(hovermode="x unified")

    st.plotly_chart(fig_growth, use_container_width=True)
else:
    st.info(
        "No year-on-year comparisons are available "
        "for the selected period."
    )


# --------------------------------------------------
# 7. YEARLY TRANSACTION VOLUME
# --------------------------------------------------

st.subheader("Annual Transaction Volume")

annual = (
    filtered.assign(year=filtered["date"].dt.year)
    .groupby(["year", "system"], as_index=False)
    .agg(
        volume=("volume", "sum"),
        value=("value", "sum"),
        months=("date", lambda dates: dates.dt.to_period("M").nunique()),
    )
)

fig_annual = px.bar(
    annual,
    x="year",
    y="volume",
    color="system",
    barmode="group",
    title="Annual Transaction Volume",
    labels={
        "year": "Year",
        "volume": "Number of Transactions",
        "system": "Payment System",
    },
)

st.plotly_chart(fig_annual, use_container_width=True)

st.caption(
    "Annual totals for the current year may cover only part "
    "of the year. Compare full years with full years."
)

# --------------------------------------------------
# 8. PAYMENT SYSTEM COMPARISON
# --------------------------------------------------

st.subheader("Payment System Comparison")

comparison = (
    filtered.groupby("system", as_index=False)
    .agg(
        transactions=("volume", "sum"),
        transaction_value=("value", "sum"),
    )
    .sort_values("transactions", ascending=False)
)

fig_comparison = px.bar(
    comparison,
    x="system",
    y="transactions",
    color="system",
    title="Total Transactions by Payment System",
    labels={
        "system": "Payment System",
        "transactions": "Number of Transactions",
    },
)

st.plotly_chart(fig_comparison, use_container_width=True)

st.dataframe(
    comparison,
    use_container_width=True,
    hide_index=True,
)


# --------------------------------------------------
# 2025 VS 2026 HALF-YEAR COMPARISON
# --------------------------------------------------

st.divider()
st.header("First-Half-Year Comparison")
st.caption(
    "January–June 2025 compared with January–June 2026"
)

comparison_data = df[
    (
        (df["date"].dt.year == 2025)
        | (df["date"].dt.year == 2026)
    )
    & (df["date"].dt.month.between(1, 6))
].copy()

if exclude_rentas:
    comparison_data = comparison_data[
        comparison_data["system"] != "rentas"
    ]

comparison_summary = (
    comparison_data.assign(
        year=comparison_data["date"].dt.year
    )
    .groupby(["system", "year"], as_index=False)
    .agg(
        volume=("volume", "sum"),
        value=("value", "sum"),
        months=("date", lambda x: x.dt.to_period("M").nunique()),
    )
)

volume_table = comparison_summary.pivot(
    index="system", columns="year", values="volume"
)

value_table = comparison_summary.pivot(
    index="system", columns="year", values="value"
)

month_table = comparison_summary.pivot(
    index="system", columns="year", values="months"
)

# Only compare systems with all six months in both years.
valid_systems = [
    system
    for system in volume_table.index
    if (
        2025 in month_table.columns
        and 2026 in month_table.columns
        and month_table.loc[system, 2025] == 6
        and month_table.loc[system, 2026] == 6
        and volume_table.loc[system, 2025] != 0
        and value_table.loc[system, 2025] != 0
    )
]

if valid_systems:
    comparison_view = pd.DataFrame({
        "system": valid_systems,
        "volume_2025": [
            volume_table.loc[s, 2025] for s in valid_systems
        ],
        "volume_2026": [
            volume_table.loc[s, 2026] for s in valid_systems
        ],
        "value_2025": [
            value_table.loc[s, 2025] for s in valid_systems
        ],
        "value_2026": [
            value_table.loc[s, 2026] for s in valid_systems
        ],
    })

    comparison_view["volume_growth_pct"] = (
        comparison_view["volume_2026"]
        / comparison_view["volume_2025"] - 1
    ) * 100

    comparison_view["value_growth_pct"] = (
        comparison_view["value_2026"]
        / comparison_view["value_2025"] - 1
    ) * 100

    # Transaction volume comparison
    volume_chart_data = comparison_view.melt(
        id_vars="system",
        value_vars=["volume_2025", "volume_2026"],
        var_name="period",
        value_name="transactions",
    )

    volume_chart_data["period"] = (
        volume_chart_data["period"]
        .map({
            "volume_2025": "Jan–Jun 2025",
            "volume_2026": "Jan–Jun 2026",
        })
    )

    fig_half_volume = px.bar(
        volume_chart_data,
        x="system",
        y="transactions",
        color="period",
        barmode="group",
        title="Transaction Volume: Same Period Comparison",
        labels={
            "system": "Payment System",
            "transactions": "Number of Transactions",
            "period": "Period",
        },
    )

    st.plotly_chart(
        fig_half_volume,
        use_container_width=True,
    )

    # Transaction value comparison
    value_chart_data = comparison_view.melt(
        id_vars="system",
        value_vars=["value_2025", "value_2026"],
        var_name="period",
        value_name="value",
    )

    value_chart_data["period"] = (
        value_chart_data["period"]
        .map({
            "value_2025": "Jan–Jun 2025",
            "value_2026": "Jan–Jun 2026",
        })
    )

    fig_half_value = px.bar(
        value_chart_data,
        x="system",
        y="value",
        color="period",
        barmode="group",
        title="Transaction Value: Same Period Comparison",
        labels={
            "system": "Payment System",
            "value": "Transaction Value (RM)",
            "period": "Period",
        },
    )

    st.plotly_chart(
        fig_half_value,
        use_container_width=True,
    )

    # Automatic insights
    fastest_volume = comparison_view.loc[
        comparison_view["volume_growth_pct"].idxmax()
    ]

    fastest_value = comparison_view.loc[
        comparison_view["value_growth_pct"].idxmax()
    ]

    declining = comparison_view[
        comparison_view["volume_growth_pct"] < 0
    ]

    st.subheader("Key Insights")

    col1, col2 = st.columns(2)

    col1.metric(
        "Fastest Volume Growth",
        fastest_volume["system"].upper(),
        f"{fastest_volume['volume_growth_pct']:+.2f}%",
    )

    col2.metric(
        "Fastest Value Growth",
        fastest_value["system"].upper(),
        f"{fastest_value['value_growth_pct']:+.2f}%",
    )

    if not declining.empty:
        st.warning(
            "Transaction volume declined for: "
            + ", ".join(declining["system"].str.upper())
        )
    else:
        st.success(
            "All included payment systems recorded "
            "non-negative transaction volume growth."
        )

    st.subheader("Growth Comparison Table")

    display_table = comparison_view.copy()

    for column in [
        "volume_2025", "volume_2026",
        "value_2025", "value_2026"
    ]:
        display_table[column] = display_table[column].map(
            lambda x: f"{x:,.0f}"
        )

    for column in ["volume_growth_pct", "value_growth_pct"]:
        display_table[column] = display_table[column].map(
            lambda x: f"{x:+.2f}%"
        )

    st.dataframe(
        display_table,
        use_container_width=True,
        hide_index=True,
    )

else:
    st.warning(
        "A complete six-month comparison is not available "
        "for the selected data."
    )


# --------------------------------------------------
# 9. DOWNLOAD FILTERED DATA
# --------------------------------------------------

st.subheader("Explore and Export Data")

st.dataframe(
    filtered.sort_values("date", ascending=False),
    use_container_width=True,
    hide_index=True,
)

csv_data = filtered.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    label="Download filtered data as CSV",
    data=csv_data,
    file_name="malaysia_fintech_filtered_data.csv",
    mime="text/csv",
)

st.success("Dashboard loaded successfully.")
