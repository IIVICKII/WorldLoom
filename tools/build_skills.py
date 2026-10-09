"""Generate the three stage skills from worldloom_source/ so the stage rules stay verbatim.

Run: python tools/build_skills.py
Every adaptation of the source text is in this file. tests/test_verbatim.py checks nothing was lost.
Re-run after any change to P1, P2, P3 or the genre profiles; never hand-edit the generated files.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "worldloom_source"
SKILLS = ROOT / "plugins/worldloom/skills"
BAR = "=" * 69


def load(name):
    return (SRC / name).read_text(encoding="utf-8").rstrip("\n").split("\n")


def at(lines, prefix):
    hits = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    assert len(hits) == 1, (prefix, hits)
    return hits[0]


def section(lines, title):
    """A '=====' banner section: from the bar above its title to the line before the next banner."""
    start = next(i for i, l in enumerate(lines) if l == BAR and lines[i + 1].startswith(title) and lines[i + 2] == BAR)
    end = next((i for i in range(start + 3, len(lines) - 2) if lines[i] == BAR and lines[i + 2] == BAR), len(lines))
    return lines[start:end]


def swap(lines, prefix, old, new):
    """Replace old with new inside the one line that starts with prefix."""
    i = at(lines, prefix)
    assert old in lines[i], (prefix, old)
    return lines[:i] + [lines[i].replace(old, new)] + lines[i + 1:]


def after(lines, prefix, extra):
    i = at(lines, prefix)
    return lines[:i + 1] + extra + lines[i + 1:]


def banner(title):
    return [BAR, title, BAR, ""]


def write(path, front, lines):
    path = SKILLS / path
    path.parent.mkdir(parents=True, exist_ok=True)
    head = ["---", "name: " + front[0], "description: " + json.dumps(front[1], ensure_ascii=False), "---", ""] if front else []
    path.write_text("\n".join(head + lines).rstrip("\n") + "\n", encoding="utf-8")


def text(block):
    return block.strip("\n").split("\n")


# ---------------------------------------------------------------- Stage 1
def bible():
    p1 = load("P1_STORY_BIBLE_ARCHITECT_INSTRUCTIONS.md")
    out_i = p1.index(BAR, at(p1, "- Cast Sizing Decisions:"))
    body = p1[:out_i]
    body = after(body, "- Premise, Dynamics, Backgrounds, or Genre Tags absent:", [
        '- Plugin note: a subagent cannot ask the user. When you run as one, reply with exactly one line, '
        '"NEEDS_INPUT: <the missing fields>", write no files, and stop.'])
    body = after(body, "Genre decides what the story is made of.", [
        "In this plugin the knowledge file KB_GENRE_PROFILES is references/genre-profiles.md in this skill's folder "
        "(the folder holding this SKILL.md). Read it in full before you start, on every run."])
    inside = at(p1, "Inside the block:")
    check = section(p1, "SELF-CHECK")
    check = swap(check, "- Code block;", "Code block;", "Plain-text file with no code fence;")
    check = swap(check, "- Plain-text file", "nothing outside except the permitted tier line", "nothing else in the file")
    body += banner("OUTPUT FORMAT") + text('''
Adapted for the plugin: the bible goes to a file, not a code block. If you have no way to write files, read references/chat-mode.md in this skill's folder and follow its OUTPUT FORMAT, CONTINUATION and COMMANDS instead.

Where the files go: the folder named in the task; otherwise ./worldloom-output/<slug>/, where <slug> is the Working Title in lowercase kebab-case. If that folder already holds a bible_v1.txt (try to read its first line), use <slug>-2, then <slug>-3.
- input.txt: the input block exactly as you received it.
- bible_v1.txt: the whole bible as plain text with no code fence. First line, exactly: "TIER: <tier>", then a blank line, then Section 1 through the last line of Section 7. Nothing else in the file.

Reply with the output folder path on the first line and the bible path on the second, and nothing else. If the user gave no tier, write "TIER: Tablet" in the file and add one reply line: "No tier given; using Tablet." Never paste the bible into the reply.
''') + ["", p1[inside].replace("Inside the block:", "Inside the file:"), ""] + text('''
Later requests on an existing bible file, each rewriting the complete file, never a diff:
- REVISE <instruction> — the complete bible with the change applied.
- TIER: <name> — regenerate against another tier's ceilings.
- GENRE: <tags> — regenerate with a different genre reading, re-running the Genre Contract first.
''') + [""] + check
    write("worldloom-bible/SKILL.md", ("worldloom-bible",
          "Worldloom Stage 1. Expands a story premise (Story Premise, Character Dynamics, Character Backgrounds, Genre Tags, "
          "optional TIER and START) into a seven-section Roleplay Story Bible for open-ended, player-driven roleplay and "
          "writes it to bible_v1.txt. Use when the user wants a story bible, world bible or roleplay setting built from a "
          "premise, or as the first stage of a Worldloom run."), body)
    write("worldloom-bible/references/genre-profiles.md", None, load("KB_GENRE_PROFILES.md"))
    write("worldloom-bible/references/chat-mode.md", None, text('''
# Stage 1 without file tools

Use this when you cannot write files. These are the original output rules; they replace the OUTPUT FORMAT section of SKILL.md. Every other rule in SKILL.md still applies.
''') + [""] + section(p1, "OUTPUT FORMAT") + section(p1, "CONTINUATION")
          + ["Self-check line that replaces the file line in SKILL.md:", p1[at(p1, "- Code block;")], ""]
          + section(p1, "COMMANDS"))


# ---------------------------------------------------------------- Stage 2
def critique():
    p2 = load("P2_EDITORIAL_CRITIQUE_INSTRUCTIONS.md")
    out_i = p2.index(BAR, at(p2, "3. Write the complete revised bible"))
    body = p2[:out_i]
    body = after(body, 'The bible\'s first line is "TIER:', [
        "", "Plugin notes: when the task gives a file path, read the bible from that file; it carries no code fence. "
        'A subagent cannot ask the user, so when you run as one and the document is not a complete seven-section bible, '
        'reply with exactly one line, "REJECTED: <reason>", write no files, and stop.'])
    out = section(p2, "OUTPUT FORMAT")
    headers = out[at(out, "Genre Fit Corrections"):at(out, "One \"-\" bullet per change") + 1]
    check = section(p2, "SELF-CHECK")
    check = swap(check, "- Structure intact;", "code block with the TIER line first", "plain-text file with the TIER line first and no code fence")
    body += banner("OUTPUT FORMAT") + text('''
Adapted for the plugin: the critique and the revised bible go to two files, not to the chat. If you have no way to write files, read references/chat-mode.md in this skill's folder and follow its OUTPUT FORMAT, CONTINUATION and COMMANDS instead.

Both files go in the folder of the bible you were given (a pasted bible: ./worldloom-output/<slug>/, where <slug> is its Working Title in lowercase kebab-case).

First the critique, written to critique.md in plain text under these four headers, in order:
''') + [""] + headers + [""] + text('''
Then the complete revised bible, written to bible_v2.txt as plain text with no code fence. Its first line is the tier, exactly "TIER: <tier>", then a blank line, then "1. Working Title, Tags & Logline" through the end of Section 7. Nothing after it.
''') + ["", out[at(out, "Inside the block:")].replace("Inside the block:", "Inside the file:"), ""] + text('''
Reply "OK" on the first line, then the critique path and the revised bible path, one per line, and nothing else. Never paste the critique or the bible into the reply.

Variants:
- CRITIQUE ONLY (or --critique-only) — write critique.md with the four-header critique and no revised bible.
- RE-RUN — a second pass over a revision (bible_v2.txt). Write critique_rerun.md and bible_v3.txt. It should find markedly less; if the bible is sound, write "None found." under all four headers and write the bible out verbatim.
''') + [""] + check
    write("worldloom-critique/SKILL.md", ("worldloom-critique",
          "Worldloom Stage 2. Editorial critique of a complete seven-section Roleplay Story Bible: fixes genre-fit errors, "
          "inconsistencies, plot holes and flat spots without changing the cast list or the map, then writes critique.md "
          "and the revised bible_v2.txt. Use when the user wants a story bible critiqued, checked or revised, or as the "
          "second stage of a Worldloom run."), body)
    write("worldloom-critique/references/chat-mode.md", None, text('''
# Stage 2 without file tools

Use this when you cannot write files. These are the original output rules; they replace the OUTPUT FORMAT section of SKILL.md. Every other rule in SKILL.md still applies.
''') + [""] + out + section(p2, "CONTINUATION")
          + ["Self-check line that replaces the file line in SKILL.md:", p2[at(p2, "- Structure intact;")], ""]
          + section(p2, "COMMANDS"))


# ---------------------------------------------------------------- Stage 3
def compile_skill():
    p3 = load("P3_NOVELAI_CONFIG_COMPILER_INSTRUCTIONS.md")
    out_i = at(p3, "OUTPUT — two parts") - 1
    json_i = at(p3, "THE SCENARIO JSON") - 1
    memory_i = at(p3, "MEMORY — one ATTG line") - 1
    tpl_a, tpl_b = at(p3, "You are a GLM-4.6-based LLM"), at(p3, "Stay in the story.")
    fit_end = at(p3, "CONTINUATION") - 1
    notes = p3[at(p3, "1. NOTES"):at(p3, '- "Estimated: Author\'s Note') + 1]
    once = p3[at(p3, "The Prologue, Author's Note, System Prompt, Prefill, lorebook, and phrase bias appear only")]

    body = swap(p3[:out_i], "The bible arrives as pasted text", "The bible arrives as pasted text",
                "The bible arrives as a file path in the task (read the file) or as pasted text")
    body = after(body, "- Not a complete seven-section bible:", [
        '- Plugin note: a subagent cannot ask the operator. When you run as one and the bible is incomplete, reply '
        'with exactly one line, "REJECTED: <reason>", write no files, and stop.'])
    body += banner("OUTPUT — files, nothing else") + text('''
Adapted for the plugin: a script assembles the .scenario from the fixed blocks, so you write only the story-specific content, and a validator checks the result. If you cannot run Python here, read references/manual-json.md in this skill's folder and follow it instead; it holds the original hand-written JSON procedure.

All output files go in the bible's folder (a pasted bible: ./worldloom-output/<slug>/, where <slug> is the title in lowercase kebab-case). Paths under references/ and scripts/ are relative to this skill's folder, the one holding this SKILL.md.

Before writing anything, read references/system-prompt-template.md and references/content-schema.md in full, on every compile.

Order of work: plan the lorebook budget (below), write scenario_content.json (item 2), build and validate it (item 3), and write notes.md last (item 4). Item 1 says what notes.md holds.

Plugin note, the lorebook budget plan. Do this before writing any entry, so the first build lands near the target instead of far over it:
- The target is the tier's lorebook fit target from the table above, not LB_CAP. LB_CAP is the limit the validator fails on; the fit target is what you write to.
- Reserve the always-on entries first: Core Memory at the middle of CM_RANGE, Voice Guard about 220, Characters about 150 to 200, Story So Far about 320, Glossary about 25 for each line. These are typical sizes, not rules; the INFO lines of the first report give the real ones.
- Divide what is left among the Tier 1 and Tier 2 entries. Main Cast entries get the largest shares, Tier 2 entries the smallest. That share is each entry's allowance.
- Write each entry to its allowance: one token is about four characters, so an allowance of 300 tokens is about 1,200 characters of entry text. When the allowances are too small for full entries, apply "Lorebook budget, in strict order" below while you write, not after the build.
''') + ["", notes[0].replace("1. NOTES", "1. notes.md")] + notes[1:] + text('''
- "Import <Title>.scenario in NovelAI. It creates a new story."

2. scenario_content.json — the story-specific content, in the shape references/content-schema.md gives. Valid JSON: every line break inside a string written as \\n, every " as \\", every \\ as \\\\. No trailing commas, comments, or single quotes.
''') + ["", once, ""] + text('''
3. Build and validate, in one command: python "<skill folder>/scripts/build_scenario.py" "<output folder>/scenario_content.json" --validate --tier <tier>
It writes "<Title>.scenario" and validation.txt beside the content file, prints the scenario path, then prints the validator's report. If the task names a Python interpreter ("Python: <path>"), use that path in place of "python". Otherwise, if "python" is not found or will not run, try "python3", then "py".
Exit 0 is a pass. On exit 1, read the FAIL lines of the report, fix scenario_content.json, then build and validate again. Fix the content only: never edit the built file, the scripts, or the fixed blocks, and never break a rule in this document to satisfy a check. At most three build-and-validate attempts; after the third failure, stop. Count the attempts as you go: the third run of this command is the last. Read the WARN lines on a pass and fix any that point at a real fault; a run made to fix warnings counts as an attempt, and a pass with warnings left is still a pass.
A budget line in the report ends with the cut it needs, "cut about N tokens (~M characters) to reach the fit target", and for the lorebook names the largest trimmable entries. Make that whole cut in one pass, down to the fit target: never trim only as far as the cap, and never in small steps over several builds. Take it from those entries by "Lorebook budget, in strict order" below, and never take Core Memory below CM_RANGE.
Write scenario_content.json in the output folder from the start. To change it after a build, edit only the strings that change when you have an edit tool; write the whole file again only when you have none.

4. Now write notes.md, as item 1 describes. Copy the three numbers of its Estimated line, and the tokens of each entry in the lorebook plan, from the INFO lines of the last report; never estimate them by hand.

5. Reply with the scenario path, the RESULT line of validation.txt, and, after three failures, the remaining FAIL lines under the words "FAILED after 3 attempts". Nothing else: never paste the notes, the content, or the scenario into the reply.

''') + [""] + banner("THE SCENARIO CONTENT") + text('''
The builder supplies everything that is the same for every story: the top-level skeleton and key order, the sampler settings, the default lorebook entry, entry ids, each entry's activation, priority, trim and search settings (from the role you give it), the fixed comma bias group, the fixed Voice Guard text, the System Prompt template text, and the fixed Prefill lines. You never write those. You write every field below, to the rules below, into scenario_content.json.

Never reword an entry name between compiles of the same story.
''') + [""] + p3[memory_i:tpl_a] + text('''
The template is references/system-prompt-template.md. The builder fills its marked places from the "systemPrompt" object in the content file: the romance block, the LitRPG line, the scenario bans, the event system, and the examples block. When budget fit needs tighter template wording, write the complete prompt as "systemPromptOverride" instead, keeping every header and every protected block.
''') + p3[tpl_b + 1:fit_end]
    body = after(body, "[Story continues:]", [
        "", 'Plugin note: the builder writes these lines. You supply only the three continuation lines, as '
        '"prefillContinuation", or leave it out to keep the three above.'])
    body = after(body, "Distinct: No two characters share a register.", [
        "", 'Plugin note: the builder writes this entry, second in the lorebook. You supply only the extension to the '
        'Forbidden line, as "voiceGuardExtra"; never list a Voice Guard entry yourself. It still counts toward LB_CAP.'])
    check = section(p3, "SELF-CHECK")
    check = swap(check, "- NOTES, then one code block", "NOTES, then one code block (or one file line), nothing after",
                 "notes.md, scenario_content.json, the built file, and validation.txt, nothing else")
    body += check + banner("VARIANTS") + text('''
Each works on an existing output folder. After any change to scenario_content.json, build and validate again.
- LOREBOOK (or --lorebook) — add --lorebook to the build-and-validate command. The builder writes "<Title>.lorebook", holding only the lorebook, to import into a story already in progress.
- PROLOGUE — reply with the current "prologue" as plain readable text, nothing else.
- TRIM — re-run the budget fit, then rewrite notes.md and scenario_content.json.
- RECOUNT — run the build-and-validate command again and reply with only the Estimated line, taken from its INFO lines.
- POV: <person and tense> — rewrite the Prologue only.
- TIER: <name> — recompile everything against that tier.
- In-play events from the operator (notes, a recap) go only into Story So Far, by the past-events rule above.
''')
    write("worldloom-compile/SKILL.md", ("worldloom-compile",
          "Worldloom Stage 3. Compiles a seven-section Roleplay Story Bible into a validated NovelAI (GLM-4.6) .scenario "
          "file: Memory, Author's Note, System Prompt, Prefill, Lorebook, Phrase Bias and Prologue, with nothing past the "
          "story's start. Also re-compiles for another TIER or POV and builds a .lorebook only. Use when the user wants a "
          "story bible turned into a NovelAI scenario or lorebook, or as the third stage of a Worldloom run."), body)
    write("worldloom-compile/references/manual-json.md", None, text('''
# Stage 3 without the builder script

Use this when you cannot run Python. These are the original rules for writing the whole scenario JSON by hand; they replace the OUTPUT and THE SCENARIO CONTENT sections of SKILL.md. Every content rule in SKILL.md still applies. The System Prompt template is references/system-prompt-template.md: fill its bracketed places yourself and remove the bracket lines. Write the Voice Guard entry and the Prefill out in full.

Original input line:
''') + [p3[at(p3, "The bible arrives as pasted text")], ""] + p3[out_i:json_i] + p3[json_i:memory_i]
          + section(p3, "CONTINUATION")
          + ["Self-check line that replaces the file line in SKILL.md:", p3[at(p3, "- NOTES, then one code block")], ""]
          + section(p3, "COMMANDS"))


if __name__ == "__main__":
    bible()
    critique()
    compile_skill()
    for f in sorted(SKILLS.rglob("*.md")):
        print("%6d chars  %s" % (len(f.read_text(encoding="utf-8")), f.relative_to(ROOT).as_posix()))
