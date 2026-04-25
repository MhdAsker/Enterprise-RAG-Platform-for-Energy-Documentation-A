# CI/CD Quick Reference

Fast lookup for common CI/CD tasks.

## 🚀 Quick Start

```bash
# 1. Set up AWS (follow .aws/DEPLOYMENT_GUIDE.md)
# 2. Configure GitHub (follow .github/GITHUB_SETUP.md)
# 3. Push code
git push origin develop  # Deploy to dev
git push origin main     # Deploy to prod (after PR merge)
```

## 📋 File Locations

| File | Purpose |
|------|---------|
| `.github/workflows/ci.yaml` | Main CI/CD pipeline |
| `.aws/task-definition-dev.json` | Development ECS config |
| `.aws/task-definition-prod.json` | Production ECS config |
| `Dockerfile` | Docker image build |
| `.aws/DEPLOYMENT_GUIDE.md` | AWS setup instructions |
| `.github/GITHUB_SETUP.md` | GitHub setup instructions |

## 🔐 GitHub Secrets to Add

```
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
GROQ_API_KEY=xxx
SLACK_WEBHOOK=https://hooks.slack.com/... (optional)
```

## 📊 Branch Strategy

| Branch | Triggers | Deploys To |
|--------|----------|-----------|
| `develop` | Push, PR | Development (auto) |
| `main` | Push, PR | Production (auto, with approvals) |

## ✅ Pipeline Status

```
Push code
  ↓
Run tests (92+)
  ↓
Security scanning
  ↓
Build Docker image
  ↓
Push to ECR
  ↓
Deploy to ECS
  ↓
Health check
  ↓
✅ Running
```

## 🔍 View Logs

### GitHub Actions
```bash
gh run list --limit 20
gh run view RUN_ID --log
gh run watch RUN_ID  # Live watch
```

### AWS ECS
```bash
# Development
aws logs tail /ecs/energy-rag-dev --follow

# Production
aws logs tail /ecs/energy-rag-prod --follow
```

## 🔧 Check Deployments

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

## 🆘 Rollback

```bash
# Update service to previous task definition
aws ecs update-service \
  --cluster energy-rag-cluster-prod \
  --service energy-rag-service-prod \
  --task-definition energy-rag-task:PREVIOUS_VERSION
```

## 📈 Monitor Deployment

```bash
# Watch service become healthy
watch -n 5 'aws ecs describe-services \
  --cluster energy-rag-cluster-prod \
  --services energy-rag-service-prod \
  --query "services[0].{runningCount: runningCount, desiredCount: desiredCount, status: status}"'
```

## 🐛 Troubleshooting

| Problem | Command |
|---------|---------|
| Tests failing | `gh run view --log` |
| Build failing | Check ECR repo exists, AWS credentials |
| Deploy failing | Check ECS cluster, logs in CloudWatch |
| App not responding | `curl http://SERVICE_URL/health` |
| Can't find secrets | Check GitHub Secrets under Settings |

## 📝 Commits & PRs

```bash
# Create feature branch
git checkout -b feat/feature-name

# Commit with conventional format
git commit -m "feat: add new feature"
git commit -m "fix: fix specific bug"
git commit -m "docs: update documentation"

# Push and create PR
git push origin feat/feature-name
# Then open PR on GitHub
```

## 🔔 Notifications

- Slack: Sent to `SLACK_WEBHOOK` channel
- Email: GitHub sends to watchers
- Status: See GitHub Actions tab

## ⚙️ Configuration

**All in one place: `.github/workflows/ci.yaml`**

Change:
- Branch names
- AWS region (search `us-east-1`)
- ECR repository name
- ECS service names
- Timeouts
- Container ports

## 📊 Resource Costs (Monthly)

| Service | Dev | Prod |
|---------|-----|------|
| ECS Fargate | ~$29 | ~$58 |
| ECR | $10+ | $10+ |
| CloudWatch | $0.50 | $1 |
| Data transfer | ~$1 | ~$2 |
| **Total** | ~$40 | ~$70 |

## 🎯 Common Tasks

### Deploy code to dev
```bash
git push origin develop
# Auto-deploys via GitHub Actions
```

### Deploy code to prod
```bash
# 1. Create PR from develop to main
# 2. Get approval
# 3. Merge
# Auto-deploys via GitHub Actions
```

### View deployment status
Go to: GitHub → Actions → Latest workflow run

### View application logs
```bash
aws logs tail /ecs/energy-rag-dev --follow
# or
aws logs tail /ecs/energy-rag-prod --follow
```

### Scale up production
```bash
aws ecs update-service \
  --cluster energy-rag-cluster-prod \
  --service energy-rag-service-prod \
  --desired-count 5
```

### Check what's running
```bash
aws ecs list-tasks --cluster energy-rag-cluster-prod
```

## 🔐 Security Checklist

- [ ] GitHub Secrets configured
- [ ] AWS credentials in GitHub Secrets
- [ ] GROQ_API_KEY in Secrets Manager
- [ ] IAM roles have least privilege
- [ ] Branch protection enabled on main
- [ ] Code reviews required
- [ ] Environment approvals for production
- [ ] Slack notifications enabled
- [ ] CloudWatch logs retention configured

## 📞 Getting Help

1. Check the relevant `.md` file:
   - `.aws/DEPLOYMENT_GUIDE.md` — AWS issues
   - `.github/GITHUB_SETUP.md` — GitHub issues
   - `CI_CD_SUMMARY.md` — Overview

2. Check GitHub Actions logs for errors

3. Check AWS CloudWatch logs

4. Check status of AWS resources:
   ```bash
   aws ecs describe-services --cluster NAME --services NAME
   ```

---

**Pro Tip**: Bookmark this file for quick reference!
