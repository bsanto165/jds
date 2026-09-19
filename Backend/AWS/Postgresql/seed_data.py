# This custom Python seed script simulates 60 days of rolling historical performance telemetry data. 
# It utilizes the AWS RDS Data API to insert realistic, time-distributed metrics directly into your Aurora PostgreSQL tables.
# The script models variance based on the track: The 6-Month Initial Upskilling group fluctuates around a baseline, while the 4-Month TOGAF Cohort reflects upward skill progression over the 60-day period.


# seed_data.py
import os
import random
from datetime import datetime, timedelta
import boto3

# --- AWS SDK Clients Configuration ---
# Uses local AWS profile credentials or IAM role execution contexts
rds_data = boto3.client(service_name='rds-data', region_name='us-east-1')

# --- Configuration Environment Enforcements ---
# These mirror the variables established in your main.tf deployment
DB_CLUSTER_ARN = os.environ.get('DB_CLUSTER_ARN', 'arn:aws:rds:us-east-1:123456789012:cluster:judgment-analytics-cluster')
DB_SECRET_ARN = os.environ.get('DB_SECRET_ARN', 'arn:aws:secretsmanager:us-east-1:123456789012:secret:database-credentials')
DB_NAME = os.environ.get('DB_NAME', 'judgment_analytics')

# --- Mock Identity & Structure Definition ---
COHORTS = {
    "cohort-upskill-01": ["EMP001", "EMP002", "EMP003", "EMP004", "EMP005"],
    "cohort-togaf-alpha": ["EMP101", "EMP102", "EMP103", "EMP104"]  # Enforces rigid 4-person limit rule
}

def run_sql(sql, parameters):
    """Executes a parameterized statement against Aurora Serverless v2 via Data API."""
    return rds_data.execute_statement(
        resourceArn=DB_CLUSTER_ARN,
        secretArn=DB_SECRET_ARN,
        database=DB_NAME,
        sql=sql,
        parameters=parameters
    )

def clear_existing_records():
    """Wipes historical seed records from target tables before processing execution loop."""
    print("🧹 Purging historical evaluation data rows...")
    run_sql("TRUNCATE TABLE employee_daily_scores CASCADE;", [])
    run_sql("TRUNCATE TABLE cohort_memberships CASCADE;", [])

def seed_cohort_memberships():
    """Populates group tracking table schemas to fulfill application constraint paths."""
    print("👥 Populating enterprise cohort structure metadata...")
    sql = "INSERT INTO cohort_memberships (cohort_id, employee_id) VALUES (:cohort_id, :employee_id);"
    
    for cohort_id, employee_list in COHORTS.items():
        for employee_id in employee_list:
            run_sql(sql, [
                {'name': 'cohort_id', 'value': {'stringValue': cohort_id}},
                {'name': 'employee_id', 'value': {'stringValue': employee_id}}
            ])

def generate_telemetry_history():
    """Generates continuous daily submission metrics spanning a 60-day testing window."""
    print("📊 Generating 60-day historical score telemetry distribution...")
    insert_sql = """
        INSERT INTO employee_daily_scores (employee_id, cohort_id, score, timestamp)
        VALUES (:employee_id, :cohort_id, :score, :timestamp);
    """
    
    base_date = datetime.utcnow() - timedelta(days=60)
    total_inserted = 0

    for day in range(61):
        current_timestamp = base_date + timedelta(days=day)
        # Add slight time randomization to simulate realistic submission offsets
        random_hour = random.randint(8, 18)
        random_minute = random.randint(0, 59)
        execution_time = current_timestamp.replace(hour=random_hour, minute=random_minute)
        formatted_time = execution_time.strftime('%Y-%m-%d %H:%M:%S')

        for cohort_id, employee_list in COHORTS.items():
            for employee_id in employee_list:
                # 1. Skip occasional weekend submissions to replicate work patterns (70% chance to submit)
                if execution_time.weekday() >= 5 and random.random() > 0.3:
                    continue
                
                # 2. Skip occasional random business days (10% churn rate missing data loop windows)
                if random.random() < 0.1:
                    continue

                # 3. Model score behavior tracking paths over time
                if cohort_id == "cohort-togaf-alpha":
                    # Progression model: Starts low, improves over 60 days
                    base_competency = 65 + (day * 0.4) 
                    variance = random.uniform(-8, 8)
                else:
                    # General fluctuation model: Flat average baseline
                    base_competency = 72
                    variance = random.uniform(-15, 15)

                final_score = max(0.0, min(100.0, base_competency + variance))

                run_sql(insert_sql, [
                    {'name': 'employee_id', 'value': {'stringValue': employee_id}},
                    {'name': 'cohort_id', 'value': {'stringValue': cohort_id}},
                    {'name': 'score', 'value': {'doubleValue': round(final_score, 2)}},
                    {'name': 'timestamp', 'value': {'stringValue': formatted_time}}
                ])
                total_inserted += 1

    print(Successfully generated and synchronized {total_inserted} telemetry records.)

if __name__ == "__main__":
    # Ensure AWS profile environment configurations are verified before running script execution loops
    try:
        clear_existing_records()
        seed_cohort_memberships()
        generate_telemetry_history()
        print("✅ Data seed operation complete. Data engine ready for sandbox verification.")
    except Exception as e:
        print(f"❌ Target Data Layer Refused Ingestion: {str(e)}")
        print("Verify your local terminal session exports match valid AWS DB_CLUSTER_ARN and DB_SECRET_ARN details.")
