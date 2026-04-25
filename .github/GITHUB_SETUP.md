# GitHub Configuration Guide

Complete setup guide for GitHub Actions CI/CD pipeline.

## Repository Settings

### 1. Branch Protection Rules

Go to: Settings → Branches → Add branch protection rule

#### For `main` branch:
- ✅ Require a pull request before merging
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- ✅ Require code reviews before merging (1 approval minimum)
- ✅ Dismiss stale pull request approvals when new commits are pushed
- ✅ Include administrators
- ✅ Restrict who can push to matching branches
- ✅ Allow deletion of head branch

**Required status checks:**
- `test` job
- `security` job
- `build` job
- Any other required checks

#### For `develop` branch:
- ✅ Require a pull request before merging
- ✅ Require status checks to pass before merging
- ⚠️ Allow stale reviews (optional for faster development)
- ✅ Allow deletion of head branch

### 2. Environments

Go to: Settings → Environments → New environment

#### Development Environment
- **Name**: development
- **Deployment branches**: develop
- **Required reviewers**: None (optional)
- **Protection rules**: None

#### Production Environment
- **Name**: production
- **Deployment branches**: main
- **Required reviewers**: 2
- **Protection rules**: Required reviewers must approve before deployment

### 3. GitHub Secrets

Go to: Settings → Secrets and variables → Actions

#### Repository Secrets (all environments)
```
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
GROQ_API_KEY=your-groq-api-key
SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

#### Environment Secrets (optional, overrides repository secrets)
- Production: More restrictive credentials if desired
- Development: Less restrictive for testing

### 4. Environments Configuration

Go to: Settings → Environments → [environment name] → Configure

#### Development
```
Deployment branches and tags:
- Branches: develop

Required reviewers:
- None (for faster development)

Secrets:
- (inherit from repository)
```

#### Production
```
Deployment branches and tags:
- Branches: main

Required reviewers:
- 2 team members (set appropriate team)

Secrets:
- AWS_ACCESS_KEY_ID (different key if desired)
- AWS_SECRET_ACCESS_KEY (different secret if desired)
- GROQ_API_KEY
- SLACK_WEBHOOK
```

## GitHub Actions Configuration

### 1. Workflow Permissions

Go to: Settings → Actions → General

- ✅ Allow all actions and reusable workflows
- **Workflow permissions**:
  - ✅ Read and write permissions
  - ✅ Allow GitHub Actions to create and approve pull requests

### 2. Concurrency Settings

The `ci.yaml` workflow is configured to:
- Cancel in-progress runs for the same ref
- Allow main and develop to run simultaneously
- Prevent duplicate runs

## Setting Up Secrets via CLI

### Using GitHub CLI

```bash
# Login to GitHub
gh auth login

# Set repository secrets
gh secret set AWS_ACCESS_KEY_ID --body "your-access-key"
gh secret set AWS_SECRET_ACCESS_KEY --body "your-secret-key"
gh secret set GROQ_API_KEY --body "your-groq-api-key"
gh secret set SLACK_WEBHOOK --body "your-slack-webhook-url"

# Verify secrets are set
gh secret list
```

### Using GitHub API

```bash
# Create a personal access token first (Settings → Developer settings → Personal access tokens)
# Then use the API:

curl -X PUT \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/MhdAsker/Enterprise-RAG-Platform-for-Energy-Documentation-A/actions/secrets/AWS_ACCESS_KEY_ID \
  -d '{"encrypted_value":"YOUR_ENCRYPTED_VALUE","key_id":"YOUR_KEY_ID"}'
```

## Workflow Triggers

The CI/CD pipeline is triggered on:

### Automatic Triggers
- Push to `main` branch
- Push to `develop` branch
- Pull request to `main` branch
- Pull request to `develop` branch

### Manual Triggers (optional)
Add to workflow to enable manual runs:
```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy to'
        required: true
        default: 'development'
```

## Notifications

### Slack Integration

The workflow sends notifications to Slack on:
- Deployment status (success/failure)
- Test failures
- Security scan results
- Build errors

**Setup:**
1. Create incoming webhook: https://api.slack.com/messaging/webhooks
2. Add webhook URL to GitHub Secrets as `SLACK_WEBHOOK`
3. Workflow will automatically send notifications

### Email Notifications

GitHub will send email notifications to repository watchers on:
- Workflow failures
- Manual action items (reviews, approvals)

Go to: Settings → Notifications to customize

## Status Badge

Add to your README.md:

```markdown
# Enterprise RAG Platform for Energy Documentation

