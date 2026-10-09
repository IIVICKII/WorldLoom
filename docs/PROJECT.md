# Worldloom
Last updated: 2026-10-09 · Current phase: PLAN.md Phase 9 (inherit model, quiet probe, 1.2.0) done; Phase 10 (update install, live check) next

## What it is
Worldloom turns a story premise into a NovelAI (GLM-4.6) `.scenario` file through three stages: Story Bible, editorial critique, config compile. It ran as three Claude Projects joined by copy-paste. This repo repackages it as one Claude plugin (`plugins/worldloom`) with a local marketplace at the repo root.

## Stack and commands
- Stack: Markdown skills and agents, JSON manifests, stdlib-only Python 3.12 scripts. No dependencies.
- Install: `claude plugin marketplace add "C:\Users\ASUS\Documents\WorldLoom"` then `claude plugin install worldloom@worldloom-local` (run by the user in an interactive `claude` terminal). On another machine: `claude plugin marketplace add IIVICKII/WorldLoom`, then the same install command (untested).
- Run: `/worldloom:worldloom <input block> [--pause] [--skip-critique]`
- Test all: `python tests/test_scripts.py`, `python tests/test_verbatim.py`, `python tests/test_bible.py`
- Check a bible: `python plugins/worldloom/skills/worldloom/scripts/check_bible.py BIBLE [--against ORIGINAL]`
- Regenerate stage skills after a source change: `python tools/build_skills.py`
- Build: `python plugins/worldloom/skills/worldloom-compile/scripts/build_scenario.py content.json [--out-dir DIR] [--lorebook] [--validate [--tier T]]` (`--validate` also writes `validation.txt` and exits 0/1)
- Validate: `python plugins/worldloom/skills/worldloom-compile/scripts/validate_scenario.py FILE [--tier Tablet|Scroll|Opus] [--lorebook] [--report validation.txt]`
- Package: `python tools/package.py` (writes `dist/*.zip`; re-run after any plugin change)
- Validate manifests: `claude plugin validate .` and `claude plugin validate ./plugins/worldloom`
- Lint/typecheck: none.

## Architecture
See PLAN.md section 1 for the full tree.
- Orchestrator skill spawns three subagents (architect, critic, compiler) and passes only file paths.
- Stage rules live once, in `skills/worldloom-*/SKILL.md`; agents are thin wrappers that read them.
- Stage 3 writes `scenario_content.json`; `build_scenario.py` assembles the `.scenario` from `fixed_blocks.json`; `validate_scenario.py` checks it.
- Outputs go to `./worldloom-output/<slug>/`.

## Current state
- Works: builder and validator (`tests/test_scripts.py` passes: 33 error mutations, 13 warning cases); validator report with `INFO` budget lines and heuristic warnings; `check_bible.py` (`tests/test_bible.py` passes); plugin tree (`tests/test_verbatim.py` passes, zero exceptions). Live 1.1.0 run `worldloom-output/the-withy-line/`: the orchestrator found Python itself, both bible checks ran and passed, Stage 3 ended PASS 16/16 with 1 warning. Earlier 1.0.0 runs: `the-clock-at-obermoos/`, `the-kettle-post/`, `test-a-sonnet/`, `test-a2-haiku/`.
- In progress: none.
- Installed: `worldloom@worldloom-local` 1.1.0, user scope. Source and GitHub are 1.2.0; the installed copy stays 1.1.0 (pinned models) until the user updates in Phase 10. Local `dist/` holds the 1.2.0 zips.
- Known issues: the lorebook still lands near the cap (about 2,193 of 2,200, fit target 2,024) in the 1.1.0 run; the compiler used its three builds and left that warning. The Prologue last-spoken-line fault did not recur in that run (one sample). claude.ai and Cowork are untested. Measured tokens per stage, 1.1.0: Stage 1 Opus 43.4k, Stage 2 Sonnet 44.3k, Stage 3 Sonnet 83.3k (15 tool uses, 260 s; 1.0.0 was 86.5k, 21, 306 s).

## Next up
PLAN.md section 11, Phase 10: the user runs `claude plugin marketplace update worldloom-local` and `claude plugin update worldloom@worldloom-local`, opens a new session, and runs one premise from a Sonnet session; record the model per stage, whether three separate stage agents appear, and whether effort follows the session.

