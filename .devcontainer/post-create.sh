#!/bin/bash

# Post-create script for Eagle Bank API Dev Container
set -e

echo "🚀 Setting up Eagle Bank API development environment..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --user -r requirements.txt
pip install --user -r requirements-dev.txt

# Install additional development tools
echo "🔧 Installing additional development tools..."
pip install --user \
    pytest-cov \
    pytest-xdist \
    httpx \
    jupyter \
    ipython

# Set up pre-commit hooks (if you want them)
echo "🪝 Setting up development tools..."
pip install --user pre-commit

# Create useful aliases
echo "⚡ Setting up development aliases..."
cat >> ~/.bashrc << 'EOF'

# Eagle Bank API Development Aliases
alias api="python -m app.main"
alias test="python -m pytest"
alias testcov="python -m pytest --cov=app --cov-report=html"
alias lint="flake8 app tests"
alias format="black app tests"
alias run-api="uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
alias run-debug="python debug_main.py"
alias db-connect="psql postgresql://postgres:password@db:5432/eagle_bank"
alias redis-cli="redis-cli -h redis -p 6379"

# Docker shortcuts
alias dc="docker-compose"
alias dcu="docker-compose up"
alias dcd="docker-compose down"
alias dcl="docker-compose logs"

# Git shortcuts
alias gs="git status"
alias ga="git add"
alias gc="git commit"
alias gp="git push"
alias gl="git log --oneline -10"

echo "🏦 Eagle Bank API Development Environment Ready!"
echo "Available commands:"
echo "  run-api     - Start the API with auto-reload"
echo "  run-debug   - Start the API with debugging"
echo "  test        - Run tests"
echo "  testcov     - Run tests with coverage"
echo "  lint        - Check code style"
echo "  format      - Format code with black"
echo "  db-connect  - Connect to PostgreSQL"
echo "  redis-cli   - Connect to Redis"
EOF

# Create a welcome message
cat > /tmp/welcome.txt << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║  🏦 Welcome to Eagle Bank API Development Container!        ║
║                                                              ║
║  🚀 Quick Start:                                            ║
║    • run-api      - Start the FastAPI server                ║
║    • run-debug    - Start with debugging enabled            ║
║    • test         - Run the test suite                      ║
║    • format       - Format code with Black                  ║
║                                                              ║
║  🔗 Services:                                               ║
║    • API:         http://localhost:8000                     ║
║    • Docs:        http://localhost:8000/docs                ║
║    • PostgreSQL:  localhost:5432                            ║
║    • Redis:       localhost:6379                            ║
║    • Keycloak:    http://localhost:8080                     ║
║                                                              ║
║  🐛 Debug:        Port 5678 for remote debugging           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF

# Display welcome message
cat /tmp/welcome.txt

# Make sure the workspace directory exists and has proper permissions
sudo chown -R vscode:vscode /workspaces/eagle-bank-api-python

# Initialize the database (if needed)
echo "🗄️  Checking database connection..."
# Wait for database to be ready
until pg_isready -h db -p 5432 -U postgres; do
    echo "Waiting for database..."
    sleep 2
done

echo "✅ Post-create setup completed successfully!"
echo "💡 Type 'source ~/.bashrc' to load new aliases, or restart your terminal."
