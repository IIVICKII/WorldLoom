# Worldloom

Turns a story premise into a validated NovelAI (GLM-4.6) `.scenario` file in one run.

```
premise ──► Stage 1 Story Bible ──► Stage 2 Critique ──► Stage 3 Compile ──► <Title>.scenario
            bible_v1.txt            critique.md           notes.md
                                    bible_v2.txt          validation.txt
```

## Run it

```
/worldloom:worldloom
TIER: Tablet
START: the morning she arrives, before she has met anyone      (optional)
POV: first person past                                         (optional)
Story Premise: ...
Character Dynamics: ...
Character Backgrounds: ...
Genre Tags: cozy fantasy, slow-burn romance
```

Everything lands in `./worldloom-output/<slug>/`:

| File | What it is |
|---|---|
| `input.txt` | Your input block, as given |
| `bible_v1.txt` | Stage 1 Story Bible |
| `critique.md` | Stage 2 critique under four headers |
| `bible_v2.txt` | Stage 2 revised bible |
| `notes.md` | Stage 3 notes: tier, title and alternatives, POV, lorebook plan, token estimates |
| `scenario_content.json` | The story-specific content Stage 3 wrote |
| `<Title>.scenario` | The file to import: NovelAI → Library → Import File |
| `validation.txt` | The validator's report |

To name the character you play, say so in Character Dynamics ("Mira is the one I play"). Without a `POV:` line the Prologue is third person limited past.

## Commands

| Command | Effect |
|---|---|
| `/worldloom:worldloom <input block>` | Full run |
| `... --pause` | Stop after the bible so you can read it. Say "continue" to go on. |
| `... --skip-critique` | Compile `bible_v1.txt` directly |
| `/worldloom:worldloom-bible <input block>` | Bible only. Later: `REVISE <change>`, `TIER: <name>`, `GENRE: <tags>` |
| `/worldloom:worldloom-critique <bible path>` | Critique and revised bible. `--critique-only` for the critique alone; `RE-RUN` for a second pass |
| `/worldloom:worldloom-compile <bible path>` | Compile only |
| `/worldloom:worldloom-compile <bible path> TIER: Scroll` | Recompile for another tier |
| `/worldloom:worldloom-compile <bible path> POV: second person present` | Rewrite the Prologue in another point of view |
| `/worldloom:worldloom-compile <bible path> --lorebook` | `<Title>.lorebook` only, to import into a story already in progress |
| `PROLOGUE`, `TRIM`, `RECOUNT` after a compile | Show the Prologue / re-fit budgets / re-estimate tokens |

## Models

Every stage runs on the model and effort level of the session you start the run from. Pick the model before you run the command.

| Stage | Agent file | `model:` |
|---|---|---|
| 1 Story Bible | `agents/worldloom-architect.md` | `inherit` |
| 2 Critique | `agents/worldloom-critic.md` | `inherit` |
| 3 Compile | `agents/worldloom-compiler.md` | `inherit` |

What that means for cost and quality: from an Opus session all three stages run on Opus, which costs clearly more than a Sonnet session. From a Haiku session the bible, the creative part, is written by the smallest model; in testing Haiku also used more tokens than Sonnet on Stage 3.

To pin one stage to a model whatever the session uses, change its `model:` line to `opus`, `sonnet` or `haiku`, raise `version` in `.claude-plugin/plugin.json`, then run `claude plugin update worldloom@worldloom-local` and start a new session. If the update does not pick the change up, reinstall: `claude plugin uninstall worldloom@worldloom-local`, then `claude plugin install worldloom@worldloom-local`. Installing copies the plugin into `~/.claude/plugins/cache/`, so an edit to the source folder does nothing until you update or reinstall.

## Where it works

| Surface | Behaviour |
|---|---|
| Claude Code, Cowork | Full pipeline. Each stage runs as its own subagent in a fresh context; the scripts build and validate the file. |
| claude.ai chat (plugin or skills uploaded) | Subagents are not available, so the `worldloom` skill runs the three stages one after another in the same chat. With code execution the scripts still run; without it Stage 3 writes the JSON by hand (`references/manual-json.md`). |
| Free plan | Upload the stage skills one at a time (`worldloom-bible`, `worldloom-critique`, `worldloom-compile`) and run each in its own chat, pasting the bible across. Each falls back to its original code-block output and `CONTINUE`. |

The scripts need Python 3 and nothing else. They use no network. The full run looks for an interpreter once (`python`, `python3`, `py -3`, then a per-user Windows install under `%LOCALAPPDATA%\Programs\Python`) and hands it to Stage 3. With none found, the bible checks are skipped, Stage 3 writes the JSON by hand, and the final report says the scenario was not validated.

