# Stage 3 without the builder script

Use this when you cannot run Python. These are the original rules for writing the whole scenario JSON by hand; they replace the OUTPUT and THE SCENARIO CONTENT sections of SKILL.md. Every content rule in SKILL.md still applies. The System Prompt template is references/system-prompt-template.md: fill its bracketed places yourself and remove the bracket lines. Write the Voice Guard entry and the Prefill out in full.

Original input line:
The bible arrives as pasted text, possibly still inside a code block (ignore the fence). Its first line is "TIER: Tablet | Scroll | Opus". The operator may add "POV: first person past | first person present | second person present | third person limited past | third person limited present" for the Prologue. Without a POV line, the Prologue is third person limited past.

=====================================================================
OUTPUT — two parts, nothing else
=====================================================================

1. NOTES — plain text, short lines:
- "TIER: <tier>" (and "assumed" if it was missing); a derived Genre Contract, if you derived one.
- "Title: <chosen title>" then "Alternatives: <four to six more, grouped by the bible's genre tags>".
- "POV: <person and tense>", plus a note if the Prologue's two-speaker rule lapsed.
- Lorebook plan: one line per entry — name, tier, approximate tokens — including the always-on entries; any Narrative Weight deviation or demotion in a few words.
- "Estimated: Author's Note ~N / AN_CAP · System Prompt ~N / SP_CAP · Lorebook ~N / LB_CAP (Operator Reference excluded)".
- "Save the block below as <Title>.scenario and import it in NovelAI. It creates a new story."

2. The scenario JSON in one plain code block, and nothing after it. If this chat can create downloadable files, write the JSON to "<Title>.scenario" instead, parse it once to confirm it is valid, and replace the code block with one line naming the file.

The Prologue, Author's Note, System Prompt, Prefill, lorebook, and phrase bias appear only inside the JSON. Never write any of them out a second time as plain text.

=====================================================================
THE SCENARIO JSON
=====================================================================

Valid JSON on the first parse: every line break inside a string written as \n, every " as \", every \ as \\. No trailing commas, comments, or single quotes. Write it compactly: no indentation, one top-level key per line, one lorebook entry or bias group per line. Copy every FIXED block character for character.

Top-level keys, in this order:

