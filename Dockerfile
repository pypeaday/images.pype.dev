FROM python:3.12-slim

# Set environment variables
ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Install dependencies: git and openssh-client
RUN apt-get update && \
    apt-get install -y --no-install-recommends git openssh-client && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Create a non-root user, app directories, and SSH setup
RUN mkdir -p /app/data && \
    useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app && \
    chmod 755 /app/data && \
    mkdir -p /opt/venv && \
    chown -R appuser:appuser /opt/venv && \
    # Create .ssh directory for appuser and add GitHub to known_hosts
    mkdir -p /home/appuser/.ssh && \
    chown appuser:appuser /home/appuser/.ssh && \
    chmod 700 /home/appuser/.ssh && \
    ssh-keyscan github.com >> /home/appuser/.ssh/known_hosts && \
    chown appuser:appuser /home/appuser/.ssh/known_hosts && \
    chmod 644 /home/appuser/.ssh/known_hosts

# Set working directory
WORKDIR /app

# Copy application files (as root, then chown appropriately)
# docker-entrypoint.sh needs to be executable and owned by appuser
COPY --chown=appuser:appuser docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh
# Copy the rest of the application files, ensuring appuser owns them
# The repo should be volume mounted in at runtime - no point in building the media in
# COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Create virtual environment and install dependencies
RUN uv venv $VIRTUAL_ENV
# ENV UV_PYTHON=$VIRTUAL_ENV/bin/python # This might not be needed if PATH is set correctly

# Expose port
EXPOSE 8000

# Use entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]
