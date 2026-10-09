---
name: worldloom
description: Runs the whole Worldloom pipeline in one go. Takes a story premise (Story Premise, Character Dynamics, Character Backgrounds, Genre Tags, optional TIER, START and POV) and produces a Story Bible, an editorial critique, a revised bible, and a validated NovelAI (GLM-4.6) .scenario file in ./worldloom-output/<slug>/. Switches --pause (stop after the bible) and --skip-critique. Use when the user wants a NovelAI scenario built from a premise, or says "worldloom".
---

# Worldloom orchestrator

You run three stages in order and pass file paths between them. You never write a bible, a critique or a scenario yourself here, and you never read a bible into this conversation: each stage reads and writes files.

| Stage | Subagent | Skill it follows | Writes |
|---|---|---|---|
| 1 Story Bible | `worldloom:worldloom-architect` | `worldloom-bible` | `input.txt`, `bible_v1.txt` |
| 2 Critique | `worldloom:worldloom-critic` | `worldloom-critique` | `critique.md`, `bible_v2.txt` |
| 3 Compile | `worldloom:worldloom-compiler` | `worldloom-compile` | `notes.md`, `scenario_content.json`, `<Title>.scenario`, `validation.txt` |

## 1. Read the request

The input block:

    TIER: Tablet | Scroll | Opus      (optional; Tablet when absent)
    START: ...                        (optional)
    POV: ...                          (optional; for the Prologue)
    Story Premise: ...
    Character Dynamics: ...
    Character Backgrounds: ...
    Genre Tags: ...

- Story Premise, Character Dynamics, Character Backgrounds or Genre Tags absent: ask for the missing fields in one short message and stop. Ask nothing else.
- Take the `POV:` line out of the block. Stage 1 never sees it; Stage 3 gets it.
- Switches, anywhere in the request: `--pause` stops after Stage 1; `--skip-critique` leaves out Stage 2.
- Pass the rest of the block to Stage 1 exactly as written. Never summarise, correct or extend it.

## 2. Run the stages

Spawn one subagent per stage, one at a time, each in a fresh context. Give each only what is listed. Use absolute paths.

1. Stage 1, `worldloom:worldloom-architect`. Task message: the input block, the output root `<current working directory>/worldloom-output`, and, when that folder already has subfolders, one line `Folders in use: <names, comma separated>` (list them with one `ls`; leave the line out when there are none). Stage 1 must not write into a listed folder; a second run of the same title goes to `<slug>-2`. It replies with the output folder and the bible path.
   - Reply starts `NEEDS_INPUT:`: show the user that line and stop.
   - Otherwise check the bible (see "Checking a bible" below): `check_bible.py "<bible_v1.txt>"`. Exit 1: show the user its FAIL lines and stop.
   - `--pause`: print the bible path, say "continue" resumes the run, and stop. On "continue", go on from Stage 2 with that path.
2. Stage 2, `worldloom:worldloom-critic`, unless `--skip-critique`. Task message: the path of `bible_v1.txt`, nothing else. No premise, no notes from Stage 1, no opinion of yours: the critic must meet the bible cold.
   - Reply starts `REJECTED:`: show the user that line and stop.
   - Otherwise check the revision: `check_bible.py "<bible_v2.txt>" --against "<bible_v1.txt>"`. Exit 1 means the critic changed the cast list or the field layout, which Stage 2 forbids. Give the critic one repair: spawn `worldloom:worldloom-critic` again with a task message of exactly four parts, the line `REPAIR`, the path of `bible_v2.txt`, the path of `bible_v1.txt`, and the FAIL lines as printed. Then run the same check again. Exit 0: go on to Stage 3 and say in the final report that the revision needed one repair. Exit 1 a second time: show the user the FAIL lines and stop. Say the two ways on: run `worldloom-critique` on `bible_v1.txt` again, or compile `bible_v1.txt` as it is with `worldloom-compile`.
3. Stage 3, `worldloom:worldloom-compiler`. Task message: the path of `bible_v2.txt` (`bible_v1.txt` with `--skip-critique`), the `POV:` line when the user gave one, and the line `Python: <interpreter>` when you found one (the full path, or the command that worked).

A stage that fails or returns something other than the replies above: report what it returned and stop. Apart from the one Stage 2 repair above, never re-run a stage, and never repair a stage's output yourself.

