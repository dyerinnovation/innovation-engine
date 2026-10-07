#!/usr/bin/env bash
# Tests for detect-compaction.sh. Runs each phrase through the hook as
# UserPromptSubmit JSON, with jq and with the no-jq fallback.
set -u
here=$(cd "$(dirname "$0")" && pwd)
hook="$here/detect-compaction.sh"

positives=(
  "do the README fix and then I will compact"
  "ok let me compact and then we can do the deploy"
  "about to compact"
  "I'll /compact after this"
  "Finish the tests, then I'll compact."
  "before I compact, update the board"
  "I'm going to compact the session now"
  "gonna compact soon"
  "Wrap up, I need to compact the context"
  "let's compact here"
  "Time to compact."
  "commit everything before compaction"
  "I'm about to /compact"
  "Going to compact after you push the branch"
  "prep for compaction please"
  "LET ME COMPACT THEN WE CONTINUE"
  $'push it\nthen I\'ll compact'
  "I’ll compact after this"
  "compact after this is merged"
)
negatives=(
  "make the cards more compact"
  "use a compact layout on mobile"
  "let me see a compact version of the table"
  "I'll compact the CSS into one file"
  "the compact view looks cramped"
  "what does /compact do?"
  "compaction ratio of the database is high"
  "after compaction you forgot the branch name"
  "compact JSON output please"
  "Can you make it compact and then ship it"
  ""
  "the last compact lost context"
)

json_of() { # $1 = prompt; build hook stdin JSON
  if command -v jq >/dev/null 2>&1; then
    jq -cn --arg p "$1" '{session_id:"t",hook_event_name:"UserPromptSubmit",cwd:"/tmp",prompt:$p}'
  else
    python3 -c 'import json,sys; print(json.dumps({"session_id":"t","hook_event_name":"UserPromptSubmit","cwd":"/tmp","prompt":sys.argv[1]}))' "$1"
  fi
}

pass=0; fail=0
check() { # $1 = expect (1 match / 0 none), $2 = prompt, $3 = PATH override label
  local out
  if [ "$3" = nojq ]; then
    out=$(json_of "$2" | env PATH="$nojq_path" bash "$hook")
  else
    out=$(json_of "$2" | bash "$hook")
  fi
  local got=0
  if [ -n "$out" ]; then
    got=1
    # A match must be valid JSON with the documented shape.
    if command -v jq >/dev/null 2>&1; then
      printf '%s' "$out" | jq -e '.hookSpecificOutput.hookEventName == "UserPromptSubmit" and (.hookSpecificOutput.additionalContext | length > 0)' >/dev/null || got=bad
    fi
  fi
  if [ "$got" = "$1" ]; then pass=$((pass + 1)); else fail=$((fail + 1)); printf 'FAIL (%s, expect %s got %s): %q\n' "$3" "$1" "$got" "$2"; fi
}

# A PATH with the usual tools but no jq, for the fallback path.
nojq_path=$(mktemp -d)
for t in bash cat sed tr printf env; do
  p=$(command -v "$t") && ln -s "$p" "$nojq_path/$t"
done

for mode in jq nojq; do
  for p in "${positives[@]}"; do check 1 "$p" "$mode"; done
  for p in "${negatives[@]}"; do check 0 "$p" "$mode"; done
done
rm -rf "$nojq_path"

printf '%d positives, %d negatives, 2 modes: %d passed, %d failed\n' "${#positives[@]}" "${#negatives[@]}" "$pass" "$fail"
[ "$fail" -eq 0 ]
