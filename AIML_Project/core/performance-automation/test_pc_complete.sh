#!/bin/bash

# PC 24.1 Complete Report Download Test Script
# This script authenticates, gets cookie, and downloads the report

set -e  # Exit on error

echo "==========================================="
echo "PC 24.1 Complete Download Test"
echo "==========================================="
echo ""

# ============================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================
PC_HOST="pc-server.example.com"
PC_PORT="443"
PC_USERNAME="your-username"
PC_PASSWORD="your-password"
DOMAIN="DEFAULT"
PROJECT="MyProject"
RUN_ID="12345"
RESULT_ID="67890"

echo "Configuration:"
echo "  PC Host: $PC_HOST:$PC_PORT"
echo "  Username: $PC_USERNAME"
echo "  Domain: $DOMAIN"
echo "  Project: $PROJECT"
echo "  Run ID: $RUN_ID"
echo "  Result ID: $RESULT_ID"
echo ""

# ============================================
# STEP 1: AUTHENTICATION
# ============================================
echo "==========================================="
echo "STEP 1: Authentication"
echo "==========================================="

# Generate Base64 token
BASE64_TOKEN=$(printf '%s:%s' "$PC_USERNAME" "$PC_PASSWORD" | base64 -w 0)
echo "✓ Base64 token generated (length: ${#BASE64_TOKEN})"
echo "  Token preview: ${BASE64_TOKEN:0:20}..."
echo ""

# Authenticate
echo "Authenticating with PC..."
AUTH_RESPONSE=$(curl -k -i -s -X POST \
  "https://${PC_HOST}:${PC_PORT}/LoadTest/rest/authentication-point/authenticate" \
  -H "Content-Type: application/json" \
  --data-binary "{\"Token\":\"${BASE64_TOKEN}\"}")

echo "Authentication response received (length: ${#AUTH_RESPONSE})"
echo ""

# Extract HTTP status
if echo "$AUTH_RESPONSE" | grep -q "HTTP/2 200\|HTTP/1.1 200\|HTTP/2 201\|HTTP/1.1 201"; then
    echo "✓ Authentication successful (HTTP 200/201)"
else
    echo "✗ Authentication failed!"
    echo "Response:"
    echo "$AUTH_RESPONSE" | head -20
    exit 1
fi

# Extract cookies
COOKIE=$(echo "$AUTH_RESPONSE" | grep -i 'set-cookie:' | awk -F': ' '{print $2}' | awk -F';' '{print $1}' | tr '\n' '; ' | sed 's/; $//')

if [ -z "$COOKIE" ]; then
    echo "✗ Failed to extract cookie!"
    echo "Response headers:"
    echo "$AUTH_RESPONSE" | head -30
    exit 1
fi

echo "✓ Cookie extracted successfully"
echo "  Cookie length: ${#COOKIE}"
echo "  Cookie preview: ${COOKIE:0:80}..."
echo ""

# ============================================
# STEP 2: TEST ENDPOINTS
# ============================================
echo "==========================================="
echo "STEP 2: Testing Endpoints"
echo "==========================================="
echo ""

# Array of endpoints to test
ENDPOINTS=(
    "/LoadTest/rest/domains/$DOMAIN/projects/$PROJECT/Runs/$RUN_ID/Results/$RESULT_ID/data"
    "/LoadTest/rest/domains/$DOMAIN/projects/$PROJECT/Runs/$RUN_ID/Results/$RESULT_ID"
    "/LoadTest/rest/domains/$DOMAIN/projects/$PROJECT/Results/$RESULT_ID/data"
    "/LoadTest/rest/domains/$DOMAIN/projects/$PROJECT/Results/$RESULT_ID/Report.zip"
    "/loadtest/rest/domains/$DOMAIN/projects/$PROJECT/Runs/$RUN_ID/Results/$RESULT_ID/data"
)

WORKING_ENDPOINT=""

for endpoint in "${ENDPOINTS[@]}"; do
    echo "Testing: $endpoint"
    
    # HEAD request to check if endpoint exists
    HEAD_RESPONSE=$(curl -k -I -s \
        "https://$PC_HOST:$PC_PORT$endpoint" \
        -H "Cookie: $COOKIE" \
        -H "Accept: application/octet-stream" \
        -w "\nHTTP_CODE:%{http_code}\n")
    
    HTTP_CODE=$(echo "$HEAD_RESPONSE" | grep "HTTP_CODE:" | cut -d':' -f2)
    
    if [ "$HTTP_CODE" = "200" ] || echo "$HEAD_RESPONSE" | grep -q "HTTP/2 200\|HTTP/1.1 200"; then
        echo "  ✓ 200 OK - Endpoint is accessible!"
        WORKING_ENDPOINT="$endpoint"
        break
    elif [ "$HTTP_CODE" = "404" ] || echo "$HEAD_RESPONSE" | grep -q "404"; then
        echo "  ✗ 404 Not Found"
    elif [ "$HTTP_CODE" = "401" ] || echo "$HEAD_RESPONSE" | grep -q "401"; then
        echo "  ✗ 401 Unauthorized"
    else
        echo "  ? Status: $HTTP_CODE"
        echo "$HEAD_RESPONSE" | head -5
    fi
    echo ""
