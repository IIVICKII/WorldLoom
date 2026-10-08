# Worldloom — Operations Guide

Three Claude Projects turn a story idea into a NovelAI (GLM-4.6) configuration that imports in one
paste. This guide is for you; it is not uploaded to any project.

```
Your idea ──► P1 Story Bible ──► P2 Critique (optional) ──► P3 Config ──► NovelAI (Import File)
             (code block)        (code block)               (.scenario)
```

---

## 1. Files and where they go

| File | Where |
|---|---|
| `P1_STORY_BIBLE_ARCHITECT_INSTRUCTIONS.md` | Project 1 → project instructions |
| `KB_GENRE_PROFILES.md` | Project 1 → project knowledge |
| `P2_EDITORIAL_CRITIQUE_INSTRUCTIONS.md` | Project 2 → project instructions |
| `P3_NOVELAI_CONFIG_COMPILER_INSTRUCTIONS.md` | Project 3 → project instructions |
| `SAMPLE_TEST_BIBLE_FOR_P3.md` | Not uploaded. Paste into a fresh Project 3 chat to test. |
| `The_Quiet_Ledger.scenario` | Not uploaded. A finished scenario built from the sample bible; import it into NovelAI to confirm the format works. |
| `WORLDLOOM_MODULAR_ARCHITECTURE.md` | Not uploaded. This guide. |

Projects 2 and 3 have no knowledge files: everything they need is in their instructions or in the
bible itself.

Approximate tokens loaded into every chat: Project 1 ≈ 9.1k (instructions 5.8k + genre profiles 3.3k), Project 2 ≈ 3.1k, Project 3 ≈ 12k.

---

## 2. Setting up

For each project: claude.ai/projects → **+ New Project** → name it → **Set project instructions** →
paste the whole instructions file → save. For Project 1, also add `KB_GENRE_PROFILES.md` with the
**+** button in the project knowledge panel. One chat per story in each project.

Project 3's output is a native NovelAI scenario file; NovelAI imports it directly.

---

## 3. Running a story

**Project 1 — Story Bible.** Start a chat with:

```
TIER: Tablet
START: the morning she arrives, before she has met anyone      (optional)
Story Premise: ...
Character Dynamics: ...
Character Backgrounds: ...
Genre Tags: cozy fantasy, slow-burn romance
```

The bible comes back in one code block whose first line is `TIER: ...`. Copy the block. Every field
is a labelled line Project 3 lifts into the config: the **Player Character** line, each character's
Gender, Occupation, Wants, Fears, Relationships at start, and Sample line (which becomes their Quote),
and in Section 5 the **Recent Events & Temporary Conditions** and **Known Upcoming** lists that seed
Story So Far. To name the character you play, say so in Character Dynamics ("Mira is the one I play").

**Project 2 — Critique (optional).** Paste the block. You get a short critique under four headers,
then the revised bible in one code block, again starting with `TIER: ...`. Copy that block. Skip
Project 2 entirely if the bible already reads right.

**Project 3 — Config.** Paste the block. To fix the Prologue's point of view, add a line such as
`POV: first person past` under the TIER line; without one, it is third person limited past. The response has two parts:

| Part | What you do with it |
|---|---|
| `NOTES` | Read: tier, chosen title and alternatives, POV, lorebook plan, token estimates. |
| Code block | Copy it into a text file and save it as `<Title>.scenario` (if the chat made a downloadable file instead, just download it). In NovelAI: Library → Import File → choose it. |

The import creates a new story with everything set: Memory (an ATTG line), Author's Note, System Prompt,
Prefill, lorebook, Phrase Bias, GLM sampler settings, and the Prologue as the opening
text. Delete nothing; just start playing.

---

## 4. Commands

| Project | Command | Effect |
|---|---|---|
| 1 | `CONTINUE` | Resume a cut-off bible in a new code block; join the two blocks. |
| 1 | `REVISE <change>` | Re-emit the whole bible with the change. |
| 1 | `TIER: <name>` / `GENRE: <tags>` | Regenerate against another tier or genre reading. |
| 2 | `CONTINUE` | Resume a cut-off response. |
| 2 | `CRITIQUE ONLY` | Critique without the revised bible. |
| 2 | `RE-RUN` | Second pass over a revision you paste back. |
| 3 | `CONTINUE` | Resume a cut-off response. |
| 3 | `SYNC SCENARIO` | Re-emit the complete scenario JSON. Use when a response was cut inside the JSON. |
| 3 | `LOREBOOK` | Emit only the lorebook, to save as `<Title>.lorebook` and import into a story already in progress. |
| 3 | `PROLOGUE` | Show the Prologue as readable text. |
| 3 | `TRIM` / `RECOUNT` | Re-fit budgets / re-estimate tokens. |
| 3 | `POV: <person and tense>` | Rewrite the Prologue and re-emit the scenario. |
| 3 | `TIER: <name>` | Recompile for another tier. |

