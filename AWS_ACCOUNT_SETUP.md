# AWS Account Setup Guide - Your Account

**Account Details:**
- Account ID: `412381749261`
- Account Name: `llmops` (asker313)
- Preferred Region: `us-east-1` (N. Virginia)

---

## 🚀 Quick Setup Commands (Copy & Paste)

### Step 1: Deploy CloudFormation Stack (5 minutes)

```bash
# Set your region
export AWS_REGION="us-east-1"
export ACCOUNT_ID="412381749261"
export STACK_NAME="energy-rag-stack"

# Navigate to project
cd /path/to/RAG_LLMOPS

# Create the stack
aws cloudformation create-stack \
  --stack-name "$STACK_NAME" \
  --template-body file://.aws/template.yml \
  --parameters ParameterKey=EnvironmentName,ParameterValue=energy-rag \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$AWS_REGION"

# Wait for completion (3-5 minutes)
aws cloudformation wait stack-create-complete \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION"

# Get the outputs (save these!)
aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION" \
  --query 'Stacks[0].Outputs' \
  --output table
```

**Expected Outputs:**
```
ECRRepositoryUri:        412381749261.dkr.ecr.us-east-1.amazonaws.com/energy-rag-platform
ECSClusterDevName:       energy-rag-cluster-dev
ECSClusterProdName:      energy-rag-cluster-prod
ECSServiceDevName:       energy-rag-service-dev
ECSServiceProdName:      energy-rag-service-prod
LogGroupDevName:         /ecs/energy-rag-dev
LogGroupProdName:        /ecs/energy-rag-prod
```

---

### Step 2: Create Secrets (2 minutes)

Get your Groq API Key from: https://console.groq.com/

```bash
export GROQ_API_KEY="gsk_YOUR_API_KEY_HERE"
export AWS_REGION="us-east-1"

# Development secret
aws secretsmanager create-secret \
  --name groq-api-key-dev \
  --description "Groq API Key for Development" \
  --secret-string "$GROQ_API_KEY" \
  --region "$AWS_REGION"

# Production secret
aws secretsmanager create-secret \
  --name groq-api-key-prod \
  --description "Groq API Key for Production" \
  --secret-string "$GROQ_API_KEY" \
  --region "$AWS_REGION"

# Verify
aws secretsmanager list-secrets \
  --region "$AWS_REGION" \
  --query 'SecretList[*].[Name, ARN]' \
  --output table
```

---

### Step 3: Create IAM User for GitHub Actions (3 minutes)

```bash
export ACCOUNT_ID="412381749261"
export AWS_REGION="us-east-1"

# Create user
aws iam create-user --user-name github-actions-deployment

# Create access key (SAVE THIS!)
aws iam create-access-key --user-name github-actions-deployment \
  --query 'AccessKey.[AccessKeyId, SecretAccessKey]' \
  --output text

# Attach permissions
aws iam attach-user-policy \
  --user-name github-actions-deployment \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser

aws iam attach-user-policy \
  --user-name github-actions-deployment \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Custom policy for ECS updates
cat > /tmp/github-ecs-policy.json <<'EOF'
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
      "Resource": [
        "arn:aws:iam::412381749261:role/energy-rag-ecs-task-execution-role",
        "arn:aws:iam::412381749261:role/energy-rag-ecs-task-role"
      ]
    }
  ]
}
EOF

aws iam put-user-policy \
  --user-name github-actions-deployment \
  --policy-name github-actions-ecs-policy \
  --policy-document file:///tmp/github-ecs-policy.json
```

**Save these credentials:**
```
AWS_ACCESS_KEY_ID: AKIA...
AWS_SECRET_ACCESS_KEY: ...
```

---

### Step 4: Configure GitHub Secrets (2 minutes)

```bash
# Use the credentials from Step 3
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="..."
export GROQ_API_KEY="gsk_..."

# Add GitHub secrets
gh secret set AWS_ACCESS_KEY_ID --body "$AWS_ACCESS_KEY_ID"
gh secret set AWS_SECRET_ACCESS_KEY --body "$AWS_SECRET_ACCESS_KEY"
gh secret set GROQ_API_KEY --body "$GROQ_API_KEY"

# Verify
gh secret list
```

---

### Step 5: Push Code (2 minutes)

```bash
cd /path/to/RAG_LLMOPS

# Commit (already done)
# git add -A
# git commit -m "feat: CI/CD pipeline"

# Push to GitHub
git push origin master

# Watch deployment
gh run watch
```

---

## 🔍 Verify Everything Works

### Check CloudFormation Stack

```bash
aws cloudformation describe-stacks \
  --stack-name energy-rag-stack \
  --query 'Stacks[0].StackStatus'
```

