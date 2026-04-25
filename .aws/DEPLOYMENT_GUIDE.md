# AWS ECS Fargate Deployment Guide

Complete guide for deploying Energy RAG Platform to AWS ECS Fargate with GitHub Actions CI/CD.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [AWS Setup](#aws-setup)
3. [GitHub Secrets Configuration](#github-secrets-configuration)
4. [ECS Cluster Setup](#ecs-cluster-setup)
5. [Deployment Process](#deployment-process)
6. [Monitoring & Logs](#monitoring--logs)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

- AWS Account with appropriate IAM permissions
- GitHub repository with this code
- Docker installed locally (for testing)
- AWS CLI v2 installed
- `jq` for JSON parsing (optional)

## AWS Setup

### 1. Create ECR Repository

```bash
# Create ECR repository for the Docker image
aws ecr create-repository \
    --repository-name energy-rag-platform \
    --region us-east-1 \
    --image-scan-on-push \
    --encryption-configuration encryptionType=AES

# Output:
# {
#   "repository": {
#     "repositoryUri": "ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/energy-rag-platform"
#   }
# }
```

### 2. Create IAM Roles

#### ECS Task Execution Role
```bash
# Create trust policy
cat > trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
aws iam create-role \
    --role-name ecsTaskExecutionRole \
    --assume-role-policy-document file://trust-policy.json

# Attach policy for ECR and CloudWatch
aws iam attach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Attach policy for Secrets Manager
aws iam attach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite
```

#### ECS Task Role
```bash
# Create role
aws iam create-role \
    --role-name ecsTaskRole \
    --assume-role-policy-document file://trust-policy.json

# Create and attach custom policy
cat > task-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:us-east-1:*:log-group:/ecs/energy-rag-*"
    }
  ]
}
EOF

aws iam put-role-policy \
    --role-name ecsTaskRole \
    --policy-name energy-rag-task-policy \
    --policy-document file://task-policy.json
```

### 3. Create CloudWatch Log Groups

```bash
# Development
aws logs create-log-group \
    --log-group-name /ecs/energy-rag-dev \
    --region us-east-1

aws logs put-retention-policy \
    --log-group-name /ecs/energy-rag-dev \
    --retention-in-days 7

# Production
aws logs create-log-group \
    --log-group-name /ecs/energy-rag-prod \
    --region us-east-1

aws logs put-retention-policy \
    --log-group-name /ecs/energy-rag-prod \
    --retention-in-days 30
```

### 4. Store Secrets in AWS Secrets Manager

```bash
# Store Groq API key for development
aws secretsmanager create-secret \
    --name groq-api-key-dev \
    --description "Groq API Key for Development" \
    --secret-string "YOUR_GROQ_API_KEY" \
    --region us-east-1

# Store Groq API key for production
aws secretsmanager create-secret \
    --name groq-api-key-prod \
    --description "Groq API Key for Production" \
    --secret-string "YOUR_GROQ_API_KEY" \
    --region us-east-1
```

### 5. Create VPC and Networking

```bash
# Create VPC
VPC_ID=$(aws ec2 create-vpc \
    --cidr-block 10.0.0.0/16 \
    --region us-east-1 \
    --query 'Vpc.VpcId' \
    --output text)

# Create subnets
SUBNET_1=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.1.0/24 \
    --availability-zone us-east-1a \
    --region us-east-1 \
    --query 'Subnet.SubnetId' \
    --output text)

SUBNET_2=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.2.0/24 \
    --availability-zone us-east-1b \
    --region us-east-1 \
    --query 'Subnet.SubnetId' \
    --output text)

# Create security group
SG_ID=$(aws ec2 create-security-group \
    --group-name energy-rag-sg \
    --description "Security group for Energy RAG Platform" \
    --vpc-id $VPC_ID \
    --region us-east-1 \
    --query 'GroupId' \
    --output text)

# Allow inbound traffic on port 8000
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 8000 \
    --cidr 0.0.0.0/0 \
    --region us-east-1

echo "VPC_ID=$VPC_ID"
echo "SUBNET_1=$SUBNET_1"
echo "SUBNET_2=$SUBNET_2"
echo "SG_ID=$SG_ID"
```

## ECS Cluster Setup

### 1. Create ECS Clusters

```bash
# Development cluster
aws ecs create-cluster \
    --cluster-name energy-rag-cluster-dev \
    --capacity-providers FARGATE FARGATE_SPOT \
    --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1,base=1 \
    --region us-east-1

# Production cluster
aws ecs create-cluster \
    --cluster-name energy-rag-cluster-prod \
    --capacity-providers FARGATE \
    --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1,base=2 \
    --region us-east-1
```

### 2. Register Task Definitions

```bash
# Replace placeholders in task definitions
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

sed -i "s/ACCOUNT_ID/$ACCOUNT_ID/g" .aws/task-definition-dev.json
sed -i "s/ACCOUNT_ID/$ACCOUNT_ID/g" .aws/task-definition-prod.json

# Register development task definition
aws ecs register-task-definition \
    --cli-input-json file://.aws/task-definition-dev.json \
    --region us-east-1

# Register production task definition
aws ecs register-task-definition \
    --cli-input-json file://.aws/task-definition-prod.json \
    --region us-east-1
```

### 3. Create Load Balancers (Optional but Recommended)

```bash
# Create Application Load Balancer
ALB_ARN=$(aws elbv2 create-load-balancer \
    --name energy-rag-alb \
    --subnets $SUBNET_1 $SUBNET_2 \
    --security-groups $SG_ID \
    --scheme internet-facing \
    --type application \
    --region us-east-1 \
    --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text)

# Create target groups
TG_DEV_ARN=$(aws elbv2 create-target-group \
    --name energy-rag-tg-dev \
    --protocol HTTP \
    --port 8000 \
    --vpc-id $VPC_ID \
    --target-type ip \
    --health-check-protocol HTTP \
    --health-check-path /health \
    --health-check-interval-seconds 30 \
    --health-check-timeout-seconds 5 \
    --healthy-threshold-count 3 \
    --unhealthy-threshold-count 3 \
    --region us-east-1 \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text)

echo "ALB_ARN=$ALB_ARN"
echo "TG_DEV_ARN=$TG_DEV_ARN"
```

### 4. Create ECS Services

```bash
# Development service
aws ecs create-service \
    --cluster energy-rag-cluster-dev \
    --service-name energy-rag-service-dev \
    --task-definition energy-rag-task:1 \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_1,$SUBNET_2],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
    --region us-east-1

# Production service with auto-scaling
aws ecs create-service \
    --cluster energy-rag-cluster-prod \
    --service-name energy-rag-service-prod \
    --task-definition energy-rag-task:1 \
    --desired-count 3 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_1,$SUBNET_2],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
    --region us-east-1
```

## GitHub Secrets Configuration

Add the following secrets to your GitHub repository (Settings → Secrets and variables → Actions):

### Required Secrets

1. **AWS_ACCESS_KEY_ID**
   - Value: Your AWS access key ID
   - Scope: All environments

2. **AWS_SECRET_ACCESS_KEY**
   - Value: Your AWS secret access key
   - Scope: All environments

3. **GROQ_API_KEY**
   - Value: Your Groq API key
   - Scope: All environments

4. **SLACK_WEBHOOK** (Optional)
   - Value: Your Slack webhook URL for notifications
   - Scope: All environments

### Setting Secrets via CLI

```bash
# Create GitHub CLI auth token first
gh auth login

# Set secrets
gh secret set AWS_ACCESS_KEY_ID --body "your-access-key"
gh secret set AWS_SECRET_ACCESS_KEY --body "your-secret-key"
gh secret set GROQ_API_KEY --body "your-groq-key"
gh secret set SLACK_WEBHOOK --body "https://hooks.slack.com/..."
```

## Deployment Process

### Manual Deployment

```bash
# Push to develop branch for dev deployment
git push origin develop

# Push to main branch for production deployment
git push origin main

# GitHub Actions will automatically:
# 1. Run tests (92+ tests)
# 2. Run security scans
# 3. Build Docker image
# 4. Push to ECR
# 5. Deploy to ECS Fargate
```

### Deployment Flow

```
Push to GitHub
    ↓
GitHub Actions Triggered
    ├─ Run Tests (pytest)
    ├─ Security Scanning (Trivy, TruffleHog)
    ├─ Build Docker Image
    ├─ Push to AWS ECR
    ├─ Scan Image
    ├─ Deploy to ECS Dev (if develop branch)
    └─ Deploy to ECS Prod (if main branch)
        ├─ Update task definition
        ├─ Update ECS service
        ├─ Wait for stability
        └─ Health check
```

## Monitoring & Logs

### View Logs

```bash
# Development logs
aws logs tail /ecs/energy-rag-dev --follow

# Production logs
aws logs tail /ecs/energy-rag-prod --follow

# Specific task logs
aws logs tail /ecs/energy-rag-prod --follow --log-stream-names "ecs/energy-rag-container/TASK_ID"
```

### Check Service Status

```bash
# Development
aws ecs describe-services \
    --cluster energy-rag-cluster-dev \
    --services energy-rag-service-dev

# Production
aws ecs describe-services \
    --cluster energy-rag-cluster-prod \
    --services energy-rag-service-prod
```

### Check Running Tasks

```bash
# Development
aws ecs list-tasks --cluster energy-rag-cluster-dev

# Production
aws ecs list-tasks --cluster energy-rag-cluster-prod

# Get task details
aws ecs describe-tasks \
    --cluster energy-rag-cluster-prod \
    --tasks arn:aws:ecs:us-east-1:ACCOUNT_ID:task/energy-rag-cluster-prod/TASK_ID
```

## Auto-Scaling Setup

```bash
# Create Auto Scaling Target for Production
aws application-autoscaling register-scalable-target \
    --service-namespace ecs \
    --resource-id service/energy-rag-cluster-prod/energy-rag-service-prod \
    --scalable-dimension ecs:service:DesiredCount \
    --min-capacity 2 \
    --max-capacity 10

# Create scaling policy (CPU)
aws application-autoscaling put-scaling-policy \
    --policy-name energy-rag-cpu-scaling \
    --service-namespace ecs \
    --resource-id service/energy-rag-cluster-prod/energy-rag-service-prod \
    --scalable-dimension ecs:service:DesiredCount \
    --policy-type TargetTrackingScaling \
    --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

### scaling-policy.json
```json
{
  "TargetValue": 70.0,
  "PredefinedMetricSpecification": {
    "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
  },
  "ScaleOutCooldown": 60,
  "ScaleInCooldown": 300
}
```

## Troubleshooting

### Tasks Not Starting

```bash
# Check task logs
aws logs tail /ecs/energy-rag-prod --follow

# Check task stop reason
aws ecs describe-tasks \
    --cluster energy-rag-cluster-prod \
    --tasks TASK_ARN \
    --query 'tasks[0].stoppedReason'
```

### Common Issues

1. **Image not found in ECR**
   - Check GitHub Actions build log
   - Verify ECR repository exists
   - Check AWS credentials in GitHub Secrets

2. **Task fails health check**
   - Verify `/health` endpoint is accessible
   - Check CloudWatch logs
   - Verify environment variables are set

3. **Service cannot reach task**
   - Check security group rules (port 8000 open)
   - Verify subnet configuration
   - Check VPC routing

## Cleanup

```bash
# Delete service (keeps task running until stopped)
aws ecs delete-service \
    --cluster energy-rag-cluster-prod \
    --service energy-rag-service-prod \
    --force

# Stop all tasks
aws ecs update-service \
    --cluster energy-rag-cluster-prod \
    --service energy-rag-service-prod \
    --desired-count 0

# Delete cluster
aws ecs delete-cluster \
    --cluster energy-rag-cluster-prod

# Delete ECR repository
aws ecr delete-repository \
    --repository-name energy-rag-platform \
    --force
```

## Cost Optimization

### Development
- Use FARGATE_SPOT for cost savings (~70% cheaper)
- Reduce desired count to 1
- Set lower CPU/memory (512/1024)

### Production
- Use FARGATE for reliability
- Set desired count to 3+ for HA
- Use auto-scaling to handle peaks
- Consider Reserved Capacity for savings

## Next Steps

1. ✅ Create AWS resources using commands above
2. ✅ Configure GitHub Secrets
3. ✅ Push code to repository
4. ✅ Monitor first deployment in GitHub Actions
5. ✅ Set up CloudWatch alarms
6. ✅ Configure SNS notifications
7. ✅ Test rollback procedure
