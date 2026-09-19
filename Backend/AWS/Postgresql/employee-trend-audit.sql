# This query calculates the rolling average at an individual employee level. It mimics the exact operation your backend AWS Lambda function runs when displaying parameters to the Streamlit UI interface.

-- Micro Audit: Validates individual 60-day rolling performance trends
SELECT 
    id,
    employee_id,
    cohort_id,
    timestamp::DATE as submission_date,
    score AS daily_submission_score,
    ROUND(
        AVG(score) OVER(
            PARTITION BY employee_id 
            ORDER BY timestamp
            RANGE BETWEEN INTERVAL '60 days' PRECEDING AND CURRENT ROW
        ), 2
    ) AS calculated_60_day_rolling_avg
FROM employee_daily_scores
WHERE employee_id = 'EMP101' -- Test swap with EMP001 to compare tracks
ORDER BY timestamp DESC;
