# You can run these scripts directly using the AWS Console via the RDS Query Editor, or execute them from your terminal profile using the AWS CLI Data API wrapper:

aws rds-data execute-statement \
    --resource-arn "YOUR_DB_CLUSTER_ARN" \
    --secret-arn "YOUR_DB_SECRET_ARN" \
    --database "judgment_analytics" \
    --sql "SELECT cohort_id, COUNT(*), ROUND(AVG(score), 2) FROM employee_daily_scores GROUP BY cohort_id;"
