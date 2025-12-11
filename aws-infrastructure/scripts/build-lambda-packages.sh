#!/bin/bash
# Build Lambda deployment packages

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LAMBDA_DIR="$PROJECT_ROOT/lambda-functions"
TERRAFORM_DIR="$SCRIPT_DIR/../terraform"

echo "Building Lambda deployment packages..."

# Function to build a Lambda package
build_lambda() {
    local function_name=$1
    local function_dir="$LAMBDA_DIR/$function_name"
    local zip_file="$TERRAFORM_DIR/../lambda-functions/$function_name/deployment.zip"
    
    if [ ! -d "$function_dir" ]; then
        echo "Error: Function directory not found: $function_dir"
        return 1
    fi
    
    echo "Building $function_name..."
    
    # Create temporary directory
    local temp_dir=$(mktemp -d)
    trap "rm -rf $temp_dir" EXIT
    
    # Copy function code
    cp -r "$function_dir"/* "$temp_dir/"
    
    # Install dependencies
    if [ -f "$function_dir/requirements.txt" ]; then
        echo "Installing dependencies for $function_name..."
        pip install -r "$function_dir/requirements.txt" -t "$temp_dir/" --quiet
    fi
    
    # Create zip file
    cd "$temp_dir"
    zip -r "$zip_file" . -q
    
    echo "✓ Built $function_name"
}

# Build all Lambda functions
build_lambda "user-management"
build_lambda "data-source-config"
build_lambda "process-notifications"
build_lambda "summarize"
build_lambda "deliver"
build_lambda "status-check"

echo ""
echo "All Lambda packages built successfully!"
echo "Deployment packages are in: lambda-functions/*/deployment.zip"

