---
name: feedback-triage
description: Triage and file everything the user pastes (command output, logs, chat messages, meeting notes, emails, review feedback, documents) so it survives context compaction. The main session decides what the paste means and answers at once; a background filer on a small, fast model saves it verbatim in a typed, dated folder under the project's evidence root. Triggers on "save this", "file this", "triage this paste", "log this", or any paste of logs, messages or notes when the project has an evidence root.
---

# Feedback triage

Evidence that lives only in the chat transcript is lost at compaction and re-derived by the
next session. This skill turns every paste into a file, named for its subject, in a typed
and dated folder, so any fresh session or agent can find it with `ls` and `grep`. The
folder tree is the index.

## The split

Two roles, one turn:

- **Main session (triage).** Reads the paste and decides what it means, who owns the next
  step, and what is still open. Answers the user right away.
- **Background filer (a small, fast model; mid-tier at most).** Saves the paste verbatim.
  It is dispatched in the same turn, in the background, so the user never waits on filing.

The main session never files by hand and never blocks on the filer. The filer never
thinks about meaning.

## When it fires

Every time the user pastes something: command output, logs, a chat message or thread,
meeting notes, an email, review or user feedback, a document. Also on "save this" and
"file this". To make it automatic, copy `rules/dispatch-on-every-paste.md` into the
project's `.claude/rules/` and set the evidence root in it.

## Main session steps

1. Read the paste. Decide the type (see the folder table) and a subject slug.
2. Write a short triage brief: meaning, who owns the next step, what is still open.
3. Dispatch the filer in the background: the `tpm:feedback-triage` agent this plugin
   ships, with the small model class named in the spawn (see `swe:agent-model-routing`).
   Pass the paste verbatim, the type, the subject slug, the date, the triage brief, the
   evidence root, and related paths if known.
4. Answer the user immediately. Do not wait for the filer.
5. When the filer replies with paths, verify: the file exists and `grep` finds the
   `## Raw` and `## Triage` headers. Only then tell the user it is saved, with the path.
   If verification fails, say so and re-dispatch once.

## Filing rules (the filer follows these)

- Root: the project's evidence root (default `docs/internal-docs/`).
- Folder: chosen by type from the table below. Dated folders use `M-D-YY` with no leading
  zeros (for example `10-2-26`).
- File name: the subject in kebab-case (`ci-build-failure.md`), never the session or the
  time. The same subject on the same day appends a new `##` section to the existing file.
- File layout:
  - `# <Subject> (<YYYY-MM-DD>)` and one context line (what it is, where it came from)
  - `## Raw`: the paste, verbatim, in a fenced block (use a fence longer than any fence
    inside)
  - `## Triage`: from the brief; if there is none, write `Triage: pending`
  - `## Related`: relative links to related files, back-linked both ways (edit the other
    file too, inside the evidence root only)

## Default folder table

| Type | Folder under the evidence root |
|---|---|
| Command output, logs, CI and deploy output | `logs/<M-D-YY>/` |
| Chat messages and threads | `messages/<M-D-YY>/` |
| Meeting notes | `meeting-notes/<M-D-YY>/` |
| Emails | `emails/` |
| Failure reports with no evidence yet | `errors/` |
| Review and user feedback | `feedback/<M-D-YY>/` |
| Decisions made, with who and when | `decisions/` |

## Hard rules

The filer:

- never diagnoses
- never runs commands against live systems
- never contacts anyone
- never writes secrets: redacts them to `<redacted>` and says so in its reply
- never edits outside the evidence root
- never commits or pushes
- replies with the paths only

The main session owns meaning, commits, and anything outward-facing.

## Setting it up in a project

1. Copy `profiles/_template.md` into the project's docs, set the evidence root, and adjust
   the folder table. Keep the hard rules unchanged.
2. Copy `rules/dispatch-on-every-paste.md` into the project's `.claude/rules/` and fill in
   the root.
3. Without the plugin installed, copy `${CLAUDE_PLUGIN_ROOT}/agents/feedback-triage.md`
   into the project's `.claude/agents/`.

## Demo

`demo/` holds four invented pastes for a fictional notes app and the exact files they
produce. Use it for a walkthrough.
