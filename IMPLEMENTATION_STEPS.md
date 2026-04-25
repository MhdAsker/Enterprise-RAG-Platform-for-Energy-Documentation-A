# Implementation Steps - AWS ECS Fargate & GitHub CI/CD

Step-by-step guide to get your Energy RAG Platform running on AWS with full CI/CD.

## ✅ Step 1: Verify Files Are in Place (5 min)

```bash
# Check all CI/CD files exist
ls -la .github/workflows/ci.yaml
ls -la .aws/task-definition-*.json
ls -la Dockerfile
ls -la CI_CD_*.md
```

Expected output:
- ✅ `.github/workflows/ci.yaml` (350+ lines)
- ✅ `.aws/task-definition-dev.json`
- ✅ `.aws/task-definition-prod.json`
- ✅ `.aws/DEPLOYMENT_GUIDE.md`
- ✅ `Dockerfile`
- ✅ `CI_CD_SUMMARY.md`
- ✅ `CI_CD_QUICKREF.md`

## ✅ Step 2: Set Up AWS Account (30 min)

Follow `.aws/DEPLOYMENT_GUIDE.md` sections:

1. **Create ECR Repository**
   ```bash
   aws ecr create-repository \
     --repository-name energy-rag-platform \
     --region us-east-1
   ```

2. **Create IAM Roles**
   - ecsTaskExecutionRole
   - ecsTaskRole
   - (Full commands in DEPLOYMENT_GUIDE.md)

3. **Create CloudWatch Log Groups**
   - /ecs/energy-rag-dev
   - /ecs/energy-rag-prod

4. **Store Secrets in Secrets Manager**
   - groq-api-key-dev
   - groq-api-key-prod

5. **Create VPC & Networking**
   - VPC (10.0.0.0/16)
   - Subnets
   - Security group (allow port 8000)

6. **Create ECS Clusters**
   - energy-rag-cluster-dev
   - energy-rag-cluster-prod

7. **Register Task Definitions**
   ```bash
   # Update ACCOUNT_ID in task definitions
   ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
   sed -i "s/ACCOUNT_ID/$ACCOUNT_ID/g" .aws/task-definition-dev.json
   sed -i "s/ACCOUNT_ID/$ACCOUNT_ID/g" .aws/task-definition-prod.json
   
   # Register
   aws ecs register-task-definition \
     --cli-input-json file://.aws/task-definition-dev.json
   ```

8. **Create ECS Services**
   ```bash
   # Development
   aws ecs create-service \
     --cluster energy-rag-cluster-dev \
     --service-name energy-rag-service-dev \
     --task-definition energy-rag-task:1 \
     --desired-count 2 \
     --launch-type FARGATE \
     --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-zzz],assignPublicIp=ENABLED}"
   ```

**Checkpoint**: Verify all AWS resources created:
```bash
aws ecr describe-repositories --repository-names energy-rag-platform
aws ecs describe-clusters --clusters energy-rag-cluster-dev
aws ecs describe-services --cluster energy-rag-cluster-dev --services energy-rag-service-dev
```

## ✅ Step 3: Configure GitHub Repository (15 min)

Follow `.github/GITHUB_SETUP.md` sections:

1. **Set Up Branch Protection**
   - Go to: Settings → Branches
   - Add protection for `main` branch
   - Require status checks pass
   - Require code reviews

2. **Create Environments**
   - Development: auto-deploy from develop
   - Production: auto-deploy from main (with approvals)

3. **Add GitHub Secrets**
   ```bash
   # Using GitHub CLI
   gh auth login
   
   gh secret set AWS_ACCESS_KEY_ID --body "your-access-key"
   gh secret set AWS_SECRET_ACCESS_KEY --body "your-secret-key"
   gh secret set GROQ_API_KEY --body "your-groq-key"
   gh secret set SLACK_WEBHOOK --body "your-slack-webhook"
   
   # Verify
   gh secret list
   ```

4. **Verify Workflow Permissions**
   - Settings → Actions → General
   - Enable: "Read and write permissions"
   - Enable: "Allow GitHub Actions to create pull requests"

**Checkpoint**: Verify secrets are set:
```bash
gh secret list
```

