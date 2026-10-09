## 2026-10-08 — Builder script assembles the scenario
Why: only about 13.7k of 32.7k characters in the reference scenario are story-specific; a script removes fixed-block copy errors and roughly halves Stage 3 output tokens. · Alternatives: model writes the full JSON (kept only as the no-script fallback in `manual-json.md`).

## 2026-10-08 — Stage rules live in skills, agents are thin wrappers
Why: one copy of each rule set serves subagents, the chat fallback and Free-plan standalone upload. · Alternatives: rules in agent bodies (chat ignores agents; would need a second copy).

## 2026-10-08 — Stage skills double as the single-stage commands
Why: fewer files, and standalone skills need folder-matching names anyway. · Alternatives: thin `commands/` aliases such as `/worldloom:compile` (offered to the user, not built).

## 2026-10-08 — Python 3.12 via winget for the scripts
Why: the brief specifies stdlib Python, and claude.ai's code sandbox runs Python. · Alternatives: Node (already installed, but departs from the brief).

## 2026-10-08 — Models: Opus for Stage 1, Sonnet for Stages 2 and 3
Why: Stage 1 carries the most judgement; Stage 3 writes the Prologue, the most imitated text. · Alternatives: Haiku for Stage 3, to be measured in Phase 4 before any switch.

## 2026-10-08 — CM_RANGE and the six-line Prologue rule are warnings
Why: the known-good reference has a 233-token Core Memory, and the dialogue rule can lapse by design. · Alternatives: errors (would reject the reference).

## 2026-10-08 — Stage skills are generated from the source files
Why: the brief requires the stage rules verbatim. A generator copies source lines and applies a short, explicit list of adaptations, and `tests/test_verbatim.py` proves no line was lost. · Alternatives: hand-written SKILL.md files (rejected: retyping 85k characters invites silent drift); keeping the original code-block output rules in SKILL.md with an override note (rejected: two conflicting output rules in one document).

## 2026-10-08 — Agents are thin; rules live only in skills
Why: one copy of each stage's rules serves the subagents, the chat fallback and standalone skill upload. · Alternatives: full rules in each agent body (rejected: two copies to keep in sync, and chat ignores agents).

## 2026-10-09 — MIT licence, with credits to OccultSage
Why: the repo is public and the user wants others to be able to reuse it; MIT is short and permissive. The scenario format and settings draw on two OccultSage community scenarios, so the README credits them and the two files stay out of the repo. · Alternatives: GPL-3.0 (forces derivatives open, not wanted); Apache-2.0 (longer, patent grant not needed); no licence (blocks reuse).

## 2026-10-09 — Stages inherit the session's model and effort
Why: the user wants the model picker and effort setting to control the whole run; a Sonnet session still ran Stage 1 on Opus. `model: inherit` in each agent does it with no orchestrator logic, and leaving `effort` unset lets the session's level apply. · Alternatives: pinned Opus/Sonnet/Sonnet (rejected: ignores the session); inherit for Stage 1 only (rejected: two rules to remember); passing model and effort from the orchestrator on each spawn (rejected: more moving parts for the same result).
