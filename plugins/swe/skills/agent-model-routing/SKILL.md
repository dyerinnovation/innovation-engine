---
name: agent-model-routing
description: Pick the right class of model for every agent you spawn (builder, reviewer, drafter, research spike, background filer), in any harness and with any provider. Reviewers get your strongest model; builders get a mid-tier model when the brief is a concrete edit list and the strongest when it says "decide how"; mechanical filing gets a small, fast model. Every spawn names its model explicitly. Triggers on "which model for this agent", "spawn a builder/reviewer", "strong or cheap model", "model routing", or planning parallel agent work.
---

# Agent model routing

Route each spawned agent by its role and by the shape of its brief, not by habit. Every
spawn names its model explicitly; nothing silently inherits the session's model.

This skill speaks in model classes, not model names, because names change with every
launch and differ by provider. Map the classes to whatever your harness offers.

## The three classes

| Class | What it is | Typical members (check your harness for current ones) |
|---|---|---|
| **Strongest** | Your provider's top reasoning model. Slowest and priciest, best at judgment. | The flagship model of your provider or the largest open-weight model you run |
| **Mid-tier** | Strong and clearly cheaper. Excellent on a clear brief. | The provider's balanced or default model; a mid-size open-weight model |
| **Small** | Fast and cheap. Follows simple, fixed instructions; little judgment. | The provider's mini, lite or fast model; a small local model |

If your harness offers only one model, use it for everything and lean harder on the
reviewer step below. If it offers two, treat them as strongest and mid-tier.

## The table

| Role | Brief shape | Class | Why |
|---|---|---|---|
| Reviewer | any | **Strongest** | The reviewer is the merge gate. Misses here ship. Never economize on it. |
| Builder | well-scoped: a numbered fix list with file and line refs | **Mid-tier** | Much cheaper and strong on a clear brief. The reviewer still gates the merge, so a miss costs a fix round, not a bad merge. |
| Builder | design-heavy | **Strongest** | These briefs cause most extra fix rounds; the strongest model cuts them. |
| Background filer | mechanical, no judgment (save a paste, rename files) | **Small** | Verbatim work only; the main session checks the result. Never a builder or reviewer. |

### Well-scoped (mid-tier) examples
Reviewer fix rounds; one-file bug fixes; config or environment fixes; mechanical sweeps and
renames; drafting a document from a written brief; building a page from a spec.

### Design-heavy (strongest) examples
Spikes and design docs; concurrency, locking or state machines; cross-service contract
changes; strategy and pricing calls; anything whose brief says "decide how" rather than
"change X at Y". The orchestrating session itself belongs here too.

## Tie-breaker

If you cannot write the brief as a numbered list of concrete edits, it is design-heavy:
use the strongest class.

## Need more assurance? Add review depth, not a pricier builder

- A second reviewer with a different lens (correctness first, then security and operations).
- An adversarial pass that tries to refute the builder's claims.
- A completeness reviewer: "what did the brief imply that was not built?"

## Map the classes in your harness

- **Harnesses with short aliases** (for example a strong/default/fast trio): map them
  straight onto strongest, mid-tier and small.
- **Harnesses with a model picker or per-agent model setting:** set the model in each
  agent's definition or spawn call, not only the session default.
- **Open-source harnesses and local models:** list the models you have configured, rank
  them by quality on your own tasks, and assign the top one as strongest. A small local
  model is fine as the filer; be cautious using one as a reviewer.

## Verify the mapping once per session

Aliases and defaults change without notice. Have the first mid-tier or small agent report
the exact model it ran on as the first line of its report. If it is not what you expected,
move that agent up a class and say so.

## Reporting

Every status update names the class and the model each agent ran on, for example
`builder 2 (mid-tier, <model id>) pass · reviewer 2 (strongest) 1 high`.