## Conventions and gotchas
- `worldloom_source/` is the source of truth. Stage rules carry over verbatim; every adaptation is listed in PLAN.md section 2.
- SKILL.md frontmatter: only `name` and `description`. Other keys are a hard error on claude.ai upload.
- No top-level `bin/` in the plugin: it blocks install on claude.ai and Cowork.
- The `claude` CLI is not on PATH. The desktop app is Store-packaged and bundles it at `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude-code\<version>\<hash>\claude.exe` (2.1.293 on 2026-10-08). Inside the app's own shells the same file appears under `%APPDATA%\Claude\...`; that path does not exist in a normal terminal. The user runs the install commands.
- Install copies the plugin to `~/.claude/plugins/cache/worldloom-local/worldloom/<version>`. It is not loaded in place: after any change under `plugins/worldloom`, update or reinstall and open a new session (or the session keeps running the old copy).
- A SKILL.md description containing `: ` must be double-quoted, or the YAML frontmatter fails and the skill loads with no metadata. `claude plugin validate ./plugins/worldloom` catches it; validating the marketplace root alone does not.
- Python 3.12.10 is at `%LOCALAPPDATA%\Programs\Python\Python312\python.exe`. Shells opened before the install still resolve `python` to the Microsoft Store stub (exit 49); use the full path or a new shell.
- Budget estimates are characters ÷ 4. The reference scenario's Core Memory is 233, under CM_RANGE, so CM_RANGE is a warning only.
- The stage `SKILL.md` files, `genre-profiles.md`, `chat-mode.md` and `manual-json.md` are generated by `tools/build_skills.py`. Never hand-edit them; change the generator and re-run it. `content-schema.md`, the orchestrator skill, the agents and the README are hand-written.
- Stage agents use `model: inherit` and set no `effort`, so a run costs what the session's model costs. The token figures in this file were measured with Opus on Stage 1 and Sonnet on Stages 2 and 3.
- Agents read their stage `SKILL.md` as a plain file, so `${CLAUDE_SKILL_DIR}` is not substituted there. Stage skills use paths relative to "this skill's folder"; the agent body supplies the absolute folder through `${CLAUDE_PLUGIN_ROOT}`.
- `content-schema.md` uses placeholders only, no sample-story names, so test runs on the sample bible are not contaminated.
- `fixed_blocks.json` and `system-prompt-template.md` were lifted from the P3 text by a one-off script, not typed. If P3 changes, re-derive them; the round-trip test fails on any drift from the reference scenario.
- A missing analytical-register ban line in the system prompt is a validator warning, not an error: P3 lets the operator remove it. The ozone and Names lines are errors.
- Subagents inherit the stale PATH too: Phase 4 compile tasks were given the full Python path in the task message. Restart the app after installing Python, or the compiler agent has to hunt for an interpreter.
- `check_bible.py` compares only the labels the bible format defines (its `LABELS` list); any other `Something: …` line is prose. A new field in P1 must be added to that list. It skips banned-name hits on lines with `→`, because Consistency Fixes may log a rename of a name the user supplied.
- Git: public repo `https://github.com/IIVICKII/WorldLoom`, branch `main`. `.gitignore` keeps out `worldloom-output/`, `dist/` and the two community scenarios in `worldloom_source/`; a clean clone rebuilds `dist/` with `python tools/package.py`. Commits use the repo-local identity `IIVICKII` with the GitHub noreply address. The owner's real name must not appear in any file, manifest or commit: use `IIVICKII` everywhere.
- Build zips with Python `zipfile`, not `Compress-Archive` (backslash entry names).

## Do not touch
- `worldloom_source/` — read-only reference.
- `CLAUDE.md`.

## Handoff
Done: Phases 0–9. Phase 9: agents inherit the session model, quiet Python search in the orchestrator skill, READMEs updated, version 1.2.0, pushed. Earlier the same day: repo published at `IIVICKII/WorldLoom` with one squashed commit, root README, MIT licence. · Stopped at: end of Phase 9. · Next: Phase 10 on approval; it starts with the user's two update commands. · Open questions: does session effort reach the stage agents (unconfirmed); did the user's earlier run use three separate stage agents or one agent for everything; old commits on GitHub are still reachable by hash until the user deletes and recreates the repo; how to get the lorebook under the fit target; short command aliases wanted or not; keep the one-off `fixed_blocks.json` generator in `tools/` or not; claude.ai: the user has uploaded the three stage skills, not the `worldloom` orchestrator.
