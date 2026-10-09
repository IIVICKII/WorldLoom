# Worldloom plugin — plan

## Context

Worldloom runs today as three Claude Projects (bible architect, critique, NovelAI compiler) joined by manual copy-paste. Goal: one plugin that takes a premise and produces `bible_v1.txt`, `critique.md`, `bible_v2.txt`, `notes.md` and a validated `<Title>.scenario` in one run, at equal or better quality, on Claude Code, Cowork and claude.ai chat, with the stage skills also usable alone on the Free plan.

Source of truth: `worldloom_source/` (all nine files read in full). Decisions already taken with you: install Python 3 via winget; you paste the install commands in an interactive `claude` terminal (CLI is not on PATH here).

## 1. Architecture

`C:\Users\ASUS\Documents\WorldLoom` becomes the marketplace root.

```
WorldLoom/
  .claude-plugin/marketplace.json          marketplace "worldloom-local", one entry -> ./plugins/worldloom
  plugins/worldloom/
    .claude-plugin/plugin.json             name "worldloom", version, description, author, license
    README.md                              usage, commands, model switch, surfaces
    agents/
      worldloom-architect.md               Stage 1 subagent, model: opus,   tools: Read, Write
      worldloom-critic.md                  Stage 2 subagent, model: sonnet, tools: Read, Write
      worldloom-compiler.md                Stage 3 subagent, model: sonnet, tools: Read, Write, Bash
    skills/
      worldloom/SKILL.md                   orchestrator: parse input + switches, spawn agents, report
      worldloom-bible/
        SKILL.md                           P1 rules
        references/genre-profiles.md       KB_GENRE_PROFILES.md, verbatim
        references/chat-mode.md            P1 code-block output format, CONTINUATION, COMMANDS
      worldloom-critique/
        SKILL.md                           P2 rules
        references/chat-mode.md            P2 code-block format, CONTINUATION, COMMANDS
      worldloom-compile/
        SKILL.md                           P3 rules (reading, T0, field rules, lorebook, budget fit, self-check)
        references/system-prompt-template.md   P3 template, verbatim, with slot markers
        references/content-schema.md       shape of scenario_content.json the model writes
        references/manual-json.md          P3 "THE SCENARIO JSON" section + CONTINUATION + COMMANDS (no-script path)
        assets/fixed_blocks.json           FIXED_SETTINGS, DEFAULT_ENTRY, context configs, comma group, role table, Voice Guard and Prefill fixed text
        scripts/build_scenario.py          content JSON + fixed blocks -> <Title>.scenario or .lorebook
        scripts/validate_scenario.py       deterministic checks -> validation.txt, exit 0/1
  tests/test_scripts.py                    stdlib asserts: reference passes, round-trip, mutations rejected
  tools/package.py                         builds dist/worldloom-plugin.zip + one zip per skill (zipfile, forward slashes)
  docs/PROJECT.md, docs/CODEMAP.md, docs/DECISIONS.md, PLAN.md    required by CLAUDE.md
```

