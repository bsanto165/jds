# main.tf
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
  default_tags {
    tags = {
      Environment = "Sandbox-POC"
      Project     = "AI-Judgment-Platform"
      CostCenter  = "HR-Tech-Transformation"
    }
  }
}

# --- S3 Buckets for RAG Source Assets ---
resource "aws_s3_bucket" "knowledge_base_bucket" {
  bucket        = "enterprise-judgment-kb-source-lake"
  force_destroy = true # Safeguard for sandbox cleanup
}

resource "aws_s3_bucket_public_access_block" "kb_private_block" {
  bucket                  = aws_s3_bucket.knowledge_base_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# --- IAM Role for Lambda Engine ---
resource "aws_iam_role" "lambda_exec_role" {
  name = "judgment-engine-lambda-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "://amazonaws.com" }
    }]
  })
})

resource "aws_iam_policy" "lambda_bedrock_rds_policy" {
  name        = "judgment-engine-resource-access"
  description = "Allows access to Bedrock runtime, S3 bucket, and RDS cluster endpoints"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["bedrock:InvokeModel", "bedrock:Retrieve"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:ListBucket"]
        Resource = [
          aws_s3_bucket.knowledge_base_bucket.arn,
          "${aws_s3_bucket.knowledge_base_bucket.arn}/*"
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["rds-data:ExecuteStatement", "rds-data:BatchExecuteStatement"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_attach" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_bedrock_rds_policy.arn
}

# --- AWS Lambda Orchestration Engine ---
resource "aws_lambda_function" "judgment_orchestrator" {
  filename         = "lambda_function.zip" # Packaged zip containing script
  function_name    = "judgment-telemetry-orchestrator"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.11"
  timeout          = 29 # Aligned with API Gateway limits
  memory_size      = 512

  environment {
    variables = {
      KB_ID        = "PLACEHOLDER_BEDROCK_KB_ID"
      DB_SECRET_ARN = "PLACEHOLDER_SECRET_ARN"
      DB_CLUSTER_ARN = "PLACEHOLDER_RDS_CLUSTER_ARN"
      DB_NAME      = "judgment_analytics"
    }
  }
}

# --- Amazon API Gateway (REST Ingress Layer) ---
resource "aws_api_gateway_rest_api" "telemetry_api" {
  name        = "AI-Judgment-Telemetry-Ingress"
  description = "API Endpoint to ingest student telemetry loops and return RAG audit checks"
}

resource "aws_api_gateway_resource" "telemetry_resource" {
  rest_api_id = aws_api_gateway_rest_api.telemetry_api.id
  parent_id   = aws_api_gateway_rest_api.telemetry_api.root_resource_id
  path_part   = "telemetry"
}

resource "aws_api_gateway_method" "post_telemetry" {
  rest_api_id   = aws_api_gateway_rest_api.telemetry_api.id
  resource_id   = aws_api_gateway_resource.telemetry_resource.id
  http_method   = "POST"
  authorization = "NONE" # Update with API Keys / Cognito for production
}

resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id             = aws_api_gateway_rest_api.telemetry_api.id
  resource_id             = aws_api_gateway_resource.telemetry_resource.id
  http_method             = aws_api_gateway_method.post_telemetry.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.judgment_orchestrator.invoke_arn
}

resource "aws_lambda_permission" "apigw_lambda" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.judgment_orchestrator.function_name
  principal     = "://amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.telemetry_api.execution_arn}/*/*"
}

resource "aws_api_gateway_deployment" "poc_deployment" {
  depends_on  = [aws_api_gateway_integration.lambda_integration]
  rest_api_id = aws_api_gateway_rest_api.telemetry_api.id
  stage_name  = "poc"
}

output "api_endpoint" {
  value = "${aws_api_gateway_deployment.poc_deployment.invoke_url}/telemetry"
}
