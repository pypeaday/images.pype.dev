#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.
set -x # Print commands and their arguments as they are executed.

# Ensure HOME is correctly set for appuser, which is crucial for git and ssh
export HOME=/home/appuser

echo "--- Docker Entrypoint Start ---"
echo "User: $(whoami)"
echo "HOME: $HOME"
echo "PWD: $(pwd)"

SSH_DIR="$HOME/.ssh"
PRIVATE_KEY_PATH="$SSH_DIR/id_rsa"
KNOWN_HOSTS_PATH="$SSH_DIR/known_hosts"

echo "Listing $SSH_DIR contents:"
ls -la "$SSH_DIR" || echo "$SSH_DIR not found or cannot be listed."

# Check for SSH private key
if [ ! -f "$PRIVATE_KEY_PATH" ]; then
  echo "ERROR: SSH private key not found at $PRIVATE_KEY_PATH."
  echo "Please ensure your private key is correctly mounted in docker-compose.yml and the host path is correct."
  echo "The key file on your host machine must also have permissions set to 600."
  # exit 1 # Commenting out exit 1 for now to see if ssh -T gives more info
else
  echo "SSH private key found at $PRIVATE_KEY_PATH."
  echo "Permissions of $PRIVATE_KEY_PATH:"
  ls -l "$PRIVATE_KEY_PATH"
fi

# Verify known_hosts exists
if [ ! -f "$KNOWN_HOSTS_PATH" ]; then
  echo "Warning: $KNOWN_HOSTS_PATH not found. SSH connections might require manual confirmation or fail."
else
  echo "$KNOWN_HOSTS_PATH found."
  echo "Permissions of $KNOWN_HOSTS_PATH:"
  ls -l "$KNOWN_HOSTS_PATH"
fi

# Configure Git with credentials from environment variables
if [ -n "$GIT_COMMIT_USER_NAME" ] && [ -n "$GIT_COMMIT_USER_EMAIL" ]; then
  echo "Configuring Git with user: '$GIT_COMMIT_USER_NAME', email: '$GIT_COMMIT_USER_EMAIL'"
  git config --global user.name "$GIT_COMMIT_USER_NAME"
  git config --global user.email "$GIT_COMMIT_USER_EMAIL"
  echo "Git global config user.name: $(git config --global user.name || echo 'not set')"
  echo "Git global config user.email: $(git config --global user.email || echo 'not set')"
else
  echo "Warning: GIT_COMMIT_USER_NAME or GIT_COMMIT_USER_EMAIL not set. Git commits may fail or use default credentials."
fi

# Attempt an SSH connection to GitHub to test keys and known_hosts
echo "Attempting SSH connection to GitHub (ssh -T git@github.com)..."
set +e # Temporarily disable exit on error
SSH_OUTPUT=$(ssh -o StrictHostKeyChecking=yes -o BatchMode=yes -T git@images-pype-dev-github.com 2>&1)
SSH_EXIT_STATUS=$?
set -e # Re-enable exit on error

echo "SSH Test Output: $SSH_OUTPUT"
echo "SSH Test Exit Status: $SSH_EXIT_STATUS"

if [ $SSH_EXIT_STATUS -eq 1 ] && echo "$SSH_OUTPUT" | grep -q "successfully authenticated"; then
  echo "SSH connection test to git@images-pype-dev-github.com SUCCEEDED (authenticated)."
elif [ $SSH_EXIT_STATUS -eq 0 ]; then # Should not happen with -T and no shell
  echo "SSH connection test to git@images-pype-dev-github.com SUCCEEDED (exit 0, unexpected for -T)."
else
  echo "SSH connection test to git@images-pype-dev-github.com FAILED. Exit status: $SSH_EXIT_STATUS"
fi
# StrictHostKeyChecking=yes will use known_hosts and fail if host key changed or not present.
# BatchMode=yes prevents password prompts.

echo "--- Docker Entrypoint: Setup Complete, Executing Command ---"
# Start the application (passed as arguments from docker-compose command)
# exec "$@"
uv run app/shotput.py
