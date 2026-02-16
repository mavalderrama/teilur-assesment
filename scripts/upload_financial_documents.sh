#!/bin/bash
# Script to download and upload Amazon financial documents to S3
# Required for Bedrock Knowledge Base

set -e

# Configuration
S3_BUCKET="${S3_BUCKET:-}"
AWS_REGION="${AWS_REGION:-us-east-2}"
KB_ID="${BEDROCK_KB_ID:-}"
DS_ID="${BEDROCK_DS_ID:-}"

# Document URLs (from assessment requirements)
declare -A DOCUMENTS
DOCUMENTS=(
    ["Amazon-2024-Annual-Report.pdf"]="https://s2.q4cdn.com/299287126/files/doc_financials/2025/ar/Amazon-2024-Annual-Report.pdf"
    ["AMZN-Q3-2025-Earnings-Release.pdf"]="https://s2.q4cdn.com/299287126/files/doc_financials/2025/q3/AMZN-Q3-2025-Earnings-Release.pdf"
    ["AMZN-Q2-2025-Earnings-Release.pdf"]="https://s2.q4cdn.com/299287126/files/doc_financials/2025/q2/AMZN-Q2-2025-Earnings-Release.pdf"
)

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "======================================================================"
echo "    Amazon Financial Documents Uploader"
echo "======================================================================"
echo ""

# Check dependencies
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI not found. Please install it first.${NC}"
    exit 1
fi

if ! command -v curl &> /dev/null; then
    echo -e "${RED}Error: curl not found. Please install it first.${NC}"
    exit 1
fi

# Get S3 bucket from terraform output if not provided
if [ -z "$S3_BUCKET" ]; then
    echo -e "${YELLOW}S3_BUCKET not set. Attempting to get from terraform...${NC}"
    if [ -d "terraform" ]; then
        cd terraform
        S3_BUCKET=$(terraform output -raw s3_bucket_name 2>/dev/null || echo "")
        cd ..
    fi

    if [ -z "$S3_BUCKET" ]; then
        echo -e "${RED}Error: S3_BUCKET not set. Please provide:${NC}"
        echo "  export S3_BUCKET=your-bucket-name"
        echo "  or run from project root with terraform outputs available"
        exit 1
    fi
fi

# Get Knowledge Base IDs from terraform if not provided
if [ -z "$KB_ID" ] || [ -z "$DS_ID" ]; then
    echo -e "${YELLOW}KB_ID or DS_ID not set. Attempting to get from terraform...${NC}"
    if [ -d "terraform" ]; then
        cd terraform
        KB_ID=$(terraform output -raw bedrock_knowledge_base_id 2>/dev/null || echo "")
        DS_ID=$(terraform output -raw bedrock_data_source_id 2>/dev/null || echo "")
        cd ..
    fi
fi

echo -e "${GREEN}Configuration:${NC}"
echo "  S3 Bucket: $S3_BUCKET"
echo "  AWS Region: $AWS_REGION"
echo "  Knowledge Base ID: ${KB_ID:-not set (optional)}"
echo "  Data Source ID: ${DS_ID:-not set (optional)}"
echo ""

# Create temporary directory
TMP_DIR=$(mktemp -d)
echo -e "${YELLOW}Using temporary directory: $TMP_DIR${NC}"
echo ""

# Download and upload each document
for filename in "${!DOCUMENTS[@]}"; do
    url="${DOCUMENTS[$filename]}"
    filepath="$TMP_DIR/$filename"

    echo "======================================================================"
    echo "Processing: $filename"
    echo "======================================================================"

    # Download document
    echo -e "${YELLOW}[1/3] Downloading from: $url${NC}"
    if curl -L -o "$filepath" "$url" --fail --silent --show-error; then
        filesize=$(ls -lh "$filepath" | awk '{print $5}')
        echo -e "${GREEN}✓ Downloaded successfully ($filesize)${NC}"
    else
        echo -e "${RED}✗ Failed to download $filename${NC}"
        continue
    fi

    # Upload to S3
    echo -e "${YELLOW}[2/3] Uploading to S3: s3://$S3_BUCKET/$filename${NC}"
    if aws s3 cp "$filepath" "s3://$S3_BUCKET/$filename" --region "$AWS_REGION"; then
        echo -e "${GREEN}✓ Uploaded to S3 successfully${NC}"
    else
        echo -e "${RED}✗ Failed to upload to S3${NC}"
        continue
    fi

    # Verify upload
    echo -e "${YELLOW}[3/3] Verifying S3 object...${NC}"
    if aws s3 ls "s3://$S3_BUCKET/$filename" --region "$AWS_REGION" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Verified in S3${NC}"
    else
        echo -e "${RED}✗ Verification failed${NC}"
    fi

    echo ""
done

# Cleanup
echo -e "${YELLOW}Cleaning up temporary files...${NC}"
rm -rf "$TMP_DIR"
echo -e "${GREEN}✓ Cleanup complete${NC}"
echo ""

# Sync Knowledge Base (if IDs provided)
if [ -n "$KB_ID" ] && [ -n "$DS_ID" ]; then
    echo "======================================================================"
    echo "Syncing Bedrock Knowledge Base"
    echo "======================================================================"
    echo ""

    echo -e "${YELLOW}Starting ingestion job...${NC}"
    JOB_OUTPUT=$(aws bedrock-agent start-ingestion-job \
        --knowledge-base-id "$KB_ID" \
        --data-source-id "$DS_ID" \
        --region "$AWS_REGION" \
        2>&1)

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Ingestion job started${NC}"
        echo "$JOB_OUTPUT" | jq '.' 2>/dev/null || echo "$JOB_OUTPUT"
        echo ""
        echo -e "${YELLOW}Monitor ingestion status with:${NC}"
        echo "  aws bedrock-agent list-ingestion-jobs \\"
        echo "    --knowledge-base-id $KB_ID \\"
        echo "    --data-source-id $DS_ID \\"
        echo "    --region $AWS_REGION"
    else
        echo -e "${RED}✗ Failed to start ingestion job${NC}"
        echo "$JOB_OUTPUT"
    fi
else
    echo "======================================================================"
    echo "Knowledge Base Sync (Manual)"
    echo "======================================================================"
    echo ""
    echo -e "${YELLOW}To sync the Knowledge Base, run:${NC}"
    echo ""
    echo "  aws bedrock-agent start-ingestion-job \\"
    echo "    --knowledge-base-id <YOUR_KB_ID> \\"
    echo "    --data-source-id <YOUR_DS_ID> \\"
    echo "    --region $AWS_REGION"
    echo ""
    echo "Get IDs from terraform:"
    echo "  cd terraform"
    echo "  terraform output bedrock_knowledge_base_id"
    echo "  terraform output bedrock_data_source_id"
fi

echo ""
echo "======================================================================"
echo -e "${GREEN}✓ Upload complete!${NC}"
echo "======================================================================"
echo ""
echo "Documents uploaded:"
for filename in "${!DOCUMENTS[@]}"; do
    echo "  ✓ $filename"
done
echo ""
echo "Next steps:"
echo "  1. Verify documents in S3:"
echo "     aws s3 ls s3://$S3_BUCKET/ --region $AWS_REGION"
echo ""
echo "  2. Wait for Knowledge Base ingestion to complete (may take 5-10 minutes)"
echo ""
echo "  3. Test the agent with document queries:"
echo "     - What is Amazon's office space in North America?"
echo "     - Tell me about Amazon's AI business"
echo ""