Expected:
```
AWS_ACCESS_KEY_ID       Updated 2026-04-25
AWS_SECRET_ACCESS_KEY   Updated 2026-04-25
GROQ_API_KEY            Updated 2026-04-25
SLACK_WEBHOOK           Updated 2026-04-25
```

## ✅ Step 4: Push Code to GitHub (5 min)

```bash
# Make sure all files are tracked
git status

# Add and commit
git add -A
git commit -m "feat: add complete CI/CD pipeline with GitHub Actions and AWS ECS"

# Push to develop branch first (test the pipeline)
git push origin develop

# Watch the workflow
gh run list --limit 5
gh run watch WORKFLOW_RUN_ID
```

## ✅ Step 5: Monitor First Deployment (15 min)

1. **Watch GitHub Actions**
   ```bash
   gh run watch
   ```
   Should see:
   - ✅ Tests pass
   - ✅ Security scan completes
   - ✅ Docker build succeeds
   - ✅ Deploy to dev starts

2. **Check AWS Deployment**
   ```bash
   # Watch ECS service
   aws ecs describe-services \
     --cluster energy-rag-cluster-dev \
     --services energy-rag-service-dev
   
   # Check logs
   aws logs tail /ecs/energy-rag-dev --follow
   ```

3. **Test the Service**
   ```bash
   # Get service URL
   SERVICE_IP=$(aws ecs describe-tasks \
     --cluster energy-rag-cluster-dev \
     --tasks $(aws ecs list-tasks --cluster energy-rag-cluster-dev --query 'taskArns[0]' --output text) \
     --query 'tasks[0].containers[0].networkInterfaces[0].privateIpv4Address' --output text)
   
   # Test health endpoint
   curl http://$SERVICE_IP:8000/health
   ```

**Expected Success**: 
- Service is running with desired count of tasks
- Health check passes
- Logs show successful startup

## ✅ Step 6: Test Production Deployment (10 min)

1. **Create Pull Request**
   ```bash
   git checkout -b release/v1.0
   git commit --allow-empty -m "Release v1.0"
   git push origin release/v1.0
   
   # Create PR via GitHub
   gh pr create --title "Release v1.0" --body "Production deployment" --base main
   ```

2. **Get Approval**
   - GitHub will require 1 code review (if configured)
   - Request review from team member

3. **Merge to Main**
   ```bash
   gh pr merge PULL_REQUEST_ID --merge
   ```

4. **Monitor Production Deployment**
   ```bash
   gh run list --limit 5
   gh run watch LATEST_WORKFLOW_ID
   
   # Check prod status
   aws ecs describe-services \
     --cluster energy-rag-cluster-prod \
     --services energy-rag-service-prod
   
   # Check prod logs
   aws logs tail /ecs/energy-rag-prod --follow
   ```

**Expected**: Service deployed to production cluster

## ✅ Step 7: Set Up Monitoring (10 min)

### CloudWatch Alarms (Optional but Recommended)

```bash
# CPU too high
aws cloudwatch put-metric-alarm \
  --alarm-name energy-rag-high-cpu \
  --alarm-description "Alert when CPU is high" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold

# Service unhealthy
aws cloudwatch put-metric-alarm \
  --alarm-name energy-rag-unhealthy-tasks \
  --alarm-description "Alert when tasks unhealthy" \
  --metric-name HealthyHostCount \
  --namespace AWS/ApplicationELB \
  --statistic Average \
  --period 300 \
  --threshold 1 \
  --comparison-operator LessThanThreshold
```

### Log Insights Queries

```bash
# Watch recent errors
aws logs start-query \
  --log-group-name /ecs/energy-rag-prod \
  --start-time $(date -d '1 hour ago' +%s) \
  --end-time $(date +%s) \
  --query-string 'fields @timestamp, @message | filter @message like /ERROR/'
```

## ✅ Step 8: Verify Everything Works (15 min)

### Test Development Deployment

```bash
# Make a test change
echo "# Updated" >> README.md
git add README.md
git commit -m "test: verify CI/CD pipeline"
git push origin develop

# Watch pipeline
gh run watch

# Verify logs
aws logs tail /ecs/energy-rag-dev --follow
```

### Test Production Deployment

