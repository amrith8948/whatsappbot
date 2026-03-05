import streamlit as st
import requests
import os
import pandas as pd

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TABLE_NAME = "admissions_chat"

st.set_page_config(layout="wide")
st.title("📊 Invisor AI Lead Dashboard")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

response = requests.get(
    f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?select=*",
    headers=headers
)

data = response.json()
df = pd.DataFrame(data)

if df.empty:
    st.warning("No leads yet.")
    st.stop()

# KPIs
col1, col2, col3 = st.columns(3)
col1.metric("Total Leads", len(df))
col2.metric("Hot Leads", len(df[df["lead_type"] == "Hot"]))
col3.metric("Scholarship Interested", len(df[df["scholarship_interest"] == True]))

st.divider()

# Filters
lead_type_filter = st.selectbox("Filter by Lead Type", ["All", "Hot", "Warm", "Cold"])

if lead_type_filter != "All":
    df = df[df["lead_type"] == lead_type_filter]

st.dataframe(df)
