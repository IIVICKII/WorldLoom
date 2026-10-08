# scenario_content.json

The one file Stage 3 writes for the builder. It holds only what differs from story to story. `scripts/build_scenario.py` adds every fixed block and writes `<Title>.scenario`. Every value follows the rules in SKILL.md; this file gives only the shape.

```json
{
  "title": "<Title>",
  "description": "<the bible's logline, T0-safe>",
  "prologue": "<PROLOGUE: paragraphs joined by a single \n, no blank lines>",
  "tags": ["<genre tag>", "<genre tag>"],
  "memory": "[ Author: <author>; Title: <Title>; Tags: <tags>; Genre: <genre> ]",
  "authorsNote": "[ Write in a style that conveys the following: <style words> ]\n[ <narration guidance> ]",
  "systemPrompt": {
    "romance": false,
    "litrpg": false,
    "examples": false,
    "scenarioBans": ["<word>, <word>, <word>", "<word>, <word>"],
    "eventSystem": ["<one condition the AI may stage>", "<another>"]
  },
  "prefillContinuation": ["<line 1>", "<line 2>", "<line 3>"],
  "voiceGuardExtra": "<one sentence naming the extra register and its words>",
  "phraseBias": [
    {"words": ["<word>", "<word>", "<word>", "<word>"], "bias": 0.15},
    {"words": ["<word>", "<word>", "<word>", "<word>"], "bias": -0.3}
  ],
  "entries": [
    {"role": "core_memory", "text": "Core Memory\nType: memory\nWorld: ..."},
    {"role": "characters", "text": "Characters:\n<Name>: ..."},
    {"role": "story_so_far", "text": "Story So Far\nType: memory\nEarlier:\n- ...\nUpcoming (not happened yet):\n- ..."},
    {"role": "glossary", "text": "Glossary:\n<Name>: ..."},
    {"role": "tier1_character", "name": "<Full Name>", "keys": ["<first name>", "<surname>", "<title>", "<role word>"], "text": "<Full Name>\nType: character\nAge: ..."},
    {"role": "tier2_other", "name": "<Place Name>", "keys": ["<keyword>", "<keyword>", "<keyword>", "<keyword>"], "text": "<Place Name>\nType: location\nDescription: ..."},
    {"role": "operator_reference", "text": "OPERATOR REFERENCE ONLY - DO NOT ADD KEYS OR TRIGGERS TO THIS ENTRY. If this entry is ever given a keyword, its contents will enter the story and spoil it.\n..."}
  ]
}
```

## Fields

- `title` — the chosen title. It must equal the Title in `memory`. The output file is named after it.
- `tags` — the bible's genre tags as lowercase strings.
- `memory` — the one ATTG line.
- `authorsNote` — the style line first, then the narration guidance.
- `systemPrompt.romance` — true only when the Genre Contract includes romance. Adds the Showing Attraction block.
- `systemPrompt.litrpg` — true only for LitRPG. Adds the system-messages line.
- `systemPrompt.examples` — true only on Scroll and Opus, and only while the prompt stays under SP_CAP. Always false on Tablet. The Attraction example appears only when `romance` is also true.
- `systemPrompt.scenarioBans` — each string is a comma-separated word list. The builder writes it as one `- NEVER use: ...` line. Leave out the words `- NEVER use:`.
- `systemPrompt.eventSystem` — each string is one bullet of the Dynamic Event System. Leave out the leading `- `.
- `systemPromptOverride` — optional. The complete System Prompt text. Use it only when budget fit needs tighter template wording, or when the operator has asked for the analytical-register line to go. It replaces `systemPrompt`. Keep every `##` header in order, the fixed ban lines and the Names line.
- `prefillContinuation` — optional. Exactly three lines for the Prefill's Continuation block, without the leading `- `. Left out, the three default lines are used.
- `voiceGuardExtra` — optional. One or more sentences added to the end of the Voice Guard's Forbidden line.
- `phraseBias` — one or two story groups. `words`: four to eight single lowercase words. `bias`: within ±0.5. The builder adds the fixed comma group first and sets `generateOnce` from the sign.
- `entries` — in lorebook order, without Voice Guard. The builder inserts Voice Guard second and numbers the ids.

## Entry roles

Give every entry one role. The role sets activation, priority, trim and search range; you never write those.

| Role | Use for | `name` | `keys` |
|---|---|---|---|
| `core_memory` | Core Memory, always first | fixed | none |
| `characters` | the Characters roster | fixed | none |
| `story_so_far` | Story So Far | fixed | none |
| `glossary` | Glossary, only when something qualifies | fixed | none |
| `tier1_character` | Tier 1 character, including a known second form | required | four to six |
| `tier1_other` | Tier 1 place, faction or lore | required | four to six |
| `tier2_character` | Tier 2 character | required | four to six |
| `tier2_other` | Tier 2 place, faction or lore | required | four to six |
| `operator_reference` | Operator Reference, always last | fixed | none |

Order: `core_memory`, `characters`, `story_so_far`, `glossary` if any, every Tier 1 entry, every Tier 2 entry, `operator_reference`.

A character entry's second text line must be `Type: character`; the validator uses it to confirm the search range.

`text` holds the whole entry: line 1 the entry name, then the lines SKILL.md specifies. `name` is the display name and matches line 1.
