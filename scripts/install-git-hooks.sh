#!/bin/sh

set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_dir=$(CDPATH= cd -- "$script_dir/.." && pwd)
hooks_dir="$repo_dir/.git/hooks"

mkdir -p "$hooks_dir"

cat << 'EOF' > "$hooks_dir/pre-commit"
#!/bin/sh

set -eu

echo "▸ Checking if generated code is in sync with contracts..."
make verify
EOF

chmod +x "$hooks_dir/pre-commit"
echo "✔ Git pre-commit hook installed successfully."
