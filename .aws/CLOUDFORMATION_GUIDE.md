# CloudFormation Deployment Guide

Infrastructure as Code deployment for Energy RAG Platform using AWS CloudFormation.

## Overview

Instead of running 20+ manual AWS CLI commands, this CloudFormation template creates **all** AWS infrastructure in 3-5 minutes:

- ✅ VPC with 2 public subnets
- ✅ Internet Gateway
- ✅ Route tables & routing
- ✅ Security Groups
- ✅ ECR Repository (Docker registry)
- ✅ IAM Roles (execution + task)
- ✅ CloudWatch Log Groups (dev + prod)
- ✅ ECS Clusters (dev + prod)
- ✅ ECS Task Definitions (dev + prod)
- ✅ ECS Services (dev + prod)
- ✅ Auto Scaling (production)

## Prerequisites

```bash
# Check AWS CLI installed
aws --version

# Check jq installed (JSON processor)
jq --version

# Configure AWS credentials
aws configure

# Verify credentials work
aws sts get-caller-identity
```

If any are missing:
```bash
# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Install jq (macOS)
brew install jq

# Install jq (Linux)
sudo apt-get install jq

# Install jq (Windows)
choco install jq
```

## Quick Start (3 steps)

### Step 1: Deploy CloudFormation Stack

```bash
# Make deploy script executable
chmod +x .aws/deploy.sh

# Deploy (uses defaults: energy-rag, us-east-1)
./.aws/deploy.sh

# Or with custom parameters
./.aws/deploy.sh my-rag-project us-west-2
```

**This will:**
- Create all VPC networking
- Create ECR repository
- Create ECS clusters & services
- Create IAM roles
- Create CloudWatch log groups
- Wait for stack to complete (3-5 minutes)
- Display all resource IDs (save these!)

### Step 2: Store Secrets in Secrets Manager

```bash
# Development
aws secretsmanager create-secret \
  --name groq-api-key-dev \
  --secret-string "your-groq-api-key-here" \
  --region us-east-1

# Production
aws secretsmanager create-secret \
  --name groq-api-key-prod \
  --secret-string "your-groq-api-key-here" \
  --region us-east-1

# Verify
aws secretsmanager list-secrets --region us-east-1
```

### Step 3: Create GitHub Actions IAM User

```bash
# Create user
aws iam create-user --user-name github-actions-deployment

# Create access key
aws iam create-access-key --user-name github-actions-deployment

# Attach policy (ECR + ECS permissions)
aws iam attach-user-policy \
  --user-name github-actions-deployment \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser

aws iam attach-user-policy \
  --user-name github-actions-deployment \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Attach inline policy for ECS service updates
cat > /tmp/github-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecs:DescribeServices",
        "ecs:DescribeTaskDefinition",
        "ecs:DescribeTasks",
        "ecs:ListTasks",
        "ecs:RegisterTaskDefinition",
        "ecs:UpdateService"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:PassRole"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam put-user-policy \
  --user-name github-actions-deployment \
  --policy-name github-actions-policy \
  --policy-document file:///tmp/github-policy.json
```

**Copy the Access Key ID & Secret Access Key to GitHub Secrets**

## Detailed Steps

### 1. Verify CloudFormation Template

```bash
# Validate template syntax
aws cloudformation validate-template \
  --template-body file://.aws/template.yml \
  --region us-east-1

# Expected: Returns template description and parameters
```

### 2. Review Template Parameters

```bash
# View all customizable parameters
cat > /tmp/params.json <<'EOF'
[
  {
    "ParameterKey": "EnvironmentName",
    "ParameterValue": "energy-rag"
  },
  {
    "ParameterKey": "VpcCIDR",
    "ParameterValue": "10.0.0.0/16"
  },
  {
    "ParameterKey": "PublicSubnet1CIDR",
    "ParameterValue": "10.0.1.0/24"
  },
  {
    "ParameterKey": "PublicSubnet2CIDR",
    "ParameterValue": "10.0.2.0/24"
  },
  {
    "ParameterKey": "ContainerPort",
    "ParameterValue": "8000"
  },
  {
    "ParameterKey": "DesiredCountDev",
    "ParameterValue": "2"
  },
  {
    "ParameterKey": "DesiredCountProd",
    "ParameterValue": "3"
  }
]
EOF

cat /tmp/params.json
```