How it connects:
- `/worldloom:worldloom <input block> [--pause] [--skip-critique]` loads the orchestrator skill. It checks the four required fields (asks once if missing, as P1 says), strips `POV:` for Stage 3, then spawns `worldloom-architect` → `worldloom-critic` → `worldloom-compiler`, passing only file paths. It never reads a bible into its own context.
- Each agent body is ~10 lines: "Read `${CLAUDE_PLUGIN_ROOT}/skills/<stage>/SKILL.md` and follow it; paths are in the task message; write full prose, ignore any terse-output mode." Frontmatter adds `omitClaudeMd: true` so your CLAUDE.md (caveman/ponytail rules) does not reach stage prose. Rules live only in skills: one copy, used by agents, chat, and standalone upload.
- Single-stage commands are the stage skills themselves:
  - `/worldloom:worldloom-critique <bible path>` — critique only (`--critique-only` = P2's CRITIQUE ONLY).
  - `/worldloom:worldloom-compile <bible path>` — compile only; `TIER: <name>` / `POV: <...>` re-compile; `--lorebook` emits `<Title>.lorebook`.
  - `/worldloom:worldloom-bible <input block>` — bible only.
- SKILL.md frontmatter uses only `name` and `description` (anything else is a hard error on claude.ai upload). No `bin/` (blocks chat/Cowork install).
- Chat fallback (agents ignored): the orchestrator skill says "no Agent tool → apply the three stage skills in sequence yourself; before Stage 2 re-read the bible from the file and treat it as another author's work". Files go to the code sandbox and scripts run there. With no file or code tools at all, each stage follows its `chat-mode.md` (original code-block output, CONTINUE) and Stage 3 follows `manual-json.md` (hand-written JSON, as today).

## 2. Source mapping and adaptations

| Source | Destination | Adaptation and reason |
|---|---|---|
| P1 instructions | `worldloom-bible/SKILL.md`, verbatim | OUTPUT FORMAT: "one code block" → "write plain text to the given path, first line `TIER: <tier>`" (file hand-off); the in-block formatting rules stay. CONTINUATION + COMMANDS → `chat-mode.md` (no cut-offs with file output; REVISE/TIER/GENRE still honoured as arguments). "knowledge file KB_GENRE_PROFILES" → "read `references/genre-profiles.md`". Missing-field question is returned to the orchestrator as `NEEDS_INPUT:` (a subagent cannot ask you). |
| KB_GENRE_PROFILES | `worldloom-bible/references/genre-profiles.md` | None. Read in full on every Stage 1 run. |
| P2 instructions | `worldloom-critique/SKILL.md`, verbatim | Output: critique → `critique.md`, revised bible → `bible_v2.txt` (same four headers, same in-block rules). CONTINUATION + COMMANDS → `chat-mode.md`. Incomplete bible → returns `REJECTED: <reason>`. |
| P3 instructions | `worldloom-compile/SKILL.md` + references | Every content rule stays verbatim in SKILL.md (INPUT, budgets, READING THE BIBLE, field map, T0 HORIZON, Memory, Author's Note, Phrase Bias rules, Prologue, banned-word rules, event-system rules, Prefill rules, Lorebook, budget order, Operator Reference, BUDGET FIT, SELF-CHECK). Moved: system-prompt template → reference file, read every compile, filled by the builder; JSON skeleton, FIXED blocks, id rule, role table → `fixed_blocks.json` + builder (text kept in `manual-json.md`); Voice Guard and Prefill fixed lines → `fixed_blocks.json`, model supplies only the extension and the three continuation lines. OUTPUT: NOTES → `notes.md`; JSON → `scenario_content.json` then built file. "parse it once to confirm" → validator. CONTINUATION, SYNC SCENARIO, PROLOGUE, TRIM, RECOUNT → `manual-json.md`. |
| Architecture guide | `README.md` (operator sections) + `docs/PROJECT.md` | Project-setup steps replaced by plugin usage; tiers, Story So Far upkeep, troubleshooting kept. |
| Sample bible, Quiet Ledger | stay in `worldloom_source/`; used by `tests/` | Not shipped in the plugin. |
| Sage / Blackfeather scenarios | stay in `worldloom_source/` | Reference only, unused. |

No rule is merged, weakened or dropped. No mature-content or adaptation features added.

## 3. Hand-off contract

All under `./worldloom-output/<slug>/` (slug = kebab-case Working Title; `-2` suffix on collision; Stage 1 creates it and returns the path).

| Stage | Reads | Writes | Returns to orchestrator |
|---|---|---|---|
| 1 | input block in task message | `input.txt`, `bible_v1.txt` | dir path, or `NEEDS_INPUT: ...` |
| 2 | `bible_v1.txt` path | `critique.md`, `bible_v2.txt` | `OK`, or `REJECTED: ...` |
| 3 | `bible_v2.txt` (or v1 with `--skip-critique`), POV/TIER override | `notes.md`, `scenario_content.json`, `<Title>.scenario`, `validation.txt` | `PASS n/n` or `FAIL` + remaining errors |

- Bibles are plain text, no code fence, first line `TIER: <tier>`.
- Stage 3 loop: write content → `build_scenario.py` → `validate_scenario.py --tier <tier>`. On exit 1, read `validation.txt`, fix `scenario_content.json`, rebuild. Maximum 3 attempts, then stop and report the remaining errors; the file is kept but marked FAILED in the final message.
- `--pause`: stop after Stage 1 and print the bible path. Resume by saying "continue" or by running the stage skills on the path.
- A stage returning `NEEDS_INPUT` / `REJECTED` stops the run with that message; nothing is retried blindly.
- Final message: scenario path, `validation.txt` summary (checks passed / total, warnings), token use per stage.

## 4. Validator checks and builder decision

**Builder: recommended.** Measured on `The_Quiet_Ledger.scenario`: 32.7k characters compact, of which about 13.7k are story-specific once the system-prompt template, prefill body and Voice Guard body are assembled by script. Stage 3 output drops from about 8.5k to about 4k tokens, and fixed blocks, ids, role settings and template headers can no longer be miscopied. The model still writes every creative and judgement field. If budget fit needs tightened system-prompt wording, the content file may carry a full `systemPromptOverride`; the validator checks it the same way. The validator always runs on the assembled file.

**Errors (fail the file):**
1. JSON parses; top-level keys in the exact order; `scenarioVersion` 3; `author` "Worldloom"; `ephemeralContext`, `placeholders` empty; `bannedSequenceGroups` exact.
2. `settings` equals FIXED_SETTINGS; `contextDefaults` (incl. DEFAULT_ENTRY), `storyContextConfig`, both `context[].contextConfig` blocks, first phrase-bias group equal the fixed values.
3. `lorebook`: `lorebookVersion` 6, `settings.orderByKeyLocations` false, `categories` `[]`.
4. Every entry equals DEFAULT_ENTRY outside the allowed fields; `displayName` non-empty; `category` "".
5. Ids match `00000000-0000-4000-8000-` + 12-digit counter, start at 1, rise by one, unique.
6. Entry order: Core Memory, Voice Guard, Characters, Story So Far, optional Glossary, keyed entries (500 before 450), Operator Reference last.
7. Role table per entry: activation, `budgetPriority`, `trimDirection`, `searchRange` (keyed `Type: character` → 4000, else 1000); always-on entries and Operator Reference have `keys` `[]`; keyed entries have keys; Operator Reference `enabled` false and starts with the fixed warning line.
8. Entry text: no `----`, `***`, `Keys:`, `Category:` lines, no empty `Key:` value; Voice Guard carries the four fixed lines; Characters starts `Characters:`.
9. Story So Far: `Story So Far` / `Type: memory` / `Earlier:` list or `Earlier: nothing yet` / `Upcoming (not happened yet):` list or `nothing yet`; no `Now:` line.
10. Memory is one line `[ Author: …; Title: <title>; Tags: …; Genre: … ]` and the title equals `title`.
11. Author's Note line 1 starts `[ Write in a style that conveys the following:`.
12. Prologue has no blank lines.
13. System prompt: every `##` header present in order, the two fixed `NEVER use` lines and the Names line intact, no unfilled slot markers, Examples block absent on Tablet. Prefill: voice line, appositive line, ends `---\n[Story continues:]`.
14. Phrase bias: one or two story groups, 4–8 single lowercase words each, |bias| ≤ 0.5, `generateOnce` matches the sign.
15. Banned names (Elara, Lyra, Thorne, Valerius, Kael, Kaelen, Ava, Marcus), whole word, anywhere except the system prompt's Names line.
16. Budgets at characters ÷ 4: Author's Note ≤ AN_CAP, System Prompt ≤ SP_CAP, lorebook texts minus Operator Reference ≤ LB_CAP, for `--tier`.

**Warnings (reported, do not fail):** Core Memory outside CM_RANGE (the reference file is 233 against 250–350, so this cannot be an error); key count outside 4–6; duplicate keys across entries; fewer than six quoted lines in the Prologue (the rule can lapse); premise-leak words in triggerable entries.

`--lorebook` mode applies checks 3–9 to a `.lorebook` file.

## 5. Models

| Stage | Model | Reason |
|---|---|---|
| 1 architect | `opus` | Most judgement: genre contract, timeline relocation, cast necessity, voices. |
| 2 critic | `sonnet` | Bounded edit under hard constraints; a different model from the author adds independence. |
| 3 compiler | `sonnet` | T0 judgement and the Prologue (the most imitated text) need prose quality. |

Haiku for Stage 3: the builder and validator remove the mechanical risk, so viability depends only on Prologue and T0 quality. Phase 4 runs the sample bible once on Sonnet and once on Haiku and reports validator result, retries, tokens, and both Prologues side by side for you to judge. Default stays Sonnet.

To change: edit the one `model:` line in `plugins/worldloom/agents/<agent>.md`, then `/reload-plugins`. (A local-path marketplace is loaded in place, so no reinstall.) README documents this.

## 6. Token estimate (input loaded per stage, characters ÷ 4)

| Stage | Today | Plugin | Note |
|---|---|---|---|
| 1 | 9.1k | ~8.9k | 5.6k skill + 3.3k genre profiles, still read every run for quality. |
| 2 | 3.1k | ~3.0k | Continuation/commands moved out. |
| 3 | 12k | ~10.7k | 8.3k skill + 2.4k template reference; JSON skeleton and fixed blocks never loaded. |
| Orchestrator | — | ~0.5k | Holds paths only. |

Input savings are small by design (rules are preserved). The real saving is Stage 3 output, about 8.5k → 4k tokens, plus no bible round-trip through your own context. Measured numbers replace these estimates in Phase 4.

## 7. Execution phases (one at a time, stop after each)

**Phase 0 — Setup.** Goal: tools and memory files exist.
- [x] `winget install Python.Python.3.12`; confirm `python --version`.
- [x] Write `docs/PROJECT.md`, `docs/CODEMAP.md`, `docs/DECISIONS.md`; copy this plan to `PLAN.md`.
- Done when: Python runs; memory files exist. Rollback: `winget uninstall Python.Python.3.12`.

**Phase 1 — Scripts.** Goal: builder and validator proven against the reference.
- [x] `assets/fixed_blocks.json`, `scripts/build_scenario.py`, `scripts/validate_scenario.py`, `tests/test_scripts.py`.
- Verify: `python tests/test_scripts.py` — reference passes all checks; content extracted from the reference rebuilds to a JSON-equal file; each of about 12 mutations (changed temperature, duplicate id, `Now:` line, blank Prologue line, banned name, non-empty categories, swapped keys, wrong priority, keyed Operator Reference, over-cap lorebook, missing header, altered comma group) is rejected with the right check number.
- Risk: template text drifts from P3. The round-trip test catches it.

**Phase 2 — Skills, agents, manifest.** Goal: plugin tree complete.
- [x] Three stage skills with references, orchestrator skill, three agents, `plugin.json`, `marketplace.json`, `README.md`.
- [x] Diff check: a script confirms every non-blank line of P1, P2, P3 appears in the plugin tree (SKILL.md or a reference), except the lines listed in section 2.
- Verify: diff check prints zero unexplained lines; JSON manifests parse.

**Phase 3 — Package and install.** Goal: installed and visible.
- [x] `python tools/package.py` → `dist/worldloom-plugin.zip`, `dist/worldloom.zip`, `dist/worldloom-bible.zip`, `dist/worldloom-critique.zip`, `dist/worldloom-compile.zip` (each skill folder as the zip's top level).
- [x] You run, in an interactive `claude` terminal:
  ```
  claude plugin validate "C:\Users\ASUS\Documents\WorldLoom"
  claude plugin marketplace add "C:\Users\ASUS\Documents\WorldLoom"
  claude plugin install worldloom@worldloom-local
  claude plugin list
  ```
- Done when: validate prints `Validation passed`; list shows `worldloom@worldloom-local … enabled`; I confirm the entry in `~/.claude/plugins/installed_plugins.json`; `/worldloom:worldloom` appears in a new session. Uploads to claude.ai (Customize → Plugins → Upload plugin; Customize → Skills) are yours to do with the zips.
- Rollback: `claude plugin marketplace remove worldloom-local`.

**Phase 4 — Tests.** See section 8. Done 2026-10-08; results in the Phase log.

## 8. Test plan

| Test | Pass criteria |
|---|---|
| A. Stage 3 alone on `SAMPLE_TEST_BIBLE_FOR_P3.md` (Sonnet) | Validator exit 0 within 3 attempts. Structural match with `The_Quiet_Ledger.scenario`: same top-level keys, same always-on entries, same four characters and House Varlen entry roles, Operator Reference last, first-person-past Prologue with ≥ 6 attributed lines, no Examples block. Text differs; structure does not. |
| A2. Same on Haiku | Same criteria; reported side by side with A. |
| B. Full run on a short invented premise (Tablet) | All six output files present; `critique.md` has the four headers; named entities identical between v1 and v2; validator exit 0; orchestrator context never contained the bible. |
| C. Broken scenario | Phase 1 mutation suite: every mutation rejected. |
| D. Chat fallback, dry | In this session without spawning agents, the orchestrator's sequential path produces the same files. Real claude.ai test is yours after upload. |

Token use per run comes from each subagent's reported usage and is listed per stage in the Phase 4 report.

## 9. Risks and open questions

- Caveman/ponytail SessionStart hooks may still reach subagents despite `omitClaudeMd`. Mitigation: agent bodies order full prose; Test B checks the bible reads normally.
- `omitClaudeMd` needs Claude Code v2.1.271+; older versions ignore it silently.
- Plugin skill names are long (`/worldloom:worldloom-compile`) because Free-plan standalone skills need self-explanatory names that match their folder. Say so if you prefer short aliases (`/worldloom:compile`) via `commands/`.
- Cowork and claude.ai behaviour is taken from the docs, not tested here; Free-plan code execution for the scripts is unconfirmed, hence the `manual-json.md` path.
- Git: folder is not a repository; nothing is committed unless you ask.

## Sources

- https://code.claude.com/docs/en/plugins-reference (manifest, layout, path variables, `bin/`)
- https://code.claude.com/docs/en/plugin-marketplaces (marketplace.json, add/install/validate, local path loads in place)
- https://code.claude.com/docs/en/sub-agents (frontmatter, `model`, fresh context, `omitClaudeMd`, plugin-agent limits)
- https://code.claude.com/docs/en/skills (frontmatter, `${CLAUDE_SKILL_DIR}`, namespacing, 500-line guidance)
- https://code.claude.com/docs/en/plugins/components (commands vs skills, agents)
- https://claude.com/docs/plugins/platform-support (chat ignores agents and hooks; commands load as skills)
- https://claude.com/docs/plugins/build and https://claude.com/docs/skills/how-to (zip shape, spec-only frontmatter, scripts in chat sandbox)

## 10. Improvement plan, Phases 5–8 (approved 2026-10-09)

Context: Phase 4 passed, but several rules were checked only by hand. Both new-premise lorebooks sat near 2,190 of the 2,200 cap, above the 2,024 fit target, and the validator printed no numbers. Prologue rules beyond layout were unchecked. The leak scan skipped always-on entries. Nothing checked Stage 1 structure or Stage 2's "revise, don't recast". Stage 3 cost 51k to 87k tokens over 13 to 21 tool turns. `python`, `python3` and `py` all failed in the session shell.

Outcome: more rules checked by script, fewer Stage 3 turns, a run that finds Python itself. No stage rule text changes. Every new check on creative content is a warning, never an error.

Constraints: `worldloom_source/` and `CLAUDE.md` untouched; stage `SKILL.md` files change only through `tools/build_skills.py`, and only in plugin-added lines; stdlib only; no `bin/`.

**Phase 5 — Validator: numbers and warnings.** Goal: `validation.txt` reports the budget numbers and warns on the rule breaks seen in Phase 4.
- [x] Budget lines in the report (`INFO`): Author's Note, System Prompt, Lorebook against cap and fit target (`cap × 0.92`), and one line per entry.
- [x] Warning when a capped field is over its fit target but within the cap.
- [x] Prologue warnings: last spoken line attributed to the player character; ends with `?`; appositive after a speech verb; `not … but …`.
- [x] Leak scan widened to Core Memory, Characters, Glossary, Memory, Author's Note and the Prologue. Story So Far stays exempt.
- [x] Small warnings: bias word already in a `NEVER use` line; ATTG Genre not among `tags`; tag not lowercase; a cast name in the Author's Note; duplicate keys compared case-insensitively.
- [x] Tests: a `WARNINGS` list in `tests/test_scripts.py`, one case per new warning; assert the report has the budget lines.
- [x] Run on the reference and the four Phase 4 scenarios; tighten any heuristic that fires on a correct file.
- Files: `validate_scenario.py`, `tests/test_scripts.py`, plugin `README.md`.
- Done when: the 33 mutations still fail on the same check; each new warning fires on its own mutation and not on the reference.
- Verify: `python tests/test_scripts.py` · `python tests/test_verbatim.py` · validator on `worldloom-output/*/*.scenario`.
- Risks / rollback: false-positive warnings cost the compiler a turn. No git; rollback is the copy of the validator inside `dist/worldloom-compile.zip`.

**Phase 6 — Bible checks for Stages 1 and 2.** Goal: a script stops the run early when Stage 1's bible is malformed or Stage 2 changed the cast list or the field layout.
- [x] `plugins/worldloom/skills/worldloom/scripts/check_bible.py FILE [--against V1]`, exit 0/1, prints only PASS/FAIL lines and the offending names or labels. Structure: `TIER:` line, seven section headings in order, one `Player Character:` line, no code fence, no banned name. `--against`: identical named entities (the line before each `Narrative Weight:` line, plus the Player Character), identical `Narrative Weight:` and `Role:` values, identical sequence of labelled lines.
- [x] Orchestrator skill runs it after Stage 1 and, with `--against`, after Stage 2; on exit 1 it shows the lines and stops.
- [x] `tests/test_bible.py`: Phase 4 bibles pass; five mutations fail.
- [x] Check `tools/package.py` includes the new `scripts/` folder.
- Files: new `check_bible.py`, new `tests/test_bible.py`, orchestrator `SKILL.md`, `README.md`, `docs/CODEMAP.md`.
- Done when: the script passes on both Phase 4 runs and the sample bible; every mutation fails naming the fault.
- Verify: `python tests/test_bible.py` · `python tests/test_scripts.py` · `python tests/test_verbatim.py`.
- Risks / rollback: older bibles with other headings fail structure; the check runs only in the orchestrator's full run. Rollback: delete the script and test, remove the orchestrator's two steps.

**Phase 7 — One build-and-validate command, interpreter hand-off, version 1.1.0.** Goal: Stage 3 needs one command per attempt and never has to hunt for Python.
- [x] `build_scenario.py --validate [--tier T]`: builds, validates through the validator's own functions, writes `validation.txt`, exits with the validator's code.
- [x] `tools/build_skills.py`: the plugin-added Build and Validate steps become the one command; "If the task names a Python interpreter, use that path."; `notes.md` budget line copied from the report. Regenerate.
- [x] Orchestrator: resolve an interpreter once and pass `Python: <path>` to Stage 3; if none, the report says the scenario is unvalidated.
- [x] Orchestrator report prints the resume command when Stage 3 fails.
- [x] `plugin.json` version `1.1.0`; README updated; `python tools/package.py` (keep the 1.0.0 plugin zip as `dist/worldloom-plugin-1.0.0.zip`).
- [x] Tests: a `--validate` CLI case.
- Files: `build_scenario.py`, `tools/build_skills.py`, generated compile `SKILL.md`, orchestrator `SKILL.md`, `agents/worldloom-compiler.md`, `plugin.json`, `README.md`, `tests/test_scripts.py`, `dist/`.
- Done when: all three test files pass; both `claude plugin validate` commands pass; `dist/` rebuilt.
- Verify: the three test files · `python tools/package.py` · `claude plugin validate .` and `./plugins/worldloom`.
- Risks / rollback: regeneration drops a source line; `test_verbatim.py` catches it.

**Phase 8 — Reinstall and one measured live run.** Goal: confirm the changes hold in a real run and measure the Stage 3 saving.
- [x] User: `claude plugin update worldloom@worldloom-local` (else uninstall and install), then a new session.
- [x] Confirm the cache copy matches the source.
- [x] One full run on a new premise with no Python path given by hand; record tokens, tool uses and time per stage, whether both bible checks ran, warnings, lorebook against fit target.
- [x] Compare with Phase 4 and record in the Phase log. No target promised.
- Files: `docs/PROJECT.md`, this file, a new folder under `worldloom-output/`.
- Done when: the run ends with a validated scenario, both bible checks ran, tokens per stage are reported.
- Verify: the three test files; an independent validator run on the new scenario.
- Risks / rollback: `plugin update` with a local marketplace is unverified; fallback is uninstall and install. Full rollback: install from the kept 1.0.0 zip.

Not in this plan: edit-based Stage 2 revision; Haiku for Stage 3; short aliases; claude.ai upload tests; stale-`.scenario` warning.

## 11. Session model and quiet probe, Phases 9–10 (approved 2026-10-09)

Context: each stage agent pinned its model (architect `opus`, critic and compiler `sonnet`), so a run from a Sonnet session still used Opus for Stage 1. The user wants every stage to follow the session's model and effort. The interpreter search ran `python`, `python3` and `py -3` in a row, and the Windows `python3` Store stub printed "Python was not found…", which looked like an error.

Outcome: the session's model and effort control all three stages; the stub message is gone. No stage rule text changes.

**Phase 9 — Inherit model, quiet probe, version 1.2.0.** Goal: all three stages run on the session's model and effort, and the interpreter search prints no stub message.
- [x] The three agent files: `model: inherit`. No `effort` line.
- [x] `tests/test_verbatim.py`: the agent check accepts `inherit` as well as `opus`, `sonnet`, `haiku`.
- [x] Orchestrator `SKILL.md`, "Finding Python" step 1: one command that stops at the first working interpreter and hides the output of failed ones, in bash and PowerShell.
- [x] Plugin `README.md` "Models" section and root `README.md`: stages follow the session; how to pin one; cost note.
- [x] `plugin.json` version `1.2.0`; `python tools/package.py`.
- [x] Memory files; one commit; push.
- Files: three agent files, orchestrator `SKILL.md`, `tests/test_verbatim.py`, both READMEs, `plugin.json`, `docs/*`, this file.
- Done when: three test files print `ALL PASS`; both `claude plugin validate` commands pass; the probe prints only `python` on this machine; the commit is on `origin/main`.
- Verify: the three test files · `claude plugin validate .` and `./plugins/worldloom` · the probe command in bash and PowerShell.
- Risks / rollback: a Haiku session gives a weaker bible; an Opus session costs more than 1.1.0. One stage can be pinned again through its `model:` line. Rollback: `git revert`, bump the version, update.

**Phase 10 — Update the install and one live check.** Goal: confirm in a real run that model and effort follow the session.
- [ ] User: `claude plugin marketplace update worldloom-local`, then `claude plugin update worldloom@worldloom-local`, then a new session (fallback: uninstall and install).
- [ ] Confirm the cache copy is 1.2.0 and identical to the source.
- [ ] User runs `/worldloom:worldloom` on a new premise from a Sonnet session at a chosen effort level, in the stories folder.
- [ ] Record: model per stage; whether the three stage agents appear separately; no Store message; no `ls docs`; tokens per stage; validator result.
- [ ] Effort: compare with the session setting. If stages do not follow it, stop and propose passing effort from the orchestrator.
- [ ] Phase log and `docs/PROJECT.md`; commit and push.
- Files: `docs/PROJECT.md`, this file.
- Done when: a validated scenario from a 1.2.0 run, with the model per stage recorded.
- Verify: an independent validator run on the new scenario; the three test files.
- Risks / rollback: `marketplace update` from GitHub is untested; fallback is remove and re-add the marketplace. If inherit misbehaves, pin the models again and release 1.2.1.

Not in this plan: purging the old commits on GitHub (the user's step); the lorebook fit target; Haiku trials; claude.ai upload tests.

## Phase log

- 2026-10-08 — Phase 0 done. Python 3.12.10 installed per user with `winget install -e --id Python.Python.3.12 --source winget --scope user` (`--source winget` avoids the msstore agreement prompt). Created `docs/PROJECT.md`, `docs/CODEMAP.md`, `docs/DECISIONS.md`, `PLAN.md`. Deferred: none.
- 2026-10-08 — Phase 1 done. Added `fixed_blocks.json`, `build_scenario.py`, `validate_scenario.py`, `tests/test_scripts.py`. `python tests/test_scripts.py` passes: reference 16/16 (1 warning, Core Memory 233 under CM_RANGE), round-trip equal to the reference with key order, 33 mutations rejected by the expected check, CLI exit codes 0/1, lorebook mode. Changes from plan: `references/system-prompt-template.md` created now instead of Phase 2 (the builder reads it); a missing analytical-register ban line is a warning, not an error (P3 allows the operator to remove it). Deferred: `content-schema.md` to Phase 2 as planned.
- 2026-10-08 — Phase 2 done. Added `tools/build_skills.py` (generates the three stage `SKILL.md` files, `genre-profiles.md`, both `chat-mode.md` files and `manual-json.md` from `worldloom_source/`, so stage text is copied, not retyped), `content-schema.md`, the orchestrator skill, three agents, `plugin.json`, `marketplace.json`, `README.md`, `tests/test_verbatim.py`. `python tests/test_verbatim.py` passes with zero exceptions: every non-blank line of P1, P2, P3 and the genre profiles is in the plugin, and each stage's lines are in its always-loaded files except the output, continuation, command and JSON-skeleton lines moved to `chat-mode.md` / `manual-json.md`. `python tests/test_scripts.py` still passes. Changes from plan: the Voice Guard and Prefill fixed text stay in the compile `SKILL.md` as well as in `fixed_blocks.json` (the model needs them to extend them); the KB_GENRE_PROFILES line is kept and a pointer line added, instead of reworded. Measured input per stage at characters ÷ 4: Stage 1 9.4k (plan said 8.9k), Stage 2 3.4k (3.0k), Stage 3 12.9k (10.7k); section 6 underestimated because no rule text was dropped and plugin notes were added. Deferred: `claude plugin validate` to Phase 3 (CLI not on PATH here).
- 2026-10-08 — Phase 3 done. Added `tools/package.py`; `dist/` holds `worldloom-plugin.zip` and four skill zips. `claude plugin validate` passes for the marketplace and for `./plugins/worldloom` (the second caught unquoted `: ` in two skill descriptions; the generator now quotes them and `test_verbatim.py` guards it). User ran `marketplace add` and `install`; `installed_plugins.json` shows `worldloom@worldloom-local` 1.0.0 and the cache copy is identical to the source. Corrections to the plan: the bundled CLI lives under `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\...`, not `%APPDATA%`; a local-path marketplace install is a cache copy, not loaded in place, so section 5's "edit the model line, then /reload-plugins" is wrong: reinstall after an edit. Deferred: claude.ai uploads (user).
- 2026-10-08 — Phase 4 done. All validator results are PASS 16/16, 0 warnings, on the first build, re-checked outside the agent. A (Stage 3, Sonnet, sample bible): same top-level keys and the same 11 entry names and roles as `The_Quiet_Ledger.scenario`, Operator Reference last, first-person-past Prologue (2,379 characters, 10 paragraphs with speech), no Examples block; 51.1k tokens, 13 tool uses, 143 s. A2 (Haiku): same structure; Prologue 2,177 characters, 9 paragraphs with speech, but its last spoken line is the player character's, against the Prologue rule; 97.6k tokens, 18 tool uses, 271 s. Haiku cost more and took longer here, so the default stays Sonnet; both Prologues are in `worldloom-output/test-prologues.md`. B (full run, `the-clock-at-obermoos`): Stage 1 Opus 43.6k tokens, 281 s; Stage 2 Sonnet 49.2k, 157 s, given only the bible path, four critique headers, named entities and labelled-field sequence identical between v1 and v2; Stage 3 Sonnet 86.5k, 21 tool uses, 306 s; all eight files present; third person limited past with no POV line; bible prose is normal, not terse. Run total about 179k tokens. C: 33 mutations rejected. D (no subagents, `the-kettle-post`): the three stage skills run in sequence in one session produced the same file set. Findings: both new-premise lorebooks sit at about 2,190 of 2,200, over the 2,024 fit target; the validator checks the cap only. Test agents were told the full Python path because the session PATH predates the install. Section 6's output estimate (about 4k tokens) was not measured separately; subagent totals are reported instead. Deferred: claude.ai and Cowork tests (user); the Haiku decision (user).
- 2026-10-09 — Phase 5 done. `validate_scenario.py` now prints `INFO` budget lines (three capped fields against cap and fit target, plus each entry) and 12 new warnings: fit target, four Prologue habits, leak words in the always-on entries, Memory, Author's Note and Prologue, bias word already banned, ATTG genre not in tags, tag not lowercase, cast name in the Author's Note; duplicate keys compare case-insensitively. No check became an error. `tests/test_scripts.py`: 33 mutations still rejected by the same checks, 13 warning cases fire on their mutation and not on the reference. The reference still shows only its Core Memory warning. On the Phase 4 files: all four are over the lorebook fit target (2,090 to 2,195 of 2,024), and three have the player character speaking the last spoken line: Test A (Sonnet), A2 (Haiku) and B (Sonnet). Correction to the Phase 4 entry: that fault is not a Haiku-only fault; the reference file and the inline Test D file are the two that follow the rule. ATTG check changed from the plan: tags may hold setting tags too, so the warning is "a Genre item is missing from tags", not "Genre differs from tags". Installed plugin (cache copy, 1.0.0) is unchanged until Phase 7 and 8. Deferred: none.
- 2026-10-09 — Phase 6 done. Added `plugins/worldloom/skills/worldloom/scripts/check_bible.py` and `tests/test_bible.py`. The orchestrator skill now runs the check after Stage 1 and, with `--against`, after Stage 2, stops on exit 1, lists the result in its report, and skips the checks with a note when no Python runs; the no-subagent path runs them too. `python tests/test_bible.py` passes: the sample bible passes, 11 mutations fail naming the fault (plan said five), a reworded field and an added prose line pass, both Phase 4 run folders pass (v1 structure, v2 against v1). Changes from plan: labelled fields are matched against the fixed list of labels the bible format defines, not any `Label:` line, because bible prose has lines such as "The tea stall …: a counter" that a legitimate fix may reword; the Player Character line is compared too; banned-name hits are skipped on lines holding `→`, since Consistency Fixes may log a rename of a user-supplied name. `tools/package.py` needs no change (it zips every file under the skill). Not tested: a live orchestrator running the check (Phase 8). Deferred: none.
- 2026-10-09 — Phase 7 done. `build_scenario.py --validate [--tier T]` builds, validates through `validate_scenario.validate` and `report`, writes `validation.txt` beside the built file, prints the report and exits with the validator's code; the two separate commands still work. `tools/build_skills.py`: the compile skill's plugin-added steps 3 and 4 are now one build-and-validate command, the skill uses a `Python: <path>` line from the task when given, `notes.md` is written last with its numbers copied from the `INFO` lines, and the LOREBOOK and RECOUNT variants name the one command; regenerated, `tests/test_verbatim.py` passes with zero exceptions. Orchestrator skill: a "Finding Python" step (`python`, `python3`, `py -3`, then `%LOCALAPPDATA%\Programs\Python\Python3*`), a `Python:` line in the Stage 3 task, a not-validated statement when none is found, and the resume command in the report. `agents/worldloom-compiler.md` uses the given interpreter. `plugin.json` is 1.1.0; README updated; `dist/` rebuilt (plugin zip 19 files) with the old plugin zip kept as `worldloom-plugin-1.0.0.zip`. Verify: all three test files pass (a `--validate` case added: exit 0 and exit 1); `claude plugin validate .` and `./plugins/worldloom` pass; the one command on the Test D content file gives PASS 16/16 with the fit-target warning. Change from plan: a run made to fix warnings counts toward the three attempts, and a pass with warnings left is a pass (the plan did not say). Not tested: the orchestrator's interpreter search and the compiler's use of the `Python:` line in a live run (Phase 8); only the bash lookup command was run by hand. Deferred: none.
- 2026-10-09 — Phase 8 done. `installed_plugins.json` shows `worldloom@worldloom-local` 1.1.0 and `diff -rq` finds the cache copy identical to the source (the user's update worked; which command they used is not recorded). Full run on a new premise, `worldloom-output/the-withy-line/`, Tablet, no Python path given by hand: the orchestrator's search took `python` (3.12.10; `python3` is still the Store stub) and passed `Python: python` to Stage 3. Stage 1 Opus 43.4k tokens, 6 tool uses, 273 s; `check_bible.py` PASS 1/1. Stage 2 Sonnet 44.3k, 5 tool uses, 127 s; `--against` PASS 2/2. Stage 3 Sonnet 83.3k, 15 tool uses, 260 s; PASS 16/16 with 1 warning, confirmed by an independent validator run; all eight files present. Run total about 171k tokens. Against Phase 4 run B (43.6k / 49.2k / 86.5k, 21 tool uses, 306 s, total about 179k): Stage 3 saved 6 tool uses and 46 s but only about 3k tokens, because the compiler now spends its three builds fixing warnings instead of stopping at the first pass. No Prologue warning is left, so the last-spoken-line fault seen in three Phase 4 files did not survive this run. The one warning left is the lorebook at about 2,193 of 2,200, over the 2,024 fit target: the compiler reported it stopped because another fix would be a fourth build. The fit-target warning alone does not bring the lorebook down. All three test files pass. Deferred: none.
- 2026-10-09 — Phase 9 done. The three agents now have `model: inherit`; none sets `effort`, so the session's effort should apply (the docs imply it; unconfirmed until Phase 10). `tests/test_verbatim.py` accepts `inherit`. The orchestrator's Python search is one loop that stops at the first interpreter printing `Python 3.` and hides the rest; on this machine it prints only `python` in bash and in PowerShell, with no Store message. Both READMEs describe the session-model behaviour, how to pin a stage, and the cost note; the 170k-token figure is labelled as measured with Opus/Sonnet/Sonnet. `plugin.json` is 1.2.0; local `dist/` rebuilt. Verify: three test files pass; `claude plugin validate .` and `./plugins/worldloom` pass. Also since Phase 8, outside any phase: the repository went to GitHub (`IIVICKII/WorldLoom`, one squashed commit), a root `README.md` and MIT `LICENSE` were added, and `Documents\CLAUDE.md` was renamed by the user so it no longer loads in sibling folders. Not tested: a live run on 1.2.0 (Phase 10). Deferred: none.