```bash
# Create PR to main
git checkout main
git pull origin main
git checkout -b test/ci-cd
git commit --allow-empty -m "Test: verify prod deployment"
git push origin test/ci-cd

# Create and merge PR
gh pr create --title "Test: verify prod deployment" --base main
gh pr merge PULL_REQUEST_ID --merge

# Watch pipeline
gh run watch

# Verify logs
aws logs tail /ecs/energy-rag-prod --follow
```

### Test Health Checks

```bash
# Get task IP
TASK_IP=$(aws ecs describe-tasks \
  --cluster energy-rag-cluster-prod \
  --tasks $(aws ecs list-tasks --cluster energy-rag-cluster-prod --query 'taskArns[0]' --output text) \
  --query 'tasks[0].containers[0].networkInterfaces[0].privateIpv4Address' --output text)

# Test health endpoint
curl http://$TASK_IP:8000/health

# Test chat endpoint
curl -X POST http://$TASK_IP:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is frequency control?", "session_id": "test"}'

# Test web UI
curl -s http://$TASK_IP:8000/ | head -20
```

## ✅ Step 9: Post-Deployment Checklist

- [ ] AWS resources all created and verified
- [ ] GitHub Secrets configured
- [ ] First develop branch deployment successful
- [ ] First main branch deployment successful
- [ ] Health checks passing
- [ ] Logs visible in CloudWatch
- [ ] Slack notifications working (if configured)
- [ ] Team members can trigger deployments
- [ ] Rollback tested (update service to previous task def)
- [ ] Monitoring configured

## ✅ Step 10: Document & Communicate

1. **Share Documentation**
   - Send team link to `.github/GITHUB_SETUP.md`
   - Send team link to `.aws/DEPLOYMENT_GUIDE.md`
   - Share `CI_CD_QUICKREF.md` for daily use

2. **Document Your Setup**
   - AWS Account ID used
   - AWS Region (us-east-1)
   - ECR repository name
   - ECS cluster names
   - Team member with AWS console access

3. **Runbooks**
   - How to deploy
   - How to rollback
   - How to scale
   - How to check logs
   - How to debug

## 🎯 Troubleshooting During Implementation

| Issue | Solution |
|-------|----------|
| AWS CLI not found | `curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && unzip awscliv2.zip && sudo ./aws/install` |
| Authentication error | Check AWS credentials: `aws sts get-caller-identity` |
| GitHub secrets not working | Redeploy workflow after adding secrets |
| Tests failing | Run `pytest test/ -v` locally first |
| ECR push failing | Verify AWS credentials, check ECR repository exists |
| ECS deployment failing | Check CloudWatch logs: `aws logs tail /ecs/energy-rag-dev --follow` |
| Health check failing | Verify app is actually running: `docker logs CONTAINER_ID` |

## ✅ Success Criteria

Your implementation is successful when:

✅ Code pushed to develop → auto-deploys to dev ECS
✅ Code pushed to main → auto-deploys to prod ECS
✅ Tests run automatically on every push
✅ Security scanning runs automatically
✅ Docker images built and pushed to ECR
✅ Health checks pass
✅ Logs visible in CloudWatch
✅ Team can see pipeline status in GitHub
✅ Deployments take 6-12 minutes end-to-end

## 📞 If Something Goes Wrong

1. **Check the docs first**
   - `.aws/DEPLOYMENT_GUIDE.md` — troubleshooting section
   - `.github/GITHUB_SETUP.md` — troubleshooting section
   - `CI_CD_SUMMARY.md` — common issues table

2. **Check logs**
   ```bash
   # GitHub Actions logs
   gh run view RUN_ID --log
   
   # AWS ECS logs
   aws logs tail /ecs/energy-rag-dev --follow
   ```

3. **Check status**
   ```bash
   # GitHub
   gh run list
   
   # AWS
   aws ecs describe-services --cluster energy-rag-cluster-dev --services energy-rag-service-dev
   ```

---

**Estimated Total Time**: 2-3 hours for complete setup

**Questions?** Refer to the documentation files or check GitHub Actions logs for detailed error messages.

**Next Steps After Implementation**:
- [ ] Set up monitoring/alerts
- [ ] Configure auto-scaling
- [ ] Implement blue-green deployment
- [ ] Document team runbooks
- [ ] Train team on deployment process