![CI/CD Pipeline](https://github.com/MhdAsker/Enterprise-RAG-Platform-for-Energy-Documentation-A/workflows/CI%2FCD%20Pipeline/badge.svg)
![Python Tests](https://github.com/MhdAsker/Enterprise-RAG-Platform-for-Energy-Documentation-A/workflows/CI%2FCD%20Pipeline/badge.svg?label=tests)
```

## Pull Request Template

Create `.github/pull_request_template.md`:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Closes #(issue number)

## Testing
- [ ] Unit tests added
- [ ] Integration tests added
- [ ] Manual testing completed

## Deployment Impact
- [ ] No deployment changes
- [ ] Development only
- [ ] Production changes required

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally
```

## Issue Templates

Create `.github/ISSUE_TEMPLATE/bug_report.md`:

```markdown
---
name: Bug Report
about: Report a bug
title: ''
labels: 'bug'
assignees: ''
---

## Description
Clear description of the bug

## Reproduction Steps
1. ...
2. ...
3. ...

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: 
- Python: 
- Commit: 

## Logs
```
error logs here
```
```

## Monitoring the Pipeline

### Real-time Status
1. Go to: Actions tab in your repository
2. Select the latest workflow run
3. View logs for each job
4. Check status of deployments

### Access Logs
```bash
# View GitHub Actions logs locally
gh run view WORKFLOW_RUN_ID --log

# List recent runs
gh run list --limit 20

# Watch a specific run
gh run watch WORKFLOW_RUN_ID
```

## Troubleshooting

### Workflow Not Running
1. Check branch protection rules don't block the workflow
2. Verify `ci.yaml` is in `.github/workflows/`
3. Check if secrets are configured
4. Look at "Actions" tab for error messages

### Tests Failing in CI
```bash
# Run tests locally first
pytest test/ -v

# Check for differences between local and CI environments
# Common issues:
# - Missing dependencies
# - Environment variable differences
# - Python version mismatch
```

### Deployment Stuck
1. Check GitHub Actions logs for timeout
2. Verify AWS credentials are valid
3. Check AWS ECS service health
4. Review CloudWatch logs in AWS

### Secrets Not Available
1. Verify secret name matches workflow variable
2. Check secret is set in correct environment/scope
3. Restart workflow if you just added secrets
4. Verify GitHub Actions permissions

## Best Practices

### Commit Messages
Use conventional commits for better readability:
```
feat: Add new feature
fix: Fix specific bug
docs: Documentation updates
test: Test additions/modifications
chore: Dependency updates
perf: Performance improvements
```

### Pull Request Process
1. Create feature branch from `develop`
2. Make changes and commit with conventional messages
3. Push to GitHub and create PR
4. Wait for all checks to pass
5. Request reviews
6. Address review comments
7. Merge when approved
8. Delete feature branch

### Deployment Workflow
```
develop branch
    ↓
Feature branch (PR)
    ↓
Code review + approval
    ↓
Merge to develop
    ↓
Auto-deploy to dev environment
    ↓
Testing in development
    ↓
Create PR from develop → main
    ↓
Code review + approval
    ↓
Merge to main
    ↓
Auto-deploy to production
    ↓
Verify production deployment
```

## Security Considerations

### Secret Management
- ✅ Use GitHub Secrets for sensitive data
- ✅ Rotate credentials regularly
- ✅ Use least privilege IAM roles
- ✅ Enable MFA on AWS account
- ✅ Use separate credentials for dev/prod

### Code Security
- ✅ Enable branch protection on main
- ✅ Require code reviews
- ✅ Use automated security scanning
- ✅ Keep dependencies updated
- ✅ Sign commits (recommended)

### Audit Trail
- ✅ GitHub provides action logs
- ✅ AWS CloudTrail logs deployments
- ✅ Review security findings regularly
- ✅ Monitor unauthorized access attempts

## Performance Tips

### Caching
The workflow includes:
- Python package caching (via `setup-python`)
- Docker layer caching
- ECR image reuse

### Parallelization
Jobs that can run in parallel:
- `test` and `security` jobs run together
- `build` waits for tests to pass (required)
- `deploy-dev` and `deploy-prod` can run independently

### Cost Optimization
- Free tier includes 2,000 minutes/month
- Reuse Docker images (use latest tag)
- Cache dependencies
- Clean up old runs

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Secrets Management](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Workflow Syntax Reference](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Using Environment Variables](https://docs.github.com/en/actions/learn-github-actions/environment-variables)
- [Reusable Workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows)