{"scenarioVersion": 3,
"title": "<title>",
"description": "<the bible's logline, T0-safe>",
"prompt": "<PROLOGUE>",
"tags": [<the bible's genre tags as lowercase strings>],
"context": [{"text": "<MEMORY>", "contextConfig": {"prefix": "", "suffix": "\n", "tokenBudget": 1, "reservedTokens": 0, "budgetPriority": 800, "trimDirection": "trimBottom", "insertionType": "newline", "maximumTrimType": "sentence", "insertionPosition": 0}}, {"text": "<AUTHOR'S NOTE>", "contextConfig": {"prefix": "", "suffix": "\n", "tokenBudget": 1, "reservedTokens": 1, "budgetPriority": -400, "trimDirection": "trimBottom", "insertionType": "newline", "maximumTrimType": "sentence", "insertionPosition": -4}}],
"ephemeralContext": [],
"placeholders": [],
"settings": FIXED_SETTINGS,
"lorebook": {"lorebookVersion": 6, "entries": [<ENTRIES>], "settings": {"orderByKeyLocations": false}, "categories": []},
"author": "Worldloom",
"storyContextConfig": {"prefix": "***\n", "suffix": "", "tokenBudget": 1, "reservedTokens": 512, "budgetPriority": 0, "trimDirection": "trimTop", "insertionType": "newline", "maximumTrimType": "sentence", "insertionPosition": -1, "allowInsertionInside": true},
"contextDefaults": {"ephemeralDefaults": [{"text": "", "contextConfig": {"prefix": "", "suffix": "\n", "tokenBudget": 1, "reservedTokens": 1, "budgetPriority": -10000, "trimDirection": "doNotTrim", "insertionType": "newline", "maximumTrimType": "newline", "insertionPosition": -2}, "startingStep": 1, "delay": 0, "duration": 1, "repeat": false, "reverse": false}], "loreDefaults": [DEFAULT_ENTRY]},
"phraseBiasGroups": [<PHRASE BIAS>],
"bannedSequenceGroups": [{"sequences": [], "enabled": true}],
"messageSettings": {"systemPrompt": "<SYSTEM PROMPT>", "prefill": "<PREFILL>"}}

FIXED_SETTINGS (the operator's own sampler preset; never change any value for any story, whatever its genre or tone):
{"parameters": {"textGenerationSettingsVersion": 8, "temperature": 1.2, "max_length": 256, "min_length": 1, "top_k": 90, "top_p": 0.92, "top_a": 1, "typical_p": 1, "tail_free_sampling": 1, "repetition_penalty": 0, "repetition_penalty_range": 0, "repetition_penalty_slope": 0, "repetition_penalty_frequency": 0.3, "repetition_penalty_presence": 0.4, "repetition_penalty_default_whitelist": false, "cfg_scale": 1, "cfg_uc": "", "phrase_rep_pen": "medium", "top_g": 0, "mirostat_tau": 0, "mirostat_lr": 1, "math1_temp": 0, "math1_quad": 0, "math1_quad_entropy_scale": 0, "min_p": 0, "order": [{"id": "temperature", "enabled": true}, {"id": "top_k", "enabled": true}, {"id": "top_p", "enabled": true}, {"id": "min_p", "enabled": false}]}, "preset": "38454893-298c-4908-9ad4-3d8e28fc6653", "trimResponses": true, "banBrackets": true, "defaultBias": true, "prefix": "vanilla", "dynamicPenaltyRange": false, "prefixMode": 0, "mode": 0, "model": "glm-4-6"}

DEFAULT_ENTRY:
{"text": "", "contextConfig": {"prefix": "----\n", "suffix": "\n", "tokenBudget": 1, "reservedTokens": 0, "budgetPriority": 400, "trimDirection": "trimBottom", "insertionType": "newline", "maximumTrimType": "sentence", "insertionPosition": -1}, "lastUpdatedAt": 1727192381195, "displayName": "New Lorebook Entry", "id": "125f8dfa-a2a3-492c-b92f-c38cbf7aa8a2", "keys": [], "searchRange": 1000, "enabled": true, "forceActivation": false, "keyRelative": false, "nonStoryActivatable": false, "category": "", "loreBiasGroups": [{"phrases": [], "ensureSequenceFinish": false, "generateOnce": true, "bias": 0, "enabled": true, "whenInactive": false}], "advancedConditions": []}

IDs: every entry id is "00000000-0000-4000-8000-" plus a 12-digit zero-padded counter, starting at 000000000001 and rising by one per entry in order. Never reuse one; DEFAULT_ENTRY keeps its own fixed id.

ENTRIES — each is DEFAULT_ENTRY with only these fields changed: "text" (the entry content), "displayName" (the entry name, never empty), "id" (new), "keys", "searchRange", "contextConfig.budgetPriority", "contextConfig.trimDirection", plus "forceActivation" or "enabled" where stated. "category" stays "". Settings by role (NovelAI trims the lowest budgetPriority first when context is tight, so priority encodes what matters most):

Entry → activation · budgetPriority · trimDirection · searchRange:
- Core Memory, Voice Guard, Characters → forceActivation true · 800 · doNotTrim · 1000
- Story So Far → forceActivation true · 700 · doNotTrim · 1000
- Glossary → forceActivation true · 600 · trimBottom · 1000
- Tier 1 character → keys · 500 · trimBottom · 4000
- Tier 1 place, faction, lore → keys · 500 · trimBottom · 1000
- Tier 2 character → keys · 450 · trimBottom · 4000
- Tier 2 place, faction, lore → keys · 450 · trimBottom · 1000
- Operator Reference → enabled false · 400 · trimBottom · 1000

A character's searchRange of 4000 keeps their entry active for a while after their name was last mentioned; places and lore only need the recent passage. Never reword an entry name between compiles of the same story.

=====================================================================
CONTINUATION
=====================================================================

If cut off, the user sends CONTINUE: resume exactly where you stopped, character for character, in a new code block, with no repetition and no commentary; then add one line telling the operator to join the two blocks before saving. If the cut fell inside a JSON string, also offer SYNC SCENARIO.

Self-check line that replaces the file line in SKILL.md:
- NOTES, then one code block (or one file line), nothing after; no config field outside the JSON.

=====================================================================
COMMANDS
=====================================================================

- CONTINUE — resume a cut-off response.
- SYNC SCENARIO — re-emit only the complete current scenario JSON. Use after a bad cut or after any change.
- LOREBOOK — emit only {"lorebookVersion": 6, "entries": [...], "settings": {"orderByKeyLocations": false}, "categories": []} with the current entries, to save as "<Title>.lorebook" and import into a story already in progress.
- PROLOGUE — show the current Prologue as plain readable text, nothing else.
- TRIM — re-run the budget fit, then re-emit NOTES and the JSON.
- RECOUNT — re-estimate and re-emit only the Estimated line.
- POV: <person and tense> — rewrite the Prologue, then re-emit the JSON.
- TIER: <name> — recompile everything against that tier.
