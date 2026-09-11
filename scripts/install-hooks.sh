#!/usr/bin/env bash
# One-time setup on a fresh clone: installs Playwright's headless Chromium and the pre-commit hook that runs the tests.
set -e
cd "$(dirname "$0")/.."
python3 -m pip install --user --quiet playwright 2>/dev/null || python3 -m pip install --user --quiet --break-system-packages playwright
python3 -m playwright install chromium-headless-shell 2>/dev/null || python3 -m playwright install chromium
cat > .git/hooks/pre-commit <<'HOOK'
#!/usr/bin/env bash
# Runs the data + click tests before every commit. Bypass a single commit with: git commit --no-verify
exec scripts/run_tests.sh
HOOK
chmod +x .git/hooks/pre-commit scripts/run_tests.sh
echo "hooks installed; try: scripts/run_tests.sh"
