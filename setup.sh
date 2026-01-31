#!/bin/bash
# Setup script for Docker environment

echo "Setting up Docker environment..."

# Create .env file with current user's UID/GID
cat > .env << EOF
# User and Group IDs for Docker (auto-generated)
USER_ID=$(id -u)
GROUP_ID=$(id -g)

# Other environment variables
QDRANT_URL=http://qdrant:6333
EOF

echo "Created .env file with USER_ID=$(id -u) and GROUP_ID=$(id -g)"

# Create necessary directories
mkdir -p input output qdrant_storage

echo "Setup complete! You can now run: docker-compose up -d"
