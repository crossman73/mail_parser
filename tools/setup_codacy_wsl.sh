#!/bin/bash
# Codacy CLI Setup Script for WSL 2
# Run this script once to install Codacy CLI in WSL

set -e

echo "🔧 Codacy CLI Setup for WSL 2"
echo "=============================="

# Check if running in WSL
if ! grep -qi microsoft /proc/version 2>/dev/null; then
    echo "❌ This script must be run inside WSL"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq curl docker.io

# Add current user to docker group (if not already)
if ! groups | grep -q docker; then
    echo "🐳 Adding user to docker group..."
    sudo usermod -aG docker $USER
    echo "⚠️  Please log out and back in for docker group changes to take effect"
fi

# Download Codacy CLI
echo "📥 Downloading Codacy CLI..."
CODACY_CLI_VERSION="latest"
curl -Ls https://coverage.codacy.com/get.sh -o /tmp/codacy-coverage.sh
chmod +x /tmp/codacy-coverage.sh

# Create alias for codacy-cli
echo "🔗 Creating codacy-cli alias..."
ALIAS_CMD='alias codacy-cli="bash <(curl -Ls https://raw.githubusercontent.com/codacy/codacy-analysis-cli/master/bin/codacy-analysis-cli.sh)"'

# Add to .bashrc if not already present
if ! grep -q "codacy-cli" ~/.bashrc 2>/dev/null; then
    echo "" >> ~/.bashrc
    echo "# Codacy CLI alias" >> ~/.bashrc
    echo "$ALIAS_CMD" >> ~/.bashrc
fi

# Create a convenience script
cat > ~/codacy-analyze.sh << 'EOF'
#!/bin/bash
# Codacy Analysis Script
# Usage: ~/codacy-analyze.sh [file_or_directory]

PROJECT_DIR="${1:-/mnt/c/dev/python-email}"
cd "$PROJECT_DIR"

echo "🔍 Running Codacy Analysis on: $PROJECT_DIR"
echo "================================================"

# Run Codacy CLI via Docker
docker run \
  --rm \
  --env CODACY_CODE="$PROJECT_DIR" \
  --volume "$PROJECT_DIR":"$PROJECT_DIR" \
  --volume /var/run/docker.sock:/var/run/docker.sock \
  --volume /tmp:/tmp \
  codacy/codacy-analysis-cli \
  analyze --directory "$PROJECT_DIR" --format text

echo ""
echo "✅ Analysis complete!"
EOF
chmod +x ~/codacy-analyze.sh

echo ""
echo "✅ Codacy CLI Setup Complete!"
echo ""
echo "Usage:"
echo "  1. Run: source ~/.bashrc"
echo "  2. Navigate to project: cd /mnt/c/dev/python-email"
echo "  3. Analyze: ~/codacy-analyze.sh"
echo ""
echo "Or use the MCP tool in VS Code: codacy_cli_analyze"
