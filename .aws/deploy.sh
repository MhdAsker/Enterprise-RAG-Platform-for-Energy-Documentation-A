#!/bin/bash

# CloudFormation Deployment Script for Energy RAG Platform
# This script deploys the entire AWS infrastructure with one command

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT_NAME="${1:-energy-rag}"
AWS_REGION="${2:-us-east-1}"
STACK_NAME="${ENVIRONMENT_NAME}-stack"

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Energy RAG Platform - CloudFormation Deployment${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "  Stack Name:     $STACK_NAME"
echo "  Environment:    $ENVIRONMENT_NAME"
echo "  AWS Region:     $AWS_REGION"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed${NC}"
    echo "   Install from: https://aws.amazon.com/cli/"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo -e "${RED}❌ jq is not installed${NC}"
    echo "   Install from: https://stedolan.github.io/jq/download/"
    exit 1
fi

# Verify AWS credentials
if ! aws sts get-caller-identity --region "$AWS_REGION" > /dev/null 2>&1; then
    echo -e "${RED}❌ AWS credentials not configured or invalid${NC}"
    echo "   Run: aws configure"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ AWS credentials valid (Account: $ACCOUNT_ID)${NC}"

# Check if template file exists
if [ ! -f "template.yml" ]; then
    echo -e "${RED}❌ template.yml not found in current directory${NC}"
    exit 1
fi
echo -e "${GREEN}✓ template.yml found${NC}"
echo ""

# Check if stack already exists
echo -e "${YELLOW}Checking if stack already exists...${NC}"
if aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    > /dev/null 2>&1; then

    echo -e "${YELLOW}Stack already exists. Updating...${NC}"
    OPERATION="update-stack"
    WAIT_CONDITION="stack-update-complete"
else
    echo -e "${YELLOW}Stack does not exist. Creating...${NC}"
    OPERATION="create-stack"
    WAIT_CONDITION="stack-create-complete"
fi

echo ""
echo -e "${BLUE}Deploying CloudFormation stack...${NC}"

# Deploy the stack
STACK_ID=$(aws cloudformation $OPERATION \
    --stack-name "$STACK_NAME" \
    --template-body file://template.yml \
    --parameters \
        ParameterKey=EnvironmentName,ParameterValue="$ENVIRONMENT_NAME" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "$AWS_REGION" \
    --query 'StackId' \
    --output text 2>&1)

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to deploy stack${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Stack $OPERATION initiated${NC}"
echo "  Stack ID: $STACK_ID"
echo ""

# Wait for stack to complete
echo -e "${YELLOW}Waiting for stack deployment to complete...${NC}"
echo "(This may take 3-5 minutes)"

if aws cloudformation wait "$WAIT_CONDITION" \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION"; then

    echo -e "${GREEN}✓ Stack deployment completed successfully${NC}"
else
    echo -e "${RED}❌ Stack deployment failed or timed out${NC}"
    echo ""
    echo -e "${YELLOW}Checking stack events...${NC}"
    aws cloudformation describe-stack-events \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query 'StackEvents[0:5]' \
        --output table
    exit 1
fi

echo ""
echo -e "${BLUE}Retrieving stack outputs...${NC}"
echo ""

# Get stack outputs
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs' \
    --output table

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Deployment Complete!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo "1. Store Groq API Key in Secrets Manager:"
echo ""
echo "   Development:"
echo "   aws secretsmanager create-secret \\"
echo "     --name groq-api-key-dev \\"
echo "     --secret-string 'YOUR_GROQ_API_KEY' \\"
echo "     --region $AWS_REGION"
echo ""
echo "   Production:"
echo "   aws secretsmanager create-secret \\"
echo "     --name groq-api-key-prod \\"
echo "     --secret-string 'YOUR_GROQ_API_KEY' \\"
echo "     --region $AWS_REGION"
echo ""
echo "2. Create IAM User for GitHub Actions:"
echo "   - Go to AWS Console → IAM → Users → Create User"
echo "   - User name: github-actions-deployment"
echo "   - Create Access Key and save credentials"
echo "   - Attach policy: AmazonEC2ContainerRegistryPowerUser"
echo ""
echo "3. Add GitHub Secrets:"
echo "   gh secret set AWS_ACCESS_KEY_ID --body 'xxx'"
echo "   gh secret set AWS_SECRET_ACCESS_KEY --body 'xxx'"
echo "   gh secret set GROQ_API_KEY --body 'xxx'"
echo ""
echo "4. View CloudWatch Logs:"
echo "   aws logs tail /ecs/${ENVIRONMENT_NAME}-dev --follow"
echo "   aws logs tail /ecs/${ENVIRONMENT_NAME}-prod --follow"
echo ""
echo "5. Push code to GitHub:"
echo "   git push origin develop"
echo ""
echo -e "${YELLOW}Useful Commands:${NC}"
echo ""
echo "  # View stack status"
echo "  aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION"
echo ""
echo "  # View stack events"
echo "  aws cloudformation describe-stack-events --stack-name $STACK_NAME --region $AWS_REGION"
echo ""
echo "  # List ECS clusters"
echo "  aws ecs list-clusters --region $AWS_REGION"
echo ""
echo "  # List ECR repositories"
echo "  aws ecr describe-repositories --region $AWS_REGION"
echo ""
echo "  # Delete stack (cleanup)"
echo "  aws cloudformation delete-stack --stack-name $STACK_NAME --region $AWS_REGION"
echo ""
