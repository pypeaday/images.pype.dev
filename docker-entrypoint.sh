#!/bin/bash
set -e

# VIRTUAL_ENV and PATH should be set by the Dockerfile

SSH_DIR="/home/appuser/.ssh"
PRIVATE_KEY_PATH="$SSH_DIR/id_rsa"
KNOWN_HOSTS_PATH="$SSH_DIR/known_hosts"

# Check for SSH private key
if [ ! -f "$PRIVATE_KEY_PATH" ]; then
  echo "ERROR: SSH private key not found at $PRIVATE_KEY_PATH."
  echo "Please ensure your private key is correctly mounted in docker-compose.yml (e.g., ~/.skm/images-pype-dev) and the host path is correct."
  echo "The key file on your host machine must also have permissions set to 600 (e.g., chmod 600 ~/.skm/images-pype-dev)."
  exit 1
else
  echo "SSH private key found at $PRIVATE_KEY_PATH."
  # The key is mounted read-only, permissions are set on the host.
  # Verify known_hosts exists
  if [ ! -f "$KNOWN_HOSTS_PATH" ]; then
    echo "Warning: $KNOWN_HOSTS_PATH not found. SSH connections might require manual confirmation or fail."
  fi
fi

# Configure Git with credentials from environment variables
if [ -n "$GIT_COMMIT_USER_NAME" ] && [ -n "$GIT_COMMIT_USER_EMAIL" ]; then
  echo "Configuring Git with user: '$GIT_COMMIT_USER_NAME', email: '$GIT_COMMIT_USER_EMAIL'"
  git config --global user.name "$GIT_COMMIT_USER_NAME"
  git config --global user.email "$GIT_COMMIT_USER_EMAIL"
else
  echo "Warning: GIT_COMMIT_USER_NAME or GIT_COMMIT_USER_EMAIL not set. Git commits may fail or use default credentials."
fi

# Start the application
echo "Starting application (uv run app/shotput.py)..."
exec "$@"
