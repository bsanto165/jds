-- Global Verification: Validates programmatic macro trends across cohorts
WITH daily_cohort_aggregates AS (
    SELECT 
        cohort_id,
        DATE(timestamp) as evaluation_date,
        AVG(score) as daily_avg_score
    FROM employee_daily_scores
    GROUP BY cohort_id, DATE(timestamp)
)
SELECT 
    cohort_id,
    evaluation_date,
    ROUND(daily_avg_score, 2) AS raw_daily_avg,
    ROUND(
        AVG(daily_avg_score) OVER(
            PARTITION BY cohort_id 
            ORDER BY evaluation_date 
            ROWS BETWEEN 59 PRECEDING AND CURRENT ROW
        ), 2
    ) AS rolling_60_day_cohort_avg
FROM daily_cohort_aggregates
ORDER BY cohort_id, evaluation_date DESC;
