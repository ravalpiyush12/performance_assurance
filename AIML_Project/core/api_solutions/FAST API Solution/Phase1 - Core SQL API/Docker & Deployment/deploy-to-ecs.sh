#!/bin/bash

# Oracle SQL API - AWS ECS Deployment Script
# This script builds, pushes, and deploys the API to ECS

set -e

# Configuration - Update these values
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="YOUR_ACCOUNT_ID"
ECR_REPOSITORY="oracle-sql-api"
ECS_CLUSTER="your-cluster-name"
ECS_SERVICE="oracle-sql-api-service"
TASK_DEFINITION="oracle-sql-api"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Oracle SQL API - ECS Deployment${NC}"
echo -e "${GREEN}================================================${NC}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

# Get current timestamp for tagging
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
IMAGE_TAG="${TIMESTAMP}"

echo -e "${YELLOW}Configuration:${NC}"
echo "  AWS Region: $AWS_REGION"
echo "  ECR Repository: $ECR_REPOSITORY"
echo "  Image Tag: $IMAGE_TAG"
echo "  ECS Cluster: $ECS_CLUSTER"
echo "  ECS Service: $ECS_SERVICE"
echo ""

# Step 1: Build Docker image
echo -e "${GREEN}Step 1: Building Docker image...${NC}"
docker build -t ${ECR_REPOSITORY}:latest -t ${ECR_REPOSITORY}:${IMAGE_TAG} .
echo -e "${GREEN}✓ Docker image built successfully${NC}"
echo ""

# Step 2: Login to ECR
echo -e "${GREEN}Step 2: Logging in to Amazon ECR...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
echo -e "${GREEN}✓ Logged in to ECR${NC}"
echo ""

# Step 3: Tag image for ECR
echo -e "${GREEN}Step 3: Tagging image for ECR...${NC}"
docker tag ${ECR_REPOSITORY}:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:latest
docker tag ${ECR_REPOSITORY}:${IMAGE_TAG} ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}
echo -e "${GREEN}✓ Image tagged${NC}"
echo ""

# Step 4: Push image to ECR
echo -e "${GREEN}Step 4: Pushing image to ECR...${NC}"
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:latest
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}
echo -e "${GREEN}✓ Image pushed to ECR${NC}"
echo ""

# Step 5: Update ECS task definition
echo -e "${GREEN}Step 5: Updating ECS task definition...${NC}"

# Get current task definition
TASK_DEFINITION_ARN=$(aws ecs describe-task-definition \
    --task-definition ${TASK_DEFINITION} \
    --region ${AWS_REGION} \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text 2>/dev/null || echo "")

if [ -z "$TASK_DEFINITION_ARN" ]; then
    echo -e "${YELLOW}Task definition not found. Creating new one...${NC}"
    # Register new task definition from file
    aws ecs register-task-definition \
        --cli-input-json file://ecs-task-definition.json \
        --region ${AWS_REGION}
else
    echo -e "${YELLOW}Updating existing task definition...${NC}"
    # Get current task definition JSON
    TASK_DEF_JSON=$(aws ecs describe-task-definition \
        --task-definition ${TASK_DEFINITION} \
        --region ${AWS_REGION} \
        --query 'taskDefinition' \
        --output json)
    
    # Update image in task definition
    NEW_TASK_DEF=$(echo $TASK_DEF_JSON | jq \
        --arg IMAGE "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}" \
        '.containerDefinitions[0].image = $IMAGE | del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)')
    
    # Register new task definition revision
    aws ecs register-task-definition \
        --cli-input-json "$NEW_TASK_DEF" \
        --region ${AWS_REGION}
fi

echo -e "${GREEN}✓ Task definition updated${NC}"
echo ""

# Step 6: Update ECS service
echo -e "${GREEN}Step 6: Updating ECS service...${NC}"

# Check if service exists
SERVICE_EXISTS=$(aws ecs describe-services \
    --cluster ${ECS_CLUSTER} \
    --services ${ECS_SERVICE} \
    --region ${AWS_REGION} \
    --query 'services[0].serviceName' \
    --output text 2>/dev/null || echo "None")

if [ "$SERVICE_EXISTS" == "None" ]; then
    echo -e "${YELLOW}Service not found. Please create the service manually or update this script.${NC}"
else
    # Update service to use new task definition
    aws ecs update-service \
        --cluster ${ECS_CLUSTER} \
        --service ${ECS_SERVICE} \
        --task-definition ${TASK_DEFINITION} \
        --force-new-deployment \
        --region ${AWS_REGION}
    
    echo -e "${GREEN}✓ Service updated${NC}"
    echo ""
    
    # Wait for service to stabilize (optional)
    echo -e "${YELLOW}Waiting for service to stabilize (this may take a few minutes)...${NC}"
    aws ecs wait services-stable \
        --cluster ${ECS_CLUSTER} \
        --services ${ECS_SERVICE} \
        --region ${AWS_REGION}
    
    echo -e "${GREEN}✓ Service is stable${NC}"
fi

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Image: ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}"
echo ""
echo "Next steps:"
echo "1. Verify the deployment in AWS ECS console"
echo "2. Check CloudWatch logs for any issues"
echo "3. Test the API health endpoint"
echo ""