This infrastructure design treats the training ecosystem as a production-grade enterprise data platform on AWS. Because you build pipelines for a living, this design skips the high-level hand-waving and maps out a Serverless, Event-Driven Knowledge & Telemetry Pipeline that separates static curriculum RAG vectors from dynamic multi-tenant stream tracking.
------------------------------
## 🏗️ 1. Global Platform System Architecture

                                [ CLIENT INTERFACE LAYER ]
                       Streamlit App (Hosted on AWS Amplify / ECS Fargate)
                                            │
                                            ▼ (HTTPS / JSON Payload)
                                [ INGRESS & SECURITY ]
                            Amazon API Gateway (REST API)
                                            │
                                            ▼ (Event Dispatch)
                           [ CORE ORCHESTRATION & EVENT FABRIC ]
                                   AWS Lambda Engine
                                            │
                 ┌──────────────────────────┴──────────────────────────┐
                 ▼ (Parallel Stream Async)                             ▼ (Sync Retrieval / Evaluation)
        [ EVENT STREAMING ]                                    [ GEN AI INFRASTRUCTURE ]
       Amazon Kinesis Data Streams                            Amazon Bedrock Knowledge Base
                 │                                                     │
                 ▼                                                     ▼ (Semantic Vector Indexing)
      Amazon Kinesis Firehose                                 Amazon OpenSearch Serverless
                 │                                                     │
                 ▼ (Batch Writing)                                     ▼ (Chunk Storage & Retrieval)
  ┌──────────────────────────────┐                      ┌──────────────────────────────┐
  │ S3 DATA LAKE: TELEMETRY BUCKET│                      │ S3 DATA LAKE: RETRIEVAL BUCKET│
  │ (Parquet / Gzip Partitioned) │                      │ (Source Markdown/PDF Assets) │
  └──────────────────────────────┘                      └──────────────────────────────┘
                 │
                 ▼ (Serverless Analytics)
         Amazon Athena / Glue

------------------------------
## 📁 2. S3 Storage Pipeline & Partitioning Strategy
To prevent a messy directory structure, we split the data platform into two decoupled S3 buckets with isolated lifecycles. One acts as the Immutable RAG Source for Bedrock, and the other acts as a Structured Telemetry Lake for analytics.
## 🗂️ Bucket A: corporate-ba-academy-retrieval-storage
This bucket houses your curriculum files, instructions, and standard frameworks. It acts as the sync source for Amazon Bedrock Knowledge Bases.

corporate-ba-academy-retrieval-storage/
├── core-curriculum/
│   ├── module-01-foundational-literacy/
│   │   ├── lesson-1-1-neural-networks.pdf
│   │   └── lesson-1-2-anatomy-of-hallucination.pdf
│   ├── module-02-advanced-prompting/
│   └── [modules-03-through-07]/
├── frameworks/
│   ├── nist-ai-rmf-1.0.pdf
│   └── togaf-standard-adm-v10.pdf
└── evaluation-assets/
    ├── instructor-manual/
    │   └── instructor_evaluation_guide.md
    └── week-05-red-team-audit/
        ├── master_grading_key.md
        └── student_market_brief_template.md

## 🗂️ Bucket B: corporate-ba-academy-telemetry-lake
This bucket catches raw student JSON logs stream-written by Kinesis Firehose. It partitions data by track, tenant, and date (YYYY/MM/DD) to keep Athena queries fast and cost-effective.

corporate-ba-academy-telemetry-lake/
├── track=initial-upskilling/
│   └── student_id=EMP001/
│       └── year=2026/
│           └── month=09/
│               └── day=15/
│                   └── telemetylog_20260915_082210.parquet.gz
└── track=elite-togaf-fellowship/
    └── cohort_id=cohort-alpha/
        └── year=2026/
            └── month=10/
                └── day=01/
                    └── cohortlog_20261001_143000.parquet.gz

------------------------------
## 🛠️ 3. Complete Infrastructure as Code (provider.tf + storage.tf)
This configuration enforces serverless primitives, blocks public access explicitly at the API layer, defines native S3 managed encryption keys (SSE-KMS), and implements lifecycle transitions to Glacier to control cold storage costs.