## The validator

`skills/worldloom-compile/scripts/validate_scenario.py FILE [--tier Tablet|Scroll|Opus] [--lorebook] [--report validation.txt]`

Stage 3 builds and validates in one step: `skills/worldloom-compile/scripts/build_scenario.py scenario_content.json --validate --tier <tier>` writes the `.scenario` and `validation.txt`, prints the report, and exits 0 on a pass.

It runs 16 checks: JSON and key order, the fixed sampler and context blocks, lorebook container, entries against the default entry, ids, entry order, per-role settings, entry text rules, Story So Far shape, the ATTG line, the Author's Note style line, no blank Prologue lines, System Prompt headers and fixed lines, phrase bias, banned names, and tier budgets. Exit 0 is a pass. Stage 3 gets three attempts; a file that still fails is kept and reported as failed.

The report also carries `INFO` lines with the measured budgets (Author's Note, System Prompt, lorebook, and each entry, against the cap and the 92% fit target) and `WARN` lines. Warnings never fail a file. They cover: a field over its fit target; Core Memory outside its range; the Prologue's last spoken line belonging to the player character, ending on a question, an appositive after "said", or a "not X but Y" construction; premise-leak words in any entry except Story So Far and the Operator Reference, and in Memory, the Author's Note and the Prologue; a bias word that is already banned; an ATTG genre missing from the tags; a tag that is not lowercase; a cast name in the Author's Note; key counts and duplicate keys. The Prologue and leak checks are heuristics: read each warning and fix the ones that point at a real fault.

## The bible checks

`skills/worldloom/scripts/check_bible.py BIBLE [--against ORIGINAL]`

The full run checks the bible after Stage 1 and the revision after Stage 2, and stops if either fails. Alone, the script checks structure: the `TIER:` line, the seven section headings in order, one `Player Character:` line, no code fence, no banned name. With `--against`, it also checks that the revision kept the same named characters, factions and locations, the same Narrative Weight and Role for each, the same Player Character, and the same labelled fields in the same order. It prints names and labels only. The single-stage skills do not run it, so they still accept older bibles.

## Tier budgets

| | Tablet | Scroll | Opus |
|---|---|---|---|
| NovelAI context | 8,192 | 12,288 | 28,672 |
| Author's Note | 300 | 450 | 900 |
| System Prompt | 2,000 | 2,800 | 4,000 |
| Lorebook (all entries) | 2,200 | 3,300 | 7,000 |
| Core Memory entry | 250–350 | 400–500 | 800–1,000 |
| Main cast sized around | 2 | 3 | 4 |
| Supporting ceiling | 3–4 | 4–5 | 5–6 |
| Antagonist ceiling | 1–2 | 1–2 | 2–3 |

Cast numbers are ceilings only. Zero supporting characters and zero antagonists are valid.

## In play

- **Story So Far** is always on and never trimmed, so keep it short. Add past events to `Earlier:` as plain bullet facts with their consequence; add coming events to `Upcoming (not happened yet):` and move each to Earlier once it happens; squash old lines into one. Every past event goes here and nowhere else. Edit a character's entry only to change a standing fact such as a relationship.
- **Operator Reference** never fires. It holds possible directions, escalation beats, open questions and anything held back. Never give it a keyword.
- **Recompiling mid-story:** importing a scenario always makes a new story. To refresh an ongoing one, build a `.lorebook` with `--lorebook` and import it into that story's lorebook; copy other fields by hand.
- **Phrase Bias** starts with a group biasing "," at −1.75, on purpose: it starves GLM's comma-hung appositive habit. Untick it in NovelAI if prose feels clipped.
- **Samplers** are the same for every story. To change them, edit `settings` in `skills/worldloom-compile/assets/fixed_blocks.json`.

## Troubleshooting

| Symptom | Fix |
|---|---|
| NovelAI won't import the file | Make sure it ends in `.scenario`, not `.scenario.txt`. Check `validation.txt`. |
| Validation failed after three attempts | Read the `FAIL` lines in `validation.txt`, then run `/worldloom:worldloom-compile <bible path>` again. |
| `python` not found, or it opens the Microsoft Store | Install Python 3 and open a new terminal. |
| Characters drift into clinical or analytical talk mid-session | Edit the first drifted line out of the story text; the model copies recent text. Check the Voice Guard entry is Always On. |
| A character mentions something that hasn't happened | Delete the line from that lorebook entry in NovelAI. |
| A gentle story came back with a villain | Re-run Stage 1 with `GENRE: <your tags>`. |
| The Operator Reference is firing | Clear its keys and disable it. |
