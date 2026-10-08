# Worldloom

A Claude plugin that turns a short story premise into a ready-to-import [NovelAI](https://novelai.net) `.scenario` file, tuned for the GLM-4.6 text model.

You write four short fields: a premise, the character dynamics, the character backgrounds and the genre tags. Worldloom writes a full story bible, has a second model critique and revise it, compiles the result into NovelAI's scenario format, and checks the file with a script before handing it to you.

```
premise ──► Stage 1 Story Bible ──► Stage 2 Critique ──► Stage 3 Compile ──► <Title>.scenario
            bible_v1.txt            critique.md           notes.md
                                    bible_v2.txt          validation.txt
```

## Contents

- [What it is for](#what-it-is-for)
- [How it works](#how-it-works)
- [Requirements](#requirements)
- [Install](#install)
- [Use](#use)
- [Modify](#modify)
- [Repository layout](#repository-layout)
- [Limits and known issues](#limits-and-known-issues)
- [Credits](#credits)
- [Licence](#licence)

## What it is for

Setting up a good NovelAI scenario by hand is slow. A scenario is more than an opening paragraph: it has a Memory block, an Author's Note, a System Prompt, a Prefill, a lorebook with per-entry insertion settings, phrase biases, sampler settings and a Prologue, and each of these has a token budget that depends on your subscription tier. Small mistakes are easy to make and hard to see: an entry that never fires, a lorebook that crowds the story out of context, a character entry that gives away a twist before it happens.

Worldloom does that setup for open-ended, player-driven roleplay. It is built around a few rules:

- **The story is yours to steer.** The bible describes a world, a cast and possible directions. It does not script a plot.
- **Nothing past the start leaks in.** Entries the model always sees hold only what is true when the story opens. Possible twists and held-back facts go in an Operator Reference entry that never fires.
- **The genre is a contract.** A cozy premise does not come back with a villain; cast sizes are ceilings, and zero antagonists is valid.
- **Budgets are measured, not guessed.** A script counts every capped field against the tier's cap and reports the numbers.
- **The critic meets the bible cold.** Stage 2 runs in a fresh context and is given only the bible's path, so it reads the bible as another author's work. It may fix problems but may not change the cast list or the layout, and a script checks that it did not.

## How it works

| Stage | Subagent | Default model | Reads | Writes |
|---|---|---|---|---|
| 1 Story Bible | `worldloom-architect` | Opus | your input block | `input.txt`, `bible_v1.txt` |
| 2 Critique | `worldloom-critic` | Sonnet | `bible_v1.txt` | `critique.md`, `bible_v2.txt` |
| 3 Compile | `worldloom-compiler` | Sonnet | `bible_v2.txt` | `notes.md`, `scenario_content.json`, `<Title>.scenario`, `validation.txt` |

An orchestrator skill (`worldloom`) runs the three stages in order and passes only file paths between them, so no stage sees another stage's reasoning. Between stages it runs two scripts:

- `check_bible.py` after Stage 1 (structure) and after Stage 2 (same cast, same fields). A failure stops the run.
- `build_scenario.py --validate` inside Stage 3. The model writes only the story-specific content as JSON; the script adds the fixed sampler and context blocks, assembles the `.scenario`, and runs 16 checks on it. Stage 3 gets three attempts to pass.

A full Tablet run uses roughly 170k tokens across the three subagents and takes about eleven minutes.

## Requirements

- Claude Code (terminal, desktop app, or IDE extension), or Cowork, for the full pipeline with subagents. claude.ai chat works in a reduced form; see below.
- Python 3 for the build and check scripts (tested on 3.12). They use the standard library only and no network. Without Python the run still finishes, but the bible checks are skipped and the scenario is written by hand and not validated.
- A NovelAI subscription to use the result. The scenario targets GLM-4.6.

Only Windows has been tested. Nothing in the scripts is Windows-specific.

## Install

### Claude Code or the desktop app, from GitHub

Run these in an interactive `claude` terminal:

```bash
claude plugin marketplace add IIVICKII/WorldLoom
```

```bash
claude plugin install worldloom@worldloom-local
```

Open a new session. The skills appear as `/worldloom:worldloom`, `/worldloom:worldloom-bible`, `/worldloom:worldloom-critique` and `/worldloom:worldloom-compile`.

### From a local copy

Use this when you plan to change the plugin.

```bash
git clone https://github.com/IIVICKII/WorldLoom.git
```

```bash
claude plugin marketplace add "<path to the WorldLoom folder>"
```

```bash
claude plugin install worldloom@worldloom-local
```

### claude.ai chat

Chat takes skills, not plugins, and has no subagents.

1. Build the upload zips from a clone: `python tools/package.py`. They are written to `dist/`.
2. In claude.ai, open Settings → Capabilities and turn on code execution and file creation.
3. Under Skills, upload these four zips one at a time and enable them: `worldloom.zip`, `worldloom-bible.zip`, `worldloom-critique.zip`, `worldloom-compile.zip`. Do not upload `worldloom-plugin.zip` there.
4. In a new chat, write "Use the worldloom skill." followed by the input block.

The `worldloom` skill then runs the three stages one after another in the same chat. If the chat gets too long, run one stage per chat and carry the bible file across.

### Update

After the repository changes:

```bash
claude plugin marketplace update worldloom-local
```

```bash
claude plugin update worldloom@worldloom-local
```

Then open a new session. Installing copies the plugin into `~/.claude/plugins/cache/`, so a running session keeps the old copy.

### Uninstall

```bash
claude plugin uninstall worldloom@worldloom-local
```

```bash
claude plugin marketplace remove worldloom-local
```

## Use

```
/worldloom:worldloom
TIER: Tablet
START: the morning she arrives, before she has met anyone
POV: first person past
Story Premise: A travelling clockmaker arrives in a mountain village to repair the tower clock before the autumn fair.
Character Dynamics: The clockmaker is the one I play. She and the innkeeper start out wary of each other.
Character Backgrounds: The clockmaker left a city guild after a dispute. The innkeeper has run the inn alone for two years.
Genre Tags: cozy fantasy, slice-of-life, found family
```

- `TIER`, `START` and `POV` are optional. The tier defaults to Tablet; the Prologue defaults to third person limited past.
- Name the character you play in Character Dynamics ("… is the one I play").
- Add `--pause` to stop after the bible and read it, or `--skip-critique` to leave out Stage 2.

Everything is written to `./worldloom-output/<slug>/` under the folder you ran the command in. Import `<Title>.scenario` in NovelAI with Library → Import File.

Each stage can also be run alone, for example to recompile a bible for another tier or to build a `.lorebook` for a story already in progress. The full command list, the output files, the tier budgets, in-play advice and troubleshooting are in the [plugin guide](plugins/worldloom/README.md).

## Modify

### What is generated and what is not

The stage rules come from the files in `worldloom_source/`. A generator copies them into the plugin, so most of the plugin's instruction text must not be edited by hand.

| To change | Edit | Then |
|---|---|---|
| A stage's rules (what the bible contains, how the critic judges, how entries are written) | `worldloom_source/P1_…`, `P2_…` or `P3_…` | `python tools/build_skills.py` |
| The genre profiles | `worldloom_source/KB_GENRE_PROFILES.md` | `python tools/build_skills.py` |
| Text the plugin adds to a stage skill (file paths, the build command, chat fallback) | `tools/build_skills.py` | `python tools/build_skills.py` |
| The order of stages, the switches, the final report | `plugins/worldloom/skills/worldloom/SKILL.md` | nothing |
| A stage's model or tools | the `model:` or `tools:` line in `plugins/worldloom/agents/worldloom-*.md` | nothing |
| Samplers, context settings, tier caps, fixed Voice Guard and Prefill text | `plugins/worldloom/skills/worldloom-compile/assets/fixed_blocks.json` | update the tests if a reference value changed |
| The system prompt layout | `plugins/worldloom/skills/worldloom-compile/references/system-prompt-template.md` | as above |
| The shape of the content JSON Stage 3 writes | `references/content-schema.md` and `scripts/build_scenario.py` | as above |
| A validator check or warning | `scripts/validate_scenario.py` | add a case to `tests/test_scripts.py` |
| A bible check | `plugins/worldloom/skills/worldloom/scripts/check_bible.py` | add a case to `tests/test_bible.py` |

Generated files, never edited by hand: the three `worldloom-bible`, `worldloom-critique` and `worldloom-compile` `SKILL.md` files, `genre-profiles.md`, both `chat-mode.md` files and `manual-json.md`.

Two things to keep in mind:

- `SKILL.md` frontmatter may hold only `name` and `description`. Any other key is rejected on claude.ai upload. A description containing `: ` must be in double quotes.
- `fixed_blocks.json` and the system prompt template were derived from the P3 source text. If you change the fixed blocks in P3, change them in these files too; `tests/test_scripts.py` rebuilds the reference scenario and fails on any difference.

### The change loop

1. Make the edit, and run the generator if the table says so.
2. Run the tests. All three must print `ALL PASS`:

   ```bash
   python tests/test_scripts.py
   ```

   ```bash
   python tests/test_verbatim.py
   ```

   ```bash
   python tests/test_bible.py
   ```

   `test_scripts.py` checks the builder and validator against a known-good scenario and 33 deliberately broken ones. `test_verbatim.py` checks that every line of the source rules is still present in the plugin and that the manifests and frontmatter are valid. `test_bible.py` checks the bible checker.
3. Validate the manifests:

   ```bash
   claude plugin validate .
   ```

   ```bash
   claude plugin validate ./plugins/worldloom
   ```

4. Raise `version` in `plugins/worldloom/.claude-plugin/plugin.json`.
5. Rebuild the claude.ai zips if you use them: `python tools/package.py`.
6. Update the installed copy (see [Update](#update)) and open a new session. If the update does not pick the change up, uninstall and install again.

### Common changes

**Use a different model for a stage.** Change `model:` in the agent file to `opus`, `sonnet` or `haiku`. In testing, Haiku for Stage 3 cost more tokens and took longer than Sonnet.

**Change the samplers.** Edit `settings` in `fixed_blocks.json`. They are the same for every story.

**Change a tier budget.** Edit the tier's caps in `fixed_blocks.json` and the matching table in the P3 source, then regenerate. The validator reads the caps from the JSON.

**Add a validator warning.** Add it to `validate_scenario.py` as a warning, not an error: checks on creative content are heuristics and must never fail a file. Add one mutation to the `WARNINGS` list in `tests/test_scripts.py` that makes it fire, and confirm it does not fire on the reference scenario.

**Add a field to the bible format.** Add it to the P1 source, regenerate, and add its label to the `LABELS` list in `check_bible.py`, or the revision check will not compare it.

### Running the scripts by hand

```bash
python plugins/worldloom/skills/worldloom/scripts/check_bible.py bible_v2.txt --against bible_v1.txt
```

```bash
python plugins/worldloom/skills/worldloom-compile/scripts/build_scenario.py scenario_content.json --validate --tier Tablet
```

```bash
python plugins/worldloom/skills/worldloom-compile/scripts/validate_scenario.py "My Story.scenario" --tier Tablet
```

Each exits 0 on a pass and 1 on a failure.

## Repository layout

```
.claude-plugin/marketplace.json     marketplace manifest; points at plugins/worldloom
plugins/worldloom/
  .claude-plugin/plugin.json        plugin manifest and version
  README.md                         operator guide: commands, budgets, troubleshooting
  agents/                           three thin stage subagents (model and tools)
  skills/worldloom/                 orchestrator skill and check_bible.py
  skills/worldloom-bible/           Stage 1 rules (generated) and genre profiles
  skills/worldloom-critique/        Stage 2 rules (generated)
  skills/worldloom-compile/         Stage 3 rules (generated), builder, validator, fixed blocks
worldloom_source/                   the original stage instructions; source of truth
tools/build_skills.py               generates the stage skills from worldloom_source/
tools/package.py                    builds the upload zips in dist/
tests/                              three stdlib test scripts
docs/                               project notes: PROJECT.md, CODEMAP.md, DECISIONS.md
PLAN.md                             the phased build plan and its log
```

`worldloom-output/` (your stories) and `dist/` (build output) are not in the repository.

## Limits and known issues

- The lorebook tends to land close to the tier cap (about 2,190 of 2,200 on Tablet), above the 92% fit target. The validator warns; the cap itself is respected.
- Token counts are estimates: characters divided by four.
- The Prologue and leak warnings are heuristics. Read each one and fix those that point at a real fault.
- claude.ai chat and Cowork have not been tested end to end. Installing from GitHub, rather than from a local folder, has not been tested either.
- Stage 2 in claude.ai chat shares a context with Stage 1, so the critique is less independent there.

## Credits

The NovelAI scenario format, sampler settings and context settings that Worldloom writes draw on two community scenarios by **OccultSage**: *Sage's Simple Story Setup (GLM Edition)* and *Blackfeather Estate*. Those scenarios are not included in this repository and are not covered by its licence; they remain their author's work.

NovelAI and GLM-4.6 belong to their owners. Worldloom is an independent project and is not affiliated with Anthropic, NovelAI or OccultSage.

## Licence

[MIT](LICENSE). Copyright (c) 2026 IIVICKII. You may use, change and share this project, provided the copyright and licence notice stay with it.
