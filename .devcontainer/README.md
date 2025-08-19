# Eagle Bank API - Dev Container

This VS Code Dev Container provides a complete, containerized development environment for the Eagle Bank API project.

## 🚀 Quick Start

1. **Install Prerequisites:**
   - [VS Code](https://code.visualstudio.com/)
   - [Dev Containers Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
   - [Docker Desktop](https://www.docker.com/products/docker-desktop/)

2. **Open in Dev Container:**
   - Open this project in VS Code
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Type "Dev Containers: Reopen in Container"
   - Select it and wait for the container to build

3. **Start Developing:**
   - The container will automatically set up the environment
   - All dependencies will be pre-installed
   - Database, Redis, and Keycloak services will be available

## 🛠️ What's Included

### Development Tools
- Python 3.11 with all project dependencies
- Black code formatter
- Flake8 linter
- pytest testing framework
- debugpy for remote debugging
- Git and GitHub CLI

### Pre-configured Services
- **PostgreSQL** (port 5432) - Main database
- **Redis** (port 6379) - Cache and message broker
- **Keycloak** (port 8080) - Authentication server

### VS Code Extensions
- Python support with IntelliSense
- Docker integration
- GitHub Copilot (if you have access)
- Test integration
- Thunder Client for API testing

## 🏃‍♂️ Quick Commands

The dev container includes helpful aliases:

```bash
# Development
run-api      # Start FastAPI with auto-reload
run-debug    # Start with debugging enabled
test         # Run tests
testcov      # Run tests with coverage report
lint         # Check code style
format       # Format code with Black

# Database & Cache
db-connect   # Connect to PostgreSQL
redis-cli    # Connect to Redis

# Docker
dc           # docker-compose
dcu          # docker-compose up
dcd          # docker-compose down
```

## 🐛 Debugging

### Method 1: VS Code Debugger
1. Set breakpoints in your code
2. Press `F5` to start debugging
3. Select "Debug Eagle Bank API"

### Method 2: Remote Debugging
1. Run `run-debug` in terminal
2. Use the "Debug Eagle Bank API (Docker Attach)" configuration
3. Debug port 5678 is automatically forwarded

## 🧪 Testing

```bash
# Run all tests
test

# Run with coverage
testcov

# Run specific test file
python -m pytest tests/test_accounts.py -v

# Run tests in watch mode
python -m pytest --watch
```

## 📁 Project Structure

```
eagle-bank-api-python/
├── .devcontainer/           # Dev container configuration
│   ├── devcontainer.json    # Main dev container config
│   ├── Dockerfile           # Container definition
│   └── post-create.sh       # Setup script
├── app/                     # Application code
├── tests/                   # Test files
├── .vscode/                 # VS Code settings
└── docker-compose.devcontainer.yml  # Services for dev container
```

## 🔧 Environment Variables

The dev container automatically sets up these environment variables:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/eagle_bank
REDIS_URL=redis://redis:6379
KEYCLOAK_SERVER_URL=http://keycloak:8080
LOG_LEVEL=DEBUG
DEBUG=true
ENVIRONMENT=development
```

## 🌐 Service URLs

When the dev container is running:

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Keycloak**: http://localhost:8080

## 🔄 Rebuilding the Container

If you need to rebuild the dev container:

1. `Ctrl+Shift+P` → "Dev Containers: Rebuild Container"
2. Or: `Ctrl+Shift+P` → "Dev Containers: Rebuild Without Cache"

## 📝 Tips

- **Port Forwarding**: All necessary ports are automatically forwarded
- **Volume Mounts**: Your code changes are immediately reflected
- **Extensions**: All useful extensions are pre-installed
- **Git Integration**: Git is fully configured and ready to use
- **Docker Access**: You can use Docker commands inside the container

## 🔍 Troubleshooting

### Container won't start
- Make sure Docker Desktop is running
- Check if ports 5432, 6379, 8000, 8080 are available
- Try rebuilding the container

### Database connection issues
- Wait a moment for PostgreSQL to fully start
- Check logs: `docker-compose logs db`

### Permission issues
- The container runs as user `vscode` (UID 1000)
- File permissions should be automatically handled

## 🎯 Development Workflow

1. **Start the container** - VS Code will handle this
2. **Install dependencies** - Automatically done in post-create script
3. **Run the API** - Use `run-api` command
4. **Write code** - Full IntelliSense and debugging support
5. **Test** - Use `test` command or VS Code test integration
6. **Debug** - Set breakpoints and press F5
7. **Format** - Automatic on save, or use `format` command

Enjoy coding with the Eagle Bank API! 🏦✨
