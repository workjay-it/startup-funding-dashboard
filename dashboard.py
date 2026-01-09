import streamlit as st
import duckdb
import pandas as pd
import os

st.set_page_config(page_title="VC Screening Dashboard", layout="wide")

st.title("Startup Funding Dashboard")
st.write("Interactive dashboard for exploring startup funding data")

# ---------------- Sidebar Filters ----------------
st.sidebar.header("Filters")

min_funding = st.sidebar.slider(
    "Minimum Total Funding (USD)",
    min_value=0,
    max_value=6_000_000_000,
    value=1_000_000_000,
    step=100_000_000
)

funded_year = st.sidebar.selectbox(
    "Funding Year",
    options=["All"] + list(range(1990, 2026)),
    index=0
)

min_investors = st.sidebar.slider(
    "Minimum Investor Count",
    min_value=0,
    max_value=50,
    value=5,
    step=1
)

# ---------------- Database ----------------
DB_PATH = os.path.join(os.getcwd(), "crunchbase.duckdb")
con = duckdb.connect(DB_PATH, read_only=True)

year_filter = ""
if funded_year != "All":
    year_filter = f"AND r.funded_year = {funded_year}"

query = f"""
SELECT
    c.name AS company,
    SUM(r.raised_amount_usd) AS total_funding_usd,
    COUNT(DISTINCT i.investor_name) AS investor_count
FROM companies c
JOIN rounds r
    ON c.permalink = r.company_permalink
LEFT JOIN investments i
    ON c.permalink = i.company_permalink
WHERE r.raised_amount_usd IS NOT NULL
    {year_filter}
GROUP BY c.name
HAVING
    SUM(r.raised_amount_usd) >= {min_funding}
    AND COUNT(DISTINCT i.investor_name) >= {min_investors}
ORDER BY total_funding_usd DESC
LIMIT 20
"""

df = con.execute(query).df()

tab1, tab2 = st.tabs(["Company Screening", "Funding Trends"])

with tab1:
    st.subheader("Top Funded Companies")
    st.dataframe(df, use_container_width=True)

    st.subheader("Funding Comparison")
    st.bar_chart(df.set_index("company")["total_funding_usd"])


# ---------------- Output ----------------
st.subheader("Top Funded Companies")
st.dataframe(df, use_container_width=True)

st.subheader("Top Companies by Total Funding")
st.bar_chart(df.set_index("company")["total_funding_usd"])

st.download_button(
    label="Download results as CSV",
    data=df.to_csv(index=False),
    file_name="top_funded_companies.csv",
    mime="text/csv"
)