---

## 5. Tier budgets

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

---

## 6. What the pipeline protects

- **Genre Contract.** Project 1 settles genre first: stakes, opposition (the antagonist floor may be
  zero), flaw weight, tempo, darkness, and the "engine" that makes scenes work. A rival is never a
  villain; setting tags (fantasy, academy) never imply a dark lord. Projects 2 and 3 work to it.
- **Cast necessity.** Supporting characters and antagonists exist only when the story needs them.
  Characters you name always stay.
- **Starting point.** Play starts at a fixed moment (T0). Events and later personalities from the
  premise are relocated into pressures, directions, and open questions, never deleted, and never
  leak into anything the model can retrieve as fact.
- **Voices.** Every speaking character has a default register, a habit with a frequency, and a
  "never" clause. Clinical or analytical speech is banned three ways: the System Prompt's banned
  words, an always-on **Voice Guard** lorebook entry, and a line in the Prefill.
- **Operator Reference.** A lorebook entry that never fires, holding possible directions,
  escalation beats, open questions, and anything held back. Never give it a keyword.

---

## 7. Scenario details

- **Memory** holds one ATTG line: `[ Author: ...; Title: ...; Tags: ...; Genre: ... ]`. GLM reads it as
  a style signal; the author names steer the prose strongly.
- **Author's Note** opens with `[ Write in a style that conveys the following: ... ]`, then the
  narration guidance.
- **System Prompt and Prefill** merge the OccultSage GLM rules (no appositives, no "not X but Y", no
  named emotions, flow over choppiness) with Worldloom's voice discipline, banned words, and event system.
- **Phrase Bias** always starts with a one-entry group biasing "," at −1.75. It is deliberate, from
  the Sage setup: it starves GLM's comma-hung appositive habit ("she said, her voice low"). One or two
  story groups follow. Untick the comma group in Phrase Bias if prose feels clipped.
- **Samplers** are always your Global preset, unchanged for every story: temperature 1.2, top-k 90,
  top-p 0.92, frequency 0.3, presence 0.4, phrase repetition penalty medium, output length 256. To
  change them, edit FIXED_SETTINGS in the Project 3 instructions.
- **Lorebook layout:** always-on Core Memory, Voice Guard, and a one-line-per-person **Characters**
  roster, a **Story So Far** skeleton you fill in by hand during play (plus a **Glossary** when there
  are minor places or terms), then keyed entries for Tier 1
  and 2, then the Operator Reference. No categories. Each entry's priority decides what NovelAI trims
  first when context is tight: always-on entries are never trimmed, Main Cast outranks supporting
  cast. Character entries stay active for 4,000 characters after their name was last mentioned.
- **Character entries** split appearance into Build, Face, Hair, Eyes, Clothing, and Mannerisms, and
  carry one ordinary sample line of dialogue (Quote) as a voice anchor.
- **Recompiling mid-story:** importing a scenario always makes a new story. To refresh an ongoing
  story, send `LOREBOOK`, save as `.lorebook`, and import it into that story's lorebook; copy other
  fields by hand.
- **Story So Far:** always on, priority 700, never trimmed, so it is dropped whole if it ever won't
  fit; keep it short. Project 3 fills `Earlier:` from the bible's Recent Events & Temporary Conditions
  (a fresh wound, a recent incident) and `Upcoming (not happened yet):` from its Known Upcoming. There
  is no `Now:` line; the prologue covers the opening scene. In play, add past events to Earlier as
  plain bullet facts with their consequence, add coming events to Upcoming and move each to Earlier
  once it happens, and squash old lines into one. Keep the Upcoming label so the model never treats
  those lines as done. Every past event goes here and nowhere else, even one about a single
  character; edit a character's entry only to change a standing fact such as a relationship.

---

## 8. Troubleshooting

| Symptom | Fix |
|---|---|
| NovelAI won't import the file | Make sure it ends in `.scenario`, not `.scenario.txt`. If it was cut off, send `SYNC SCENARIO` and save again. |
| Two code blocks after a cut-off | Join them in order in one file before saving. |
| Characters drift into clinical or analytical talk mid-session | Edit the first drifted line out of the story text — the model copies recent text. Check the Voice Guard entry is Always On. |
| A character mentions something that hasn't happened | Delete the line from that lorebook entry in NovelAI. |
| A gentle story came back with a villain | In Project 1, send `GENRE: <your tags>`. |
| The Operator Reference is firing | Clear its keys and disable it. |
| Bible cut off mid-way | `CONTINUE`, then join the two code blocks. |
