#!/usr/bin/env bash
# Fails when the live site is behind the newest release. Amplify builds main on every push and
# publishes nothing if a spec fails, so a broken build leaves the site (and its social previews)
# on the old version. The site publishes its own version in /data/leaderboard.json.
#
# The newest release gets GRACE_MIN minutes (default 30) to appear; after that a mismatch fails.
set -u
SITE="${SITE_URL:-https://biased-decisions.anth.us}"
GRACE_MIN="${GRACE_MIN:-30}"

git fetch --force --tags -q origin 2>/dev/null || true
tag=$(git tag --list 'v*' --sort=-v:refname | head -1)
[ -n "$tag" ] || { echo "no release tag found" >&2; exit 1; }
want="${tag#v}"
deadline=$(( $(git log -1 --format=%ct "$tag") + GRACE_MIN * 60 ))

while true; do
  live=$(curl -fsS -m 30 "$SITE/data/leaderboard.json" 2>/dev/null \
    | python3 -c "import json,sys; print(json.load(sys.stdin)['provenance']['release']['version'])" 2>/dev/null \
    || echo unreadable)
  if [ "$live" = "$want" ]; then echo "ok: $SITE is on $want"; exit 0; fi
  [ "$(date +%s)" -ge "$deadline" ] && break
  sleep 60
done
echo "::error::$SITE is on $live but the newest release is $want, more than $GRACE_MIN minutes old. The Amplify build for main is probably failing; check the Amplify console. Social previews stay stale until it deploys."
exit 1
