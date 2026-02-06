#!/usr/bin/env bash
set -eo pipefail

ROOT_PROJECT="/mnt/c/dev/python-email"

mkdir -p "$HOME/.local/bin" "$HOME/.local/lib/codacy"

# Locate JAR
if [ -f "$ROOT_PROJECT/tools/codacy/codacy-analysis-cli-assembly.jar" ]; then
  SRC="$ROOT_PROJECT/tools/codacy/codacy-analysis-cli-assembly.jar"
elif [ -f "$ROOT_PROJECT/tools/codacy-analysis-cli-assembly.jar" ]; then
  SRC="$ROOT_PROJECT/tools/codacy-analysis-cli-assembly.jar"
else
  echo "ERROR: codacy jar not found in project tools" >&2
  exit 2
fi

cp -f "$SRC" "$HOME/.local/lib/codacy/codacy-analysis-cli-assembly.jar"

# Copy or create wrapper
if [ -f "$ROOT_PROJECT/tools/codacy-cli" ]; then
  cp -f "$ROOT_PROJECT/tools/codacy-cli" "$HOME/.local/bin/codacy-cli"
else
  cat > "$HOME/.local/bin/codacy-cli" <<'WRAP'
#!/usr/bin/env bash
JAVA=$(command -v java || true)
if [ -z "$JAVA" ]; then
  echo 'Java not found. Please install Java (JRE) to run Codacy CLI.' >&2
  exit 1
fi
JAR="$HOME/.local/lib/codacy/codacy-analysis-cli-assembly.jar"
exec "$JAVA" -jar "$JAR" "$@"
WRAP
fi

# Ensure wrapper points to the global JAR
if [ -f "$HOME/.local/bin/codacy-cli" ]; then
  sed -i 's|JAR=.*|JAR="$HOME/.local/lib/codacy/codacy-analysis-cli-assembly.jar"|' "$HOME/.local/bin/codacy-cli" || true
  chmod +x "$HOME/.local/bin/codacy-cli"
fi

# Add ~/.local/bin to login PATH if missing
if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.profile" 2>/dev/null; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.profile"
fi

# Make available in current session and verify
export PATH="$HOME/.local/bin:$PATH"
hash -r

echo "codacy-cli version:"
codacy-cli --version || "$HOME/.local/bin/codacy-cli" --version || true

echo "Installed to: $HOME/.local/bin/codacy-cli and $HOME/.local/lib/codacy/"
