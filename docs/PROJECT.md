# Worldloom
Last updated: 2026-10-09 · Current phase: PLAN.md Phase 16 (release 1.4.0 and one live full run) in progress: released, waiting for the user's live run

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
- Installed: `worldloom@worldloom-local` 1.4.0, user scope, registered from the local WorldLoom folder (not GitHub) on this machine. Cache copy identical to the source. Update with the bundled `claude.exe` by full path (`claude` is not on PATH): `plugin marketplace update worldloom-local`, then `plugin update worldloom@worldloom-local`.
- Known issues (1.3.0 live runs, see the Phase 13 log): Stage 2's copy-and-edit can delete a neighbouring field line; the revision check catches it; from Phase 14 the critic gets one repair (in the source, not yet installed or proven live). A second run whose title gives the same slug overwrites the first run's folder. Stage 3's first draft still lands well over the lorebook cap (23% on six Main Cast at Scroll) and it can exceed three builds; it passed from build 3. Stage 3 as a subagent with the Edit tool is untested. Token counts are characters ÷ 4. Old commits with the former username are reachable by hash on GitHub until the repo is recreated.

## Next up
PLAN.md section 13, Phase 16: version 1.4.0, package, validate, push, update the install, then the user does one full run with the six-lead Scroll premise; record folder, repair, builds and tokens from the transcripts.

## Conventions and gotchas
- `worldloom_source/` is the source of truth. Stage rules carry over verbatim; every adaptation is listed in PLAN.md section 2.
- SKILL.md frontmatter: only `name` and `description`. Other keys are a hard error on claude.ai upload.
- No top-level `bin/` in the plugin: it blocks install on claude.ai and Cowork.
- The `claude` CLI is not on PATH. The desktop app is Store-packaged and bundles it at `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude-code\<version>\<hash>\claude.exe` (2.1.293 on 2026-10-08). Inside the app's own shells the same file appears under `%APPDATA%\Claude\...`; that path does not exist in a normal terminal. The user runs the install commands.
- Install copies the plugin to `~/.claude/plugins/cache/worldloom-local/worldloom/<version>`. It is not loaded in place: after any change under `plugins/worldloom`, update or reinstall and open a new session (or the session keeps running the old copy).
- A SKILL.md description containing `: ` must be double-quoted, or the YAML frontmatter fails and the skill loads with no metadata. `claude plugin validate ./plugins/worldloom` catches it; validating the marketplace root alone does not.
- Python 3.12.10 is at `%LOCALAPPDATA%\Programs\Python\Python312\python.exe`. Shells opened before the install still resolve `python` to the Microsoft Store stub (exit 49); use the full path or a new shell.
- Stage transcripts live in `~/.claude/projects/<folder slug>/<session id>/subagents/agent-*.jsonl`; each row carries `message.model` and `effort`, and the tool calls show every build. Use them to measure a run instead of screenshots.
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
Done: Phases 0-15; Phase 16 release steps: version 1.4.0, packaged, both manifests validate, pushed, install updated to 1.4.0. · Stopped at: Phase 16, the user's live full run (six-lead Scroll premise, new session in the stories folder). · Next: read the stage transcripts and record the folder used (expect `the-sixth-orb-2`), whether a Stage 2 repair ran, Stage 3 builds and lorebook per build, Edit against scripts, final RESULT; phase log; commit and push. · Open questions: whether six Main Cast is worth compiling at Scroll at all (Opus tier is the fallback).
