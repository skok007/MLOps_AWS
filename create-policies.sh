#!/bin/bash

# create-policies.sh
# This script creates specific IAM policies for each required AWS service.
# It replaces the overly permissive AdministratorAccess policy with more
# restrictive policies that only grant the necessary permissions.
#
# Usage:
#   ./create-policies.sh
#
# Prerequisites:
#   - AWS CLI installed and configured with appropriate credentials
#   - Appropriate permissions to create IAM policies

# Get the AWS account ID dynamically if not provided
if [ -z "$AWS_ACCOUNT_ID" ]; then
  echo "AWS_ACCOUNT_ID not set. Attempting to retrieve it automatically..."
  AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
  if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to retrieve AWS account ID automatically."
    echo "Please set the AWS_ACCOUNT_ID environment variable manually."
    exit 1
  fi
  echo "✅ Retrieved AWS account ID: $AWS_ACCOUNT_ID"
fi

# Create Bedrock policy
# This policy allows access to Bedrock models.
echo "Creating Bedrock policy..."
cat <<EOF > bedrock-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:ListFoundationModels",
        "bedrock:ListCustomModels"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam create-policy \
  --policy-name BedrockAccessPolicy \
  --policy-document file://bedrock-policy.json

# Create ECR policy
# This policy allows access to Elastic Container Registry.
echo "Creating ECR policy..."
cat <<EOF > ecr-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:GetRepositoryPolicy",
        "ecr:DescribeRepositories",
        "ecr:ListImages",
        "ecr:DescribeImages",
        "ecr:BatchGetImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:PutImage"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam create-policy \
  --policy-name ECRAccessPolicy \
  --policy-document file://ecr-policy.json

# Create ECS policy
# This policy allows access to Elastic Container Service.
echo "Creating ECS policy..."
cat <<EOF > ecs-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecs:CreateCluster",
        "ecs:DeleteCluster",
        "ecs:DescribeClusters",
        "ecs:ListClusters",
        "ecs:CreateService",
        "ecs:DeleteService",
        "ecs:DescribeServices",
        "ecs:ListServices",
        "ecs:UpdateService",
        "ecs:RegisterTaskDefinition",
        "ecs:DeregisterTaskDefinition",
        "ecs:DescribeTaskDefinition",
        "ecs:ListTaskDefinitions",
        "ecs:RunTask",
        "ecs:StopTask",
        "ecs:DescribeTasks",
        "ecs:ListTasks"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam create-policy \
  --policy-name ECSAccessPolicy \
  --policy-document file://ecs-policy.json

# Create EC2 policy
# This policy allows access to Elastic Compute Cloud.
echo "Creating EC2 policy..."
cat <<EOF > ec2-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeInstanceStatus",
        "ec2:DescribeInstanceTypes",
        "ec2:DescribeImages",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcs",
        "ec2:DescribeKeyPairs",
        "ec2:DescribeTags"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam create-policy \
  --policy-name EC2AccessPolicy \
  --policy-document file://ec2-policy.json

# Create CloudWatch policy
# This policy allows access to CloudWatch for monitoring and logging.
echo "Creating CloudWatch policy..."
cat <<EOF > cloudwatch-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetMetricData",
        "cloudwatch:ListMetrics",
        "cloudwatch:PutMetricData",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam create-policy \
  --policy-name CloudWatchAccessPolicy \
  --policy-document file://cloudwatch-policy.json

# Create CloudFormation policy
# This policy allows access to CloudFormation for infrastructure as code.
echo "Creating CloudFormation policy..."
cat <<EOF > cloudformation-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:CreateStack",
        "cloudformation:DeleteStack",
        "cloudformation:DescribeStacks",
        "cloudformation:ListStacks",
        "cloudformation:UpdateStack",
        "cloudformation:ValidateTemplate"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam create-policy \
  --policy-name CloudFormationAccessPolicy \
  --policy-document file://cloudformation-policy.json

# Create S3 policy
# This policy allows access to Simple Storage Service.
echo "Creating S3 policy..."
cat <<EOF > s3-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:DeleteBucket",
        "s3:ListBuckets",
        "s3:GetBucketLocation",
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListObjects",
        "s3:ListObjectsV2"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam create-policy \
  --policy-name S3AccessPolicy \
  --policy-document file://s3-policy.json

# Create Lambda policy
# This policy allows access to AWS Lambda for serverless functions.
echo "Creating Lambda policy..."
cat <<EOF > lambda-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:DeleteFunction",
        "lambda:GetFunction",
        "lambda:ListFunctions",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:InvokeFunction"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam create-policy \
  --policy-name LambdaAccessPolicy \
  --policy-document file://lambda-policy.json

echo "✅ All policies created successfully." 