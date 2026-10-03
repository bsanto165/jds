# lambda_function.py
import os
import json
import boto3

bedrock_agent_runtime = boto3.client(service_name='bedrock-agent-runtime', region_name='us-east-1')
rds_data = boto3.client(service_name='rds-data', region_name='us-east-1')

KB_ID = os.environ['KB_ID']
DB_SECRET_ARN = os.environ['DB_SECRET_ARN']
DB_CLUSTER_ARN = os.environ['DB_CLUSTER_ARN']
DB_NAME = os.environ['DB_NAME']

def execute_rds_statement(sql, parameters=[]):
    return rds_data.execute_statement(
        secretArn=DB_SECRET_ARN,
        resourceArn=DB_CLUSTER_ARN,
        database=DB_NAME,
        sql=sql,
        parameters=parameters
    )

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        employee_id = body.get('employee_id')
        cohort_id = body.get('cohort_id')
        student_submission = body.get('submission_text')
        
        # 1. Query Amazon Bedrock Knowledge Base for Framework Verification (NIST / TOGAF)
        kb_response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=KB_ID,
            retrievalQuery={'text': student_submission}
        )
        
        # Basic keyword evaluation check (e.g., checking for specific validation flags)
        has_skepticism_marker = any(k in student_submission.lower() for k in ["verify", "audit", "hallucination", "bias"])
        intent_score = 85 if has_skepticism_marker else 55
        
        # 2. Write Numeric Scores into Aurora PostgreSQL Data Table
        insert_sql = """
            INSERT INTO employee_daily_scores (employee_id, cohort_id, score, timestamp)
            VALUES (:employee_id, :cohort_id, :score, CURRENT_TIMESTAMP);
        """
        execute_rds_statement(insert_sql, [
            {'name': 'employee_id', 'value': {'stringValue': employee_id}},
            {'name': 'cohort_id', 'value': {'stringValue': cohort_id}},
            {'name': 'score', 'value': {'doubleValue': float(intent_score)}}
        ])
        
        # 3. Calculate 60-Day Rolling Window Trend Data
        trend_sql = """
            SELECT AVG(score) as rolling_avg FROM employee_daily_scores
            WHERE employee_id = :employee_id AND timestamp >= CURRENT_DATE - INTERVAL '60 days';
        """
        trend_res = execute_rds_statement(trend_sql, [
            {'name': 'employee_id', 'value': {'stringValue': employee_id}}
        ])
        
        rolling_avg = trend_res['records'][0][0].get('doubleValue', float(intent_score))

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'status': 'Processed',
                'calculated_score': intent_score,
                'rolling_60_day_avg': rolling_avg,
                'rag_context_retrieved': len(kb_response.get('results', []))
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
