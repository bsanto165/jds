# To securely run this pipeline against your AWS sandbox architecture without hardcoding parameters, pass your resource strings dynamically through your environment parameters:

export DB_CLUSTER_ARN="arn:aws:rds:us-east-1:123456789012:cluster:your-actual-cluster-name"
export DB_SECRET_ARN="arn:aws:secretsmanager:us-east-1:123456789012:secret:your-actual-secret-name"
export DB_NAME="judgment_analytics"

python seed_data.py
