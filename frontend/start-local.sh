#!/bin/bash
# Start local development server for frontend

PORT=${1:-8000}

echo "🚀 Starting Notification Agent Frontend on http://localhost:$PORT"
echo ""
echo "📝 Note: This is a vanilla JavaScript app (not React)"
echo "⚠️  API calls will fail without backend - UI is for preview only"
echo ""
echo "Opening browser..."
echo ""

# Try to open browser
if command -v open &> /dev/null; then
    # macOS
    open "http://localhost:$PORT/index.local.html" &
elif command -v xdg-open &> /dev/null; then
    # Linux
    xdg-open "http://localhost:$PORT/index.local.html" &
fi

# Start server
cd "$(dirname "$0")"

if command -v python3 &> /dev/null; then
    python3 -m http.server $PORT
elif command -v python &> /dev/null; then
    python -m http.server $PORT
elif command -v php &> /dev/null; then
    php -S localhost:$PORT
else
    echo "❌ Error: No HTTP server found. Please install Python or PHP."
    echo ""
    echo "Or use any of these alternatives:"
    echo "  - npx serve"
    echo "  - npx http-server"
    echo "  - docker run -p $PORT:80 -v \$(pwd):/usr/share/nginx/html nginx"
    exit 1
fi