### 3. Deploy the Stack

#### Option A: Using the Deploy Script (Easiest)

```bash
cd .aws
chmod +x deploy.sh
./deploy.sh energy-rag us-east-1
```

#### Option B: Using AWS CLI Directly

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="us-east-1"
STACK_NAME="energy-rag-stack"

# Create stack
aws cloudformation create-stack \
  --stack-name "$STACK_NAME" \
  --template-body file://.aws/template.yml \
  --parameters \
    ParameterKey=EnvironmentName,ParameterValue=energy-rag \
    ParameterKey=VpcCIDR,ParameterValue=10.0.0.0/16 \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$REGION"

# Wait for stack creation
aws cloudformation wait stack-create-complete \
  --stack-name "$STACK_NAME" \
  --region "$REGION"

# Get outputs
aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query 'Stacks[0].Outputs' \
  --output table
```

### 4. Monitor Stack Deployment

```bash
# Watch stack events in real-time
watch -n 5 'aws cloudformation describe-stack-events \
  --stack-name energy-rag-stack \
  --query "StackEvents[0:10]" \
  --output table'

# Or get final status
aws cloudformation describe-stacks \
  --stack-name energy-rag-stack \
  --query "Stacks[0].{Status: StackStatus, CreatedTime: CreationTime}"
```

### 5. Save Stack Outputs

```bash
# Get all outputs as JSON
aws cloudformation describe-stacks \
  --stack-name energy-rag-stack \
  --query 'Stacks[0].Outputs' > stack-outputs.json

cat stack-outputs.json

# Example outputs:
# VPCId: vpc-xxxxx
# ECRRepositoryUri: 123456789012.dkr.ecr.us-east-1.amazonaws.com/energy-rag-platform
# ECSClusterDevName: energy-rag-cluster-dev
# ECSServiceDevName: energy-rag-service-dev
# LogGroupDevName: /ecs/energy-rag-dev
# LogGroupProdName: /ecs/energy-rag-prod
```

## Manual Deployment (Alternative)

If you prefer to use the AWS Console instead of CLI:

1. **Go to CloudFormation Console**
   - URL: https://console.aws.amazon.com/cloudformation/

2. **Click "Create Stack"**

3. **Upload Template**
   - Select "Upload a template file"
   - Choose `.aws/template.yml`
   - Click "Next"

4. **Specify Stack Details**
   - Stack Name: `energy-rag-stack`
   - EnvironmentName: `energy-rag`
   - Leave other parameters as default
   - Click "Next"

5. **Configure Stack Options**
   - Leave defaults
   - Click "Next"

6. **Review and Create**
   - Check ✓ "I acknowledge that AWS CloudFormation might create IAM resources"
   - Click "Create Stack"

7. **Monitor**
   - Watch Events tab
   - Wait for CREATE_COMPLETE status (3-5 minutes)
   - View Outputs tab for resource IDs

## Verify Deployment

```bash
# Check VPC created
aws ec2 describe-vpcs --filters "Name=cidr,Values=10.0.0.0/16"

# Check ECR repository
aws ecr describe-repositories \
  --query 'repositories[0].[repositoryUri, imageScanningConfiguration.scanOnPush]'

# Check ECS clusters
aws ecs list-clusters --query 'clusterArns'

# Check ECS services
aws ecs list-services --cluster energy-rag-cluster-dev
aws ecs list-services --cluster energy-rag-cluster-prod

# Check CloudWatch log groups
aws logs describe-log-groups \
  --query 'logGroups[*].[logGroupName]'

# Check IAM roles created
aws iam list-roles --query "Roles[?contains(RoleName, 'energy-rag')]"
```

## Configure GitHub Actions

### 1. Get Stack Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name energy-rag-stack \
  --query 'Stacks[0].Outputs[?OutputKey==`ECRRepositoryUri`].OutputValue' \
  --output text

# Copy this for ci.yaml: ECRRepositoryUri
```

### 2. Update ci.yaml (if needed)

The `ci.yaml` already has placeholders. Update if you used different values:

