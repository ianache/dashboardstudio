#!/bin/sh

# Path where Vite builds the files
WWW_DIR="/usr/share/nginx/html"
ENV_FILE="/app/.env"

echo "Replacing environment variables in JS files..."

# If .env exists, we read it and replace placeholders
if [ -f "$ENV_FILE" ]; then
    # For each line in .env (ignoring comments and empty lines)
    grep -v '^#' "$ENV_FILE" | grep '=' | while read -r line; do
        # Extract key and value
        key=$(echo "$line" | cut -d '=' -f 1)
        value=$(echo "$line" | cut -d '=' -f 2- | tr -d '"' | tr -d "'")
        
        echo "Processing $key..."
        
        # Replace occurrences of the key in all JS and HTML files
        # We search for the pattern like 'VITE_API_URL: "..."' or similar
        # Since Vite bakes it, it will look like the build-time value.
        # We'll use the build-time placeholder as the search string.
        
        # IMPORTANT: During build, we will set these to placeholders like "BUILD_TIME_PLACEHOLDER_VITE_API_URL"
        find "$WWW_DIR" -type f \( -name "*.js" -o -name "*.html" \) -exec sed -i "s|BUILD_TIME_PLACEHOLDER_$key|$value|g" {} +
    done
else
    echo ".env file not found at $ENV_FILE, skipping replacement."
fi

echo "Environment variables replaced. Starting Nginx..."
exec nginx -g "daemon off;"