done

if [ -z "$WORKING_ENDPOINT" ]; then
    echo "✗ No working endpoint found!"
    echo ""
    echo "Tried all endpoints:"
    for ep in "${ENDPOINTS[@]}"; do
        echo "  - $ep"
    done
    echo ""
    echo "Please verify:"
    echo "  1. Domain: $DOMAIN"
    echo "  2. Project: $PROJECT"
    echo "  3. Run ID: $RUN_ID"
    echo "  4. Result ID: $RESULT_ID"
    exit 1
fi

# ============================================
# STEP 3: DOWNLOAD REPORT
# ============================================
echo "==========================================="
echo "STEP 3: Downloading Report"
echo "==========================================="
echo ""
echo "Using endpoint: $WORKING_ENDPOINT"
echo "Full URL: https://$PC_HOST:$PC_PORT$WORKING_ENDPOINT"
echo ""

# Download with verbose output
echo "Starting download..."
curl -k -v \
    "https://$PC_HOST:$PC_PORT$WORKING_ENDPOINT" \
    -H "Cookie: $COOKIE" \
    -H "Accept: application/octet-stream" \
    -o Report.zip \
    -w "\n\nDownload Stats:\nHTTP Code: %{http_code}\nSize Downloaded: %{size_download} bytes\nSpeed: %{speed_download} bytes/sec\n" \
    2>&1 | tee download.log

echo ""
echo "Download complete!"
echo ""

# ============================================
# STEP 4: VERIFY DOWNLOADED FILE
# ============================================
echo "==========================================="
echo "STEP 4: Verify Downloaded File"
echo "==========================================="
echo ""

if [ ! -f "Report.zip" ]; then
    echo "✗ Report.zip was not created!"
    echo ""
    echo "Check download.log for errors"
    exit 1
fi

FILE_SIZE=$(stat -c%s Report.zip 2>/dev/null || stat -f%z Report.zip 2>/dev/null)
echo "File size: $FILE_SIZE bytes"

FILE_TYPE=$(file -b Report.zip)
echo "File type: $FILE_TYPE"
echo ""

if [ "$FILE_SIZE" -lt 100 ]; then
    echo "⚠ File is very small (probably an error response)"
    echo "Content:"
    cat Report.zip
    echo ""
    exit 1
fi

if echo "$FILE_TYPE" | grep -qi "zip"; then
    echo "✓ File is a valid ZIP archive!"
    echo ""
    
    # ============================================
    # STEP 5: EXTRACT AND LIST CONTENTS
    # ============================================
    echo "==========================================="
    echo "STEP 5: Extract Report"
    echo "==========================================="
    echo ""
    
    # Create extraction directory
    mkdir -p extracted_report
    
    echo "Extracting Report.zip..."
    unzip -o Report.zip -d extracted_report 2>&1
    
    echo ""
    echo "Extracted files:"
    ls -lah extracted_report/
    echo ""
    
    echo "HTML files found:"
    find extracted_report/ -name "*.html" -o -name "*.htm"
    echo ""
    
    # Find main report
    MAIN_REPORT=$(find extracted_report/ -name "index.html" -o -name "report.html" -o -name "Report.html" | head -1)
    
    if [ -n "$MAIN_REPORT" ]; then
        echo "✓ Main report: $MAIN_REPORT"
        echo ""
        echo "You can open it with:"
        echo "  firefox $MAIN_REPORT"
        echo "  or"
        echo "  open $MAIN_REPORT"
    else
        echo "⚠ Could not find main HTML report"
        echo "All files:"
        find extracted_report/ -type f
    fi
    
elif echo "$FILE_TYPE" | grep -qi "html\|text"; then
    echo "⚠ File is HTML/text, not a ZIP archive"
    echo "This is likely an error response from PC"
    echo ""
    echo "Content (first 1000 chars):"
    head -c 1000 Report.zip
    echo ""
    exit 1
else
    echo "⚠ Unknown file type: $FILE_TYPE"
    echo ""
    echo "First 500 bytes:"
    head -c 500 Report.zip
    echo ""
fi

# ============================================
# SUMMARY
# ============================================
echo ""
echo "==========================================="
echo "SUMMARY"
echo "==========================================="
echo "✓ Authentication: Success"
echo "✓ Cookie extracted: ${#COOKIE} bytes"
echo "✓ Working endpoint: $WORKING_ENDPOINT"
echo "✓ Report downloaded: $FILE_SIZE bytes"
echo "✓ File type: $FILE_TYPE"
echo ""
echo "Files created:"
echo "  - Report.zip (original download)"
echo "  - extracted_report/ (extracted contents)"
echo "  - download.log (curl verbose output)"
echo ""
echo "==========================================="
echo "TEST COMPLETED SUCCESSFULLY!"
echo "==========================================="
