# Inject your specific AWS Sandbox resource parameters

export AWS_DEFAULT_REGION="us-east-1"
export DB_CLUSTER_ARN="arn:aws:rds:us-east-1:123456789012:cluster:your-actual-cluster-name"
export DB_SECRET_ARN="arn:aws:secretsmanager:us-east-1:123456789012:secret:your-actual-secret-name"

# Boot up the local webserver dashboard
streamlit run app.py
