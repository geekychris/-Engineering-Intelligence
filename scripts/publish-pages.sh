#!/usr/bin/env bash
set -euo pipefail

# Publishes site/ to the gh-pages branch on origin so GitHub Pages can serve it.
#
# Requires:
#   - site/ already assembled (run `make pages` first, or this will bail out).
#   - Pages source in the repo settings set to
#     "Deploy from a branch" -> gh-pages -> / (root).
#
# Uses a git worktree so your main checkout is never disturbed.

SITE_DIR="site"
BRANCH="gh-pages"
WORKTREE_DIR=".gh-pages-worktree"
REMOTE="origin"

if [[ ! -d "${SITE_DIR}" || ! -f "${SITE_DIR}/index.html" ]]; then
  echo "No ${SITE_DIR}/ found. Run 'make pages' first." >&2
  exit 1
fi

# Refuse to publish uncommitted tracked changes silently — the site should
# correspond to a real commit so its "built from <sha>" footer means something.
# Untracked files are fine; they don't affect HEAD.
if ! git diff-index --quiet HEAD --; then
  echo "Tracked files have uncommitted changes. Commit or stash before publishing." >&2
  exit 1
fi

commit_sha="$(git rev-parse HEAD)"
short_sha="${commit_sha:0:7}"

cleanup() {
  if [[ -d "${WORKTREE_DIR}" ]]; then
    git worktree remove --force "${WORKTREE_DIR}" >/dev/null 2>&1 || rm -rf "${WORKTREE_DIR}"
  fi
}
trap cleanup EXIT

rm -rf "${WORKTREE_DIR}"

if git ls-remote --exit-code --heads "${REMOTE}" "${BRANCH}" >/dev/null 2>&1; then
  git fetch "${REMOTE}" "${BRANCH}:${BRANCH}" 2>/dev/null || git fetch "${REMOTE}" "${BRANCH}"
  git worktree add "${WORKTREE_DIR}" "${BRANCH}"
else
  echo "Creating orphan ${BRANCH} branch (first publish)."
  # --orphan requires git >= 2.42
  git worktree add --orphan -b "${BRANCH}" "${WORKTREE_DIR}"
fi

# Wipe worktree contents (except .git) and copy the fresh site in.
find "${WORKTREE_DIR}" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp -R "${SITE_DIR}"/. "${WORKTREE_DIR}/"

pushd "${WORKTREE_DIR}" >/dev/null
git add -A
if git diff --cached --quiet; then
  echo "No changes to publish."
else
  git commit -m "Publish site from ${short_sha}"
  git push "${REMOTE}" "${BRANCH}"
  echo "Published ${short_sha} to ${REMOTE}/${BRANCH}."
fi
popd >/dev/null
