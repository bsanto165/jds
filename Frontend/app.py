# app.py
import streamlit as st
import requests
import json

API_ENDPOINT = "YOUR_API_GATEWAY_URL_OUTPUT_HERE"

st.set_page_config(page_title="AI Judgment Evaluation Platform", layout="wide")
st.title("🛡️ Enterprise Workforce Transformation Core")
st.caption("Validating Human-in-the-Loop Capabilities and Decisional Accuracy")

# Sidebar - Session & Profile Router Configuration
st.sidebar.header("User Navigation Profile")
employee_id = st.sidebar.text_input("Employee Corporate ID", value="EMP001")
learning_track = st.sidebar.selectbox(
    "Assigned Learning Track",
    ["6-Month Initial Upskilling (Help Desk Shift)", "4-Month Advanced TOGAF Cohort"]
)
cohort_id = "cohort-upskill-01" if "6-Month" in learning_track else "cohort-togaf-alpha"

# Content Panel Layout
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Active Practical Lab Environment")
    if "6-Month" in learning_track:
        st.markdown("**Scenario Prompt:** Evaluate an AI-generated network expansion proposal. Highlight specific architectural assumptions, compliance traps, or structural errors.")
    else:
        st.markdown("**Scenario Prompt [TOGAF Cohort Only]:** Document the technical gap analysis and risk boundaries for moving the monolithic ledger architecture to decoupled serverless primitives.")
        
    submission_text = st.text_area("Enter your response draft below for system audit:", height=300)

    if st.button("Submit Artifact to Ingress Pipeline"):
        if submission_text.strip() == "":
            st.error("Submission text area cannot be left empty.")
        else:
            with st.spinner("Pushing payload through validation and data engine..."):
                payload = {
                    "employee_id": employee_id,
                    "cohort_id": cohort_id,
                    "submission_text": submission_text
                }
                try:
                    res = requests.post(API_ENDPOINT, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        st.success("Telemetry logged successfully!")
                        st.metric(label="Calculated Daily Metric Score", value=f"{data['calculated_score']} / 100")
                        st.metric(label="60-Day Rolling Competency Avg", value=f"{round(data['rolling_60_day_avg'], 2)}")
                    else:
                        st.error(f"API Error Code: {res.status_code} - {res.text}")
                except Exception as e:
                    st.error(f"Network Pipeline Connection Refused: {str(e)}")

with col2:
    st.subheader("System Performance Metric Guardrails")
    st.info("💡 **System Rules Active:** If navigating the 4-Month TOGAF path, the schema enforcement rules enforce a rigid boundary condition blocking database sync states unless exactly 4 participants submit data loops.")


#  This snippet queries your database, processes the data loop using Pandas, and uses st.line_chart to render the 60-day rolling averages as an interactive, web-native visualization.

import pandas as pd
import streamlit as st
import boto3

# --- AWS SDK Setup for Data Ingestion ---
rds_data = boto3.client(service_name='rds-data', region_name='us-east-1')

# Ensure your environment variables from main.tf are accessible
DB_CLUSTER_ARN = "YOUR_RDS_CLUSTER_ARN"
DB_SECRET_ARN = "YOUR_SECRET_ARN"
DB_NAME = "judgment_analytics"

def get_historical_trend_dataframe():
    """Queries Aurora, calculates the 60-day rolling average via Pandas, and formats for Streamlit."""
    sql_query = """
        SELECT cohort_id, score, timestamp::DATE as evaluation_date 
        FROM employee_daily_scores
        ORDER BY timestamp::DATE ASC;
    """
    
    # Fetch data using the AWS Data API
    response = rds_data.execute_statement(
        resourceArn=DB_CLUSTER_ARN,
        secretArn=DB_SECRET_ARN,
        database=DB_NAME,
        sql=sql_query
    )
    
    # Parse the response records into a structured list
    records = []
    for record in response.get('records', []):
        records.append({
            'cohort_id': record[0]['stringValue'],
            'score': record[1]['doubleValue'] if 'doubleValue' in record[1] else float(record[1].get('stringValue', 0)),
            'evaluation_date': pd.to_datetime(record[2]['stringValue'])
        })
        
    if not records:
        return pd.DataFrame() # Return empty DataFrame if no data exists yet

    # Convert to Pandas DataFrame
    df = pd.DataFrame(records)
    
    # 1. Collapse multiple daily entries per cohort into a clean daily mean baseline
    daily_df = df.groupby(['cohort_id', 'evaluation_date'])['score'].mean().reset_index()
    daily_df = daily_df.set_index('evaluation_date')
    
    # 2. Compute the true temporal 60-day rolling average per cohort channel
    daily_df['60_Day_Rolling_Avg'] = daily_df.groupby('cohort_id')['score'].transform(
        lambda x: x.rolling(window='60D', min_periods=1).mean()
    )
    
    # 3. Pivot the table layout so columns represent cohorts (Required format for st.line_chart)
    chart_pivot = daily_df.reset_index().pivot(
        index='evaluation_date', 
        columns='cohort_id', 
        values='60_Day_Rolling_Avg'
    )
    
   # --- Streamlit UI Render Block ---

# 
st.subheader("📈 JDS Competency Trend Over Time")
st.markdown("Visualizing the 60-day rolling average verification paths across active enterprise tracks.")

try:
    with st.spinner("Analyzing workforce historical telemetry data..."):
        trend_data = get_historical_trend_dataframe()
        
        if not trend_data.empty:
            # Renders an interactive line graph with native hover metrics, pan, and zoom
            st.line_chart(
                data=trend_data,
                use_container_width=True
            )
            st.caption("💡 Hover over the data paths to audit precise numeric scores across specific evaluation milestones.")
        else:
            st.warning("⚠️ No historical trend telemetry logs found. Run your Python seed script first.")

except Exception as e:
    st.error(f"Failed to render interactive telemetry metrics visualization: {str(e)}")