```yaml
env:
  AWS_REGION: us-east-1        # Change if different
  ECR_REPOSITORY: energy-rag-platform  # Change if different
  ECS_SERVICE: energy-rag-service-dev
  ECS_CLUSTER: energy-rag-cluster-dev
```

### 3. Add GitHub Secrets

```bash
# From the IAM user created above
gh secret set AWS_ACCESS_KEY_ID --body "AKIA..."
gh secret set AWS_SECRET_ACCESS_KEY --body "wJal..."
gh secret set GROQ_API_KEY --body "gsk_..."
```

## Update Stack (if needed)

```bash
# To update stack parameters
aws cloudformation update-stack \
  --stack-name energy-rag-stack \
  --template-body file://.aws/template.yml \
  --parameters \
    ParameterKey=DesiredCountProd,ParameterValue=5 \
  --capabilities CAPABILITY_NAMED_IAM

# Wait for update
aws cloudformation wait stack-update-complete \
  --stack-name energy-rag-stack
```

## Troubleshooting

### Stack Creation Failed

```bash
# Check stack events for error
aws cloudformation describe-stack-events \
  --stack-name energy-rag-stack \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]' \
  --output table

# Common issues:
# - IAM role already exists
# - VPC CIDR conflict
# - Service quota exceeded
```

### Rollback on Failure

CloudFormation automatically rolls back on failure. To manually rollback:

```bash
aws cloudformation cancel-update-stack \
  --stack-name energy-rag-stack
```

### Delete Stack (Cleanup)

```bash
# Delete ECR images first (or they'll block deletion)
aws ecr batch-delete-image \
  --repository-name energy-rag-platform \
  --image-ids imageTag=latest

# Delete stack
aws cloudformation delete-stack \
  --stack-name energy-rag-stack

# Wait for deletion
aws cloudformation wait stack-delete-complete \
  --stack-name energy-rag-stack

# Verify deletion
aws cloudformation describe-stacks \
  --stack-name energy-rag-stack 2>&1 | grep "does not exist"
```

## Cost Estimation

### What CloudFormation Creates

| Resource | Count | Estimated Cost |
|----------|-------|-----------------|
| VPC | 1 | Free |
| Subnets | 2 | Free |
| Internet Gateway | 1 | Free |
| Security Group | 1 | Free |
| ECR Repository | 1 | ~$0.10/GB storage |
| ECS Cluster | 2 | Free |
| ECS Task Definition | 2 | Free |
| ECS Service | 2 | Free |
| CloudWatch Log Group | 2 | ~$0.50/month (dev), ~$1/month (prod) |
| CloudWatch Logs | Usage | ~$0.50/GB ingested |
| IAM Roles | 2 | Free |
| **Total Infrastructure** | | ~**$10-50/month** |
| **ECS Fargate (compute)** | | ~**$40-70/month** (separate from template) |

## Next Steps

1. ✅ Run deploy script
2. ✅ Create Secrets Manager entries
3. ✅ Create GitHub Actions IAM user
4. ✅ Add GitHub Secrets
5. ✅ Push code to GitHub
6. ✅ Monitor first deployment in GitHub Actions
7. ✅ Check CloudWatch logs

## Useful Commands Reference

```bash
# View stack status
aws cloudformation describe-stacks --stack-name energy-rag-stack

# View stack outputs
aws cloudformation describe-stacks --stack-name energy-rag-stack \
  --query 'Stacks[0].Outputs'

# View recent events
aws cloudformation describe-stack-events --stack-name energy-rag-stack \
  --query 'StackEvents[0:10]'

# Update stack
aws cloudformation update-stack --stack-name energy-rag-stack \
  --template-body file://template.yml --capabilities CAPABILITY_NAMED_IAM

# List all stacks
aws cloudformation list-stacks --query 'StackSummaries[?StackStatus!=`DELETE_COMPLETE`]'

# Get template
aws cloudformation get-template --stack-name energy-rag-stack

# Validate template
aws cloudformation validate-template --template-body file://template.yml
```

---

**Time to Deploy**: 5-10 minutes (mostly waiting for AWS to create resources)

**Status**: Ready to use! 🚀