### Checking a bible

`scripts/check_bible.py`, in this skill's folder, checks a bible file without you reading it. It prints only PASS, FAIL and WARN lines with names, labels and counts, never the bible's prose.

    python "<this skill's folder>/scripts/check_bible.py" "<bible path>" [--against "<original bible path>"]

- Alone, it checks structure: the `TIER:` line, the seven section headings in order, one `Player Character:` line, no code fence, no banned name.
- With `--against`, it also checks that the revision has the same named characters, factions and locations, the same Narrative Weight and Role for each, the same Player Character, and the same labelled fields in the same order.
- A `WARN` line (Main Cast larger than the tier's budget assumes) is not a failure and never stops the run. Keep the line for the final report.
- Exit 0 is a pass. Run it with the interpreter from "Finding Python" below. With no interpreter, skip both checks and say in the final report that the bibles were not checked.
- A FAIL is never yours to repair: do not open or edit the bible.

### Finding Python

Find a Python 3 interpreter once, before Stage 1, and use that same one for the whole run:

1. Try `python`, then `python3`, then `py -3`, and stop at the first whose `--version` prints `Python 3.`. Run the search as one command that hides what the failed ones print; it prints the interpreter to use, or nothing:
   - bash: `for p in python python3 "py -3"; do $p --version 2>/dev/null | grep -q "^Python 3\." && { echo "$p"; break; }; done`
   - PowerShell: `foreach ($p in 'python','python3','py -3') { $c = $p -split ' '; if ((& $c[0] $c[1..9] --version 2>$null) -match '^Python 3\.') { $p; break } }`

   A command that prints nothing, fails, or opens the Microsoft Store is a stub, not Python.
2. On Windows, when none of those work, look for a per-user install: `ls "$LOCALAPPDATA"/Programs/Python/Python3*/python.exe` in bash, or `Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe"` in PowerShell. Use the full path of the newest one, and confirm it with `--version`.
3. Nothing found: carry on without one. The bible checks are skipped, Stage 3 gets no `Python:` line and will fall back to its hand-written procedure, and the final report must say that the scenario was not validated by the script.

Never install Python or change PATH yourself.

## 3. Report

End with a short report:

- the output folder and the path of the `.scenario` file;
- the validation result from Stage 3 (`RESULT:` line and the number of warnings; on failure the remaining `FAIL` lines, and say plainly that the file did not pass);
- when Stage 3 failed, was not validated, or did not finish: the command that runs it again on its own, `/worldloom:worldloom-compile <bible path>`, with the real path filled in;
- the files written;
- the bible checks: passed, or not run and why; and any `WARN` line they printed, word for word, followed by the command that compiles the same bible for a larger tier, `/worldloom:worldloom-compile <bible path> TIER: <larger tier>`;
- token use per stage, when the subagent results report it; otherwise say it was not reported;
- one line: import the `.scenario` in NovelAI with Library → Import File.

## Single stages

Each stage is also a skill of its own:

- `worldloom-bible <input block>` — bible only.
- `worldloom-critique <bible path>` — critique and revised bible; `--critique-only` for the critique alone.
- `worldloom-compile <bible path>` — compile only; add `TIER: <name>` or `POV: <person and tense>` to re-compile, `--lorebook` for a `.lorebook` only.

## Without subagents

When you have no tool to spawn subagents (claude.ai chat, or the stage agents are not installed), run the three stages yourself, in order, in this conversation:

1. Load the `worldloom-bible` skill and follow it in full. Write the files it names.
2. Before Stage 2, put Stage 1 out of mind: load the `worldloom-critique` skill, re-read the bible from its file, and treat it as another author's work that you are seeing for the first time. Follow the skill in full.
3. Load the `worldloom-compile` skill, re-read the revised bible from its file, and follow the skill in full, including the build and validate steps when you can run Python.

When you can run Python, run the two bible checks above as well: after step 1, and after step 2 with `--against`. Here a FAIL is your own stage's fault, so correct the file under that stage's rules and check again, once.

Find the stage skills as installed skills, or beside this one at `../worldloom-bible/SKILL.md`, `../worldloom-critique/SKILL.md` and `../worldloom-compile/SKILL.md`. Each stage skill says what to do when you cannot write files or run scripts. Never shorten a stage because you are running all three.
