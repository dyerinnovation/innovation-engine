#!/usr/bin/env bash
# UserPromptSubmit hook: when the user announces a compaction ("then I will
# compact", "about to /compact", "before compaction"), inject context telling
# the agent to run the swe:session-post-mortem skill before saying it is ready.
#
# Contract (Claude Code hooks reference, UserPromptSubmit): stdin is JSON with a
# `prompt` field; exit 0 with a hookSpecificOutput.additionalContext JSON object
# adds context; exit 0 with no output does nothing. It never blocks a prompt.
set -u

input=$(cat)

if command -v jq >/dev/null 2>&1; then
  prompt=$(printf '%s' "$input" | jq -r '.prompt // empty' 2>/dev/null) || prompt=$input
else
  # Fallback without jq: pull the "prompt" string out of the JSON with sed
  # (handles escaped quotes); escaped newlines become spaces below.
  prompt=$(printf '%s' "$input" | tr '\n' ' ' \
    | sed -nE 's/.*"prompt"[[:space:]]*:[[:space:]]*"(([^"\\]|\\.)*)".*/\1/p')
fi

# Normalize: lowercase, curly apostrophes to straight, escaped and real
# newlines/tabs to spaces, collapse runs of whitespace.
rsquo=$'\xe2\x80\x99'
text=$(printf '%s' "$prompt" | LC_ALL=C sed -e "s/${rsquo}/'/g" -e 's/\\[nrt]/ /g' \
  | tr '[:upper:]' '[:lower:]' | tr '\n\r\t' '   ' | tr -s ' ')

# 1. An announcement lead directly before "compact" (optionally /compact),
#    with an optional adverb between them.
lead="(i'll|i will|i'm going to|im going to|i am going to|going to|gonna|let me|let's|lets|about to|before i|then i'll|then|ready to|time to|need to|want to|we'll|we will|i'd like to|i should)"
adverb="(now |just |quickly |probably |go |then )?"
# 2. What may follow: end of text, punctuation, the session itself, or a
#    timing word. Anything else ("the layout", "the css") does not count.
tail="($|[[:space:]]*[.!?,;:)]|[[:space:]]+(the |this |my |our )?(session|context|conversation|chat|thread|window)|[[:space:]]+(after|afterwards|afterward|now|soon|next|once|when|here|first|shortly|right after|and then|then|in a (bit|minute|sec|second|moment)|real quick))"
re_announce="(^|[^a-z'])${lead}[[:space:]]+${adverb}/?compact${tail}"
# 3. "before/ahead of/prep for compaction".
re_compaction="(^|[^a-z])(before|ahead of|prep for|prepare for|ready for|then)[[:space:]]+(the |a )?compaction([^a-z]|$)"
# 4. "compact after this" / "/compact once you're done".
re_after="(^|[^a-z])/?compact[[:space:]]+(right )?(after|once) (this|that|you|we|it|the)"

if [[ $text =~ $re_announce || $text =~ $re_compaction || $text =~ $re_after ]]; then
  ctx="The user announced a context compaction. First finish any work they asked for in this message. Then, before compacting, run the swe:session-post-mortem skill over the whole session: list the churn, classify each item, propose fixes with sizes in one table, get per-item approval with AskUserQuestion, apply only approved items. End with a one-line ready-to-compact message."
  printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"%s"}}\n' "$ctx"
fi
exit 0