Expected: `CREATE_COMPLETE`

### Check ECS Clusters

```bash
aws ecs list-clusters --region us-east-1
```

Expected:
```
arn:aws:ecs:us-east-1:412381749261:cluster/energy-rag-cluster-dev
arn:aws:ecs:us-east-1:412381749261:cluster/energy-rag-cluster-prod
```

### Check ECR Repository

```bash
aws ecr describe-repositories \
  --repository-names energy-rag-platform \
  --region us-east-1 \
  --query 'repositories[0].repositoryUri'
```

Expected:
```
412381749261.dkr.ecr.us-east-1.amazonaws.com/energy-rag-platform
```

### Check IAM Roles Created

```bash
aws iam list-roles \
  --query "Roles[?contains(RoleName, 'energy-rag')].[RoleName, Arn]" \
  --output table
```

Expected:
```
energy-rag-ecs-task-execution-role
energy-rag-ecs-task-role
```

### Check Secrets

```bash
aws secretsmanager list-secrets \
  --query 'SecretList[?contains(Name, `groq`)].Name' \
  --output table
```

Expected:
```
groq-api-key-dev
groq-api-key-prod
```

### Check CloudWatch Logs

```bash
aws logs describe-log-groups \
  --query 'logGroups[?contains(logGroupName, `energy-rag`)].logGroupName' \
  --output table
```

Expected:
```
/ecs/energy-rag-dev
/ecs/energy-rag-prod
```

---

## 📊 Your AWS Configuration

| Setting | Value |
|---------|-------|
| Account ID | 412381749261 |
| Account Name | llmops |
| Username | asker313 |
| Primary Region | us-east-1 (N. Virginia) |
| ECR Repository | energy-rag-platform |
| Dev Cluster | energy-rag-cluster-dev |
| Prod Cluster | energy-rag-cluster-prod |
| Dev Service | energy-rag-service-dev |
| Prod Service | energy-rag-service-prod |
| Dev Log Group | /ecs/energy-rag-dev |
| Prod Log Group | /ecs/energy-rag-prod |
| Execution Role | energy-rag-ecs-task-execution-role |
| Task Role | energy-rag-ecs-task-role |

---

## 📝 Updated CI/CD Configuration

Your `ci.yaml` is pre-configured with:

```yaml
env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: energy-rag-platform
  ECS_SERVICE: energy-rag-service
  ECS_CLUSTER: energy-rag-cluster
```

No changes needed! The template auto-detects your Account ID.

---

## 🔐 Security Checklist

- [ ] CloudFormation stack created successfully
- [ ] Secrets stored in Secrets Manager
- [ ] GitHub Actions IAM user created
- [ ] GitHub Secrets configured
- [ ] IAM roles created (2 roles)
- [ ] CloudWatch log groups created (2 groups)
- [ ] ECR repository created
- [ ] ECS clusters created (2 clusters)
- [ ] ECS services running (2 services)

---

## 🚀 Final Deployment

Once all above is done:

```bash
# Push code
git push origin master

# Watch GitHub Actions
gh run watch

# Monitor logs
aws logs tail /ecs/energy-rag-dev --follow
aws logs tail /ecs/energy-rag-prod --follow

# Check ECS status
aws ecs describe-services \
  --cluster energy-rag-cluster-dev \
  --services energy-rag-service-dev \
  --query 'services[0].[serviceName, status, runningCount, desiredCount]'
```

---

## 📞 Quick Commands Reference

**Check stack status:**
```bash
aws cloudformation describe-stacks --stack-name energy-rag-stack
```

**View outputs:**
```bash
aws cloudformation describe-stacks --stack-name energy-rag-stack \
  --query 'Stacks[0].Outputs' --output table
```

**View stack events:**
```bash
aws cloudformation describe-stack-events --stack-name energy-rag-stack \
  --query 'StackEvents[0:10]' --output table
```

**Delete stack (cleanup):**
```bash
# Delete ECR images first
aws ecr batch-delete-image --repository-name energy-rag-platform \
  --image-ids imageTag=latest

# Delete stack
aws cloudformation delete-stack --stack-name energy-rag-stack

# Wait for deletion
aws cloudformation wait stack-delete-complete --stack-name energy-rag-stack
```

---

## ✅ You're All Set!

Everything is configured for your AWS account (412381749261).

**Next Steps:**
1. Run the commands in Step 1-5 above
2. Watch it all deploy automatically
3. Push code and watch GitHub Actions run
4. See your energy RAG platform live! 🚀

---

**Account**: llmops (asker313)  
**Region**: us-east-1  
**Status**: Ready to Deploy ✅
