#!/usr/bin/env bash
#
# Bump the project version in pyproject.toml AND keep server.json in lockstep,
# so the MCP Registry version always matches the PyPI release. pyproject.toml is
# the single source of truth; server.json is derived from it here.
#
# Usage:
#   scripts/bump.sh                  # patch bump (1.0.0 -> 1.0.1)
#   scripts/bump.sh minor            # 1.0.0 -> 1.1.0
#   scripts/bump.sh major            # 1.0.0 -> 2.0.0
#   scripts/bump.sh 1.4.2            # set an explicit version
#   scripts/bump.sh patch --release  # bump, commit, tag vX.Y.Z and push (triggers CI publish)
#
set -euo pipefail
cd "$(dirname "$0")/.."

PART="patch"
RELEASE=0
for a in "$@"; do
  case "$a" in
    --release) RELEASE=1 ;;
    *)         PART="$a" ;;
  esac
done

# Bump pyproject.toml (--no-sync: re-lock without rebuilding the venv)
case "$PART" in
  major|minor|patch|stable|alpha|beta|rc|post|dev)
    uv version --bump "$PART" --no-sync ;;
  *)
    uv version "$PART" --no-sync ;;   # explicit version string
esac

VERSION="$(uv version --short)"

# Derive server.json (top-level + package) from the new pyproject version
tmp="$(mktemp)"
jq --arg v "$VERSION" '.version = $v | .packages[0].version = $v' server.json > "$tmp"
mv "$tmp" server.json

echo "Bumped to $VERSION  (pyproject.toml + server.json)"

if [ "$RELEASE" = "1" ]; then
  git add pyproject.toml uv.lock server.json
  git commit -m "Release v$VERSION"
  git tag "v$VERSION"
  git push && git push --tags
  echo "Pushed v$VERSION — CI will publish to PyPI and the MCP Registry."
else
  echo "Next:"
  echo "  git add pyproject.toml uv.lock server.json"
  echo "  git commit -m \"Release v$VERSION\" && git tag v$VERSION"
  echo "  git push && git push --tags"
fi
