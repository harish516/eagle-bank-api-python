# Dev Container Dockerfile for Eagle Bank API
FROM python:3.11-slim

# Arguments
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Install system dependencies
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    git \
    curl \
    wget \
    ca-certificates \
    sudo \
    gcc \
    g++ \
    make \
    build-essential \
    postgresql-client \
    redis-tools \
    vim \
    nano \
    htop \
    procps \
    lsb-release \
    software-properties-common \
    apt-transport-https \
    gnupg2 \
    bash-completion \
    tree \
    jq \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI (optional - commented out to avoid issues)
# RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
#     && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
#     && apt-get update \
#     && apt-get install -y docker-ce-cli \
#     && apt-get clean -y \
#     && rm -rf /var/lib/apt/lists/*

# Install Docker Compose (optional - commented out to avoid issues)
# RUN curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose \
#     && chmod +x /usr/local/bin/docker-compose

# Create the user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Set up Python environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install Python development tools
RUN pip install --upgrade pip setuptools wheel

# Create workspace directory
RUN mkdir -p /workspaces/eagle-bank-api-python \
    && chown -R $USERNAME:$USERNAME /workspaces

# Switch to the user
USER $USERNAME

# Set up shell
RUN echo 'alias ll="ls -alF"' >> ~/.bashrc \
    && echo 'alias la="ls -A"' >> ~/.bashrc \
    && echo 'alias l="ls -CF"' >> ~/.bashrc \
    && echo 'export PS1="\[\e[32m\]\u@\h:\[\e[34m\]\w\[\e[0m\]\$ "' >> ~/.bashrc

# Set working directory
WORKDIR /workspaces/eagle-bank-api-python

# Install Python dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install --user -r requirements.txt \
    && pip install --user -r requirements-dev.txt

# Set PATH to include user's local bin
ENV PATH="/home/$USERNAME/.local/bin:$PATH"

# Keep container running
CMD ["sleep", "infinity"]