# provider.tf
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
      Environment       = "Production-DataPlatform"
      Project           = "BA-AI-Academy"
      CostCenter        = "DataOps-770"
      ManagedBy         = "Terraform"
      DataSymmetryClass = "Restricted"
    }
  }
}

# storage.tf
# -- KMS Customer Managed Key for Enterprise Encryption at Rest --
resource "aws_kms_key" "data_lake_key" {
  description             = "KMS Key for encryption of BA Academy Retrieval and Telemetry storage layers"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}

# ──────────────────────────────────────────────────────────
# 1. RETRIEVAL STORAGE LAYER (RAG INPUT GATEWAY)
# ──────────────────────────────────────────────────────────
resource "aws_s3_bucket" "retrieval_bucket" {
  bucket        = "corporate-ba-academy-retrieval-storage"
  force_destroy = false
}

resource "aws_s3_bucket_public_access_block" "block_retrieval_public" {
  bucket                  = aws_s3_bucket.retrieval_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "retrieval_crypto" {
  bucket = aws_s3_bucket.retrieval_bucket.id
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.data_lake_key.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

# ──────────────────────────────────────────────────────────
# 2. TELEMETRY STREAM STORAGE LAYER (DATA LAKE)
# ──────────────────────────────────────────────────────────
resource "aws_s3_bucket" "telemetry_bucket" {
  bucket        = "corporate-ba-academy-telemetry-lake"
  force_destroy = false
}

resource "aws_s3_bucket_public_access_block" "block_telemetry_public" {
  bucket                  = aws_s3_bucket.telemetry_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "telemetry_crypto" {
  bucket = aws_s3_bucket.telemetry_bucket.id
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.data_lake_key.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

# S3 Intelligent-Tiering / Lifecycle Management rules to control cold-data costs
resource "aws_s3_bucket_lifecycle_configuration" "telemetry_lifecycle" {
  bucket = aws_s3_bucket.telemetry_bucket.id

  rule {
    id     = "archive-old-telemetry-streams"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "GLACIER_IR" # Instant Retrieval for historical HR audits
    }

    expiration {
      days = 365 # 1 year retention policy for corporate data logs
    }
  }
}

# ──────────────────────────────────────────────────────────
# OUTPUT DATA PIPE VALUES
# ──────────────────────────────────────────────────────────
output "s3_retrieval_arn" {
  value       = aws_s3_bucket.retrieval_bucket.arn
  description = "Target ARN for feeding Bedrock Knowledge Base synchronization engines."
}

output "s3_telemetry_arn" {
  value       = aws_s3_bucket.telemetry_bucket.arn
  description = "Target ARN to attach to Kinesis Firehose delivery configuration models."
}

------------------------------
## 👁️ 4. Data Engineer Pipeline Commentary

* Decoupled Ingress Buffer: Running API Gateway straight to Lambda works fine for low volume, but for high-concurrency token processing, routing incoming metrics asynchronously into an Amazon Kinesis Data Stream prevents backend Lambda invocation spikes from dropping student shift summaries.
* Parquet + Gzip Compression: Kinesis Firehose handles on-the-fly transformations from JSON to compressed Apache Parquet. This reduces the data footprint by up to 80% and ensures that when your manager analytics dashboard runs an Amazon Athena query (SELECT AVG(weighted_daily_score) FROM...), it only scans the specific targeted column blocks rather than reading full text files. This keeps query costs close to zero.
* Intelligent KMS Boundary: The data lake uses a single, isolated Customer Managed KMS Key with rotation turned on. This sets up an audit boundary: even if a system role accidentally leaves an S3 endpoint open, the data cannot be read without specific decryption clearance on the KMS key resource policy.

Since you build pipelines for a living, where should we take this design next? If you want to dive deeper, we can:

* Write the Kinesis Firehose Transformation Lambda script to parse raw JSON into Parquet formats.
* Create the Amazon Athena / AWS Glue Catalog schema DDL definitions to query the telemetry lake directly.
* Map out the Amazon Bedrock OpenSearch Serverless vector index field configurations for the RAG step.


