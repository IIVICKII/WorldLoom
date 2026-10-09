# Code map
Last updated: 2026-10-09
Skip: worldloom-output/, dist/, __pycache__/

## Entry points
- `PLAN.md` — approved phased plan, architecture tree, validator check list, phase log
- `CLAUDE_CODE_PLUGIN_PLANNING_PROMPT.md` — the original planning brief and requirements

- `README.md` — public overview: purpose, install from GitHub or local, claude.ai upload, how to modify and test
- `.claude-plugin/marketplace.json` — local marketplace `worldloom-local`; one plugin entry pointing at `./plugins/worldloom`
- `plugins/worldloom/.claude-plugin/plugin.json` — plugin manifest: name, version, description
- `LICENSE` — MIT licence text
- `.gitignore` — keeps generated stories, `dist/` and the two community scenarios out of the public repo
- `plugins/worldloom/README.md` — operator guide: commands, outputs, model switch, surfaces, tiers, troubleshooting

## tools/ and tests/
- `tools/build_skills.py` — generates the three stage skills and their source-derived references from `worldloom_source/`; holds every adaptation
- `tools/package.py` — builds `dist/worldloom-plugin.zip` and one zip per skill with `zipfile`
- `tests/test_scripts.py` — stdlib asserts: reference passes, content round-trip, 33 mutations rejected, 13 warning cases, CLI exit codes
- `tests/test_bible.py` — stdlib asserts for `check_bible.py`: sample bible passes, 13 mutations rejected, cast-size warning, run folders pass, CLI exit codes
- `tests/test_verbatim.py` — every source line is in the plugin; frontmatter, agent and manifest sanity

## plugins/worldloom/agents/
- `worldloom-architect.md`, `worldloom-critic.md`, `worldloom-compiler.md` — thin stage subagents; `model: inherit` and tools, then read the stage `SKILL.md`

## plugins/worldloom/skills/
- `worldloom/SKILL.md` — orchestrator: parses input and switches, finds Python, spawns the three agents with file paths, runs the bible checks, reports; chat fallback
- `worldloom/scripts/check_bible.py` — bible structure check and `--against` revision check (same entities, weights, labelled fields); warns on a Main Cast above the tier's size; exit 0/1
- `worldloom-bible/SKILL.md` — Stage 1 rules (P1), generated; writes `input.txt`, `bible_v1.txt`
- `worldloom-bible/references/genre-profiles.md` — KB_GENRE_PROFILES copy, generated; read every Stage 1 run
- `worldloom-critique/SKILL.md` — Stage 2 rules (P2), generated; writes `critique.md`, `bible_v2.txt`
- `worldloom-*/references/chat-mode.md` — original code-block output, CONTINUATION and COMMANDS for use without file tools, generated
- `worldloom-compile/SKILL.md` — Stage 3 rules (P3), generated; notes, content JSON, build and validate loop
- `worldloom-compile/references/content-schema.md` — shape of `scenario_content.json` and the entry roles; hand-written
- `worldloom-compile/references/manual-json.md` — P3 JSON skeleton and commands for use without Python, generated

## plugins/worldloom/skills/worldloom-compile/ (scripts and data)
- `scripts/build_scenario.py` — `scenario_content.json` + fixed blocks to `<Title>.scenario` or `.lorebook`; `--validate` runs the validator too; exports `build`, `system_prompt`, `prefill`
- `scripts/validate_scenario.py` — 16 deterministic checks plus warnings, exit 0/1; exports `validate`, `role_of`, `report`
- `assets/fixed_blocks.json` — FIXED_SETTINGS, DEFAULT_ENTRY, context configs, role table, Voice Guard and Prefill fixed text, tier caps; generated from P3
- `references/system-prompt-template.md` — P3 system-prompt template verbatim with slot markers; filled by the builder

## worldloom_source/ (read-only reference)
- `P1_STORY_BIBLE_ARCHITECT_INSTRUCTIONS.md` — Stage 1 rules: premise to seven-section Story Bible
- `KB_GENRE_PROFILES.md` — Genre Contract reference used by Stage 1
- `P2_EDITORIAL_CRITIQUE_INSTRUCTIONS.md` — Stage 2 rules: four-header critique plus revised bible
- `P3_NOVELAI_CONFIG_COMPILER_INSTRUCTIONS.md` — Stage 3 rules: bible to NOTES plus `.scenario` JSON, fixed blocks
- `WORLDLOOM_MODULAR_ARCHITECTURE.md` — operator guide: tiers, commands, Story So Far, troubleshooting
- `SAMPLE_TEST_BIBLE_FOR_P3.md` — compliant Tablet bible with a POV line; Stage 3 test input
- `The_Quiet_Ledger.scenario` — known-good Stage 3 output for the sample bible; test reference
- `Sages_Simple_Story_Setup_GLM.scenario`, `Blackfeather_Estate.scenario` — community scenarios the format came from; unused

## docs/
- `PROJECT.md` — project snapshot, commands, gotchas, handoff
- `DECISIONS.md` — significant choices and why
