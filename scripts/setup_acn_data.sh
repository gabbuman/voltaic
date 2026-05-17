#!/usr/bin/env bash
#
# Idempotently clone the ACN-Data static mirror to a sibling folder.
# The dataset is the SOURCE of the project (not output), and is large
# (~1-3 GB across 85K compressed files), so it lives OUTSIDE this repo.
#
# After this script runs, the data will be at:
#   ../voltaic-data/acn-data-static/
#
# Re-running is a no-op (just prints status). To force a fresh clone,
# delete the target folder and re-run.

set -euo pipefail

# Resolve repo root regardless of where the script is invoked from.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_PARENT="$(cd "${REPO_ROOT}/.." && pwd)/voltaic-data"
TARGET="${DATA_PARENT}/acn-data-static"
REMOTE="https://github.com/tongxin-li/ACN-Data-Static.git"

echo "Repo root:    ${REPO_ROOT}"
echo "Target path:  ${TARGET}"
echo "Source:       ${REMOTE}"
echo

if [[ -d "${TARGET}/.git" ]]; then
  echo "OK  Already cloned at ${TARGET}"
  echo "    To refresh: cd '${TARGET}' && git pull"
  exit 0
fi

mkdir -p "${DATA_PARENT}"

echo "Cloning (this is large — first clone may take several minutes)..."
git clone --depth 1 "${REMOTE}" "${TARGET}"

echo
echo "Done. Size on disk:"
du -sh "${TARGET}" 2>/dev/null || echo "(du unavailable on this platform)"
