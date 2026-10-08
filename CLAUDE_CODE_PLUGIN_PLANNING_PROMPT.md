# Worldloom → one-shot plugin: planning prompt for Claude Code

Paste everything below the line into a new Claude Code session started in the folder where you unzipped `worldloom_handoff.zip`.

---

You are planning a Claude plugin called **worldloom**. It turns a story premise into a finished NovelAI `.scenario` file in one run. **This session is planning only.** Work in plan mode. Read, research, and design, then present the plan for my review. Do not create, edit, move, or install anything until I approve the plan. I will execute it in a later step.

## What exists today

Worldloom is a three-stage pipeline that currently runs as three separate Claude Projects. I copy-paste between them by hand. The source files are in `./worldloom_source/`:

| File | Role today |
|---|---|
| `P1_STORY_BIBLE_ARCHITECT_INSTRUCTIONS.md` | Stage 1. Premise → Roleplay Story Bible (seven labelled sections, emitted as one code block starting `TIER: <tier>`). |
| `KB_GENRE_PROFILES.md` | Stage 1 knowledge file (genre contract reference). Only Stage 1 reads it. |
| `P2_EDITORIAL_CRITIQUE_INSTRUCTIONS.md` | Stage 2. Bible → four-header critique plus a revised bible (revise, don't recast). |
| `P3_NOVELAI_CONFIG_COMPILER_INSTRUCTIONS.md` | Stage 3. Bible → NOTES plus one NovelAI `.scenario` JSON (Memory/ATTG, Author's Note, System Prompt, Prefill, lorebook, phrase bias, fixed sampler settings, Prologue). |
| `SAMPLE_TEST_BIBLE_FOR_P3.md` | A compliant Stage-1/2 bible (Tablet tier, with a `POV:` line) for testing Stage 3. |
| `The_Quiet_Ledger.scenario` | A known-good Stage-3 output for that sample bible: the reference shape. |
| `WORLDLOOM_MODULAR_ARCHITECTURE.md` | The operator's guide: tiers, commands, Story So Far, NovelAI details. |
| `Sages_Simple_Story_Setup_GLM.scenario`, `Blackfeather_Estate.scenario` | Community GLM-4.6 scenarios the format was derived from. Reference only. |

Read every file in full before planning, and treat them as the source of truth. They encode many hard-won rules, including:
- the T0 horizon and the premise leak sweep;
- the Genre Contract and Cast Necessity;
- Voice rules and the analytical-register ban stack;
- prologue dialogue rules;
- the Story So Far design;
- fixed sampler settings and fixed JSON blocks;
- tier budgets.

## Goal

A plugin that, from one command and my premise, produces:
1. the Stage 1 bible;
2. the Stage 2 critique and revised bible;
3. a validated `<Title>.scenario` file, ready to import into NovelAI.

The quality must be the same as running the three Projects by hand, or better.

## Requirements

1. **Preserve the instructions.** Each stage's rules carry over substantively verbatim. Change only what the new runtime requires: input/output plumbing, code-block versus file output, CONTINUE/command sections that no longer apply. List every such change in the plan with the reason. Do not weaken, merge away, or "simplify" any rule. Do not reintroduce mature-content or adaptation features; those were deliberately removed.
2. **Independent critique.** Where subagents are available (Cowork, Claude Code), Stage 2 runs as its own subagent with a fresh context, so it never critiques its own draft. Each stage passes artifacts through files on disk, not by pasting them back through the orchestrator's context.
3. **Works across surfaces.** It must work in Claude Code and Cowork with subagents, and degrade gracefully in regular claude.ai chat. Chat loads skills and commands but ignores agents and hooks, so there the stages run sequentially in one conversation. On the Free plan the skills must also be usable on their own, uploaded individually, because plugins need a paid plan.
4. **Per-stage models.** Each subagent declares its model. Proposed: Stage 1 Opus, Stage 2 Sonnet, Stage 3 Sonnet. Evaluate whether Haiku 5.5 is viable for Stage 3, and make the choice easy to change.
5. **Deterministic validation.** Add a stdlib-only Python validator for the `.scenario`, with no network and no dependencies. It checks:
   - the JSON parses;
   - the top-level key order;
   - FIXED_SETTINGS, DEFAULT_ENTRY, contextDefaults, storyContextConfig and the comma bias group match exactly;
   - `categories` is `[]`;
   - entry ids follow the pattern and are unique;
   - each entry's activation, budgetPriority, trimDirection and searchRange match the role table;
   - the Story So Far shape is right (Earlier list, `Upcoming (not happened yet):` label, no `Now:` line);
   - Memory is one ATTG line whose title matches;
   - the Prologue has no blank lines;
   - none of the banned names appear;
   - the tier budget estimates (characters ÷ 4) are within caps.

   On failure, Stage 3 gets the error list and fixes the file, with a bounded number of retries. Then it reports.
6. **Consider a builder script.** Evaluate splitting Stage 3 as follows: the model writes only the variable content as compact JSON (texts, keys, entry list, prologue, bias groups, filled system prompt and prefill), and a script assembles the full `.scenario` from the fixed blocks. That would cut output tokens and copy errors. Recommend it or reject it with reasons. If you recommend it, the validator still runs on the assembled file.
7. **Token efficiency.** Use progressive disclosure: SKILL.md bodies stay lean, and large references (genre profiles, the system-prompt template, fixed JSON blocks) live in reference files loaded only when needed. Report the expected tokens loaded per stage compared with today (Projects load about 9.1k, 3.1k, and 12k).
8. **The run.**
   - One command, for example `/worldloom`. It takes the P1 input block: TIER, optional START, Story Premise, Character Dynamics, Character Backgrounds, Genre Tags, and optional POV.
   - Optional switches: `--pause` stops after the bible for my review; `--skip-critique` skips Stage 2.
   - Separate commands also re-run a single stage on an existing bible, matching today's Projects:
     - compile only;
     - critique only;
     - re-compile for another tier or POV;
     - emit a lorebook only, as a `.lorebook` file.
   - Outputs go to `./worldloom-output/<slug>/`: `bible_v1.txt`, `critique.md`, `bible_v2.txt`, `notes.md`, `<Title>.scenario`, `validation.txt`.
   - The final message says where the file is and which checks passed.
9. **Installation.** Install the plugin as part of execution (after my approval):
   - in Claude Code, through a local marketplace in the plugin repo, so it persists across sessions;
   - also produce a zip I can upload in claude.ai under Customize → Plugins → Upload plugin;
   - also produce a separate zip per skill for Free-plan upload under Customize → Skills.
   - Verify the install, for example with `/plugin` showing worldloom enabled and the command available.
10. **Testing.**
    - Stage 3 alone on `SAMPLE_TEST_BIBLE_FOR_P3.md`: the validator passes, and you compare the result structurally with `The_Quiet_Ledger.scenario`.
    - A full end-to-end run on a short invented premise.
    - A deliberately broken scenario that the validator must reject.
    - Report the token use of each test run.

## Research before planning

Do not rely on memory for plugin mechanics. Fetch and read the current official docs on:
- plugin structure and the manifest (`.claude-plugin/plugin.json`);
- components (skills, commands, agents with their frontmatter including `model` and `tools`, hooks);
- local marketplaces (`marketplace.json`), installing (`/plugin marketplace add`, `/plugin install`), and loading or testing with `--plugin-dir`;
- the platform-support matrix (what chat, Cowork, and Claude Code each load).

Useful starting points: https://code.claude.com/docs/en/plugins/overview, https://code.claude.com/docs/en/plugins/create, https://code.claude.com/docs/en/sub-agents, https://claude.com/docs/plugins/platform-support, https://claude.com/docs/plugins/build. Cite what you relied on.

## What the plan must contain

1. **Architecture:** the full file tree of the plugin with each file's purpose. Show how the orchestrator, subagents, skills, commands, scripts, and reference files connect, and how the chat fallback works.
2. **Source mapping:** for each source document, where its content goes and every adaptation made, with the reason.
3. **Stage hand-off contract:** the file names and formats passed between stages, and how failures and retries work.
4. **The validator's full check list and the builder-script decision.**
5. **Model choice per stage**, with reasons and how to change it.
6. **Token estimate** per stage, compared with today.
7. **Step-by-step execution order** I can approve: build, install, test. Include exact install and verification commands.
8. **Test plan** with pass criteria.
9. **Risks and open questions** for me, kept short. Ask only what you cannot reasonably decide yourself.

Keep the plan concise and concrete. When it's ready, present it for review and stop.
