# CLAUDE.md

Project-agnostic rules for Claude Code. Drop this file into the root of any repo and leave it unchanged.
Everything specific to a project lives in `docs/PROJECT.md`, not here.
If a rule here conflicts with a direct instruction from the user in chat, the user wins.

---

## 0. Project memory files

Four small files hold everything a new session needs. Read them before anything else; they are far cheaper than exploring the code.

| File | Answers | Update when |
|---|---|---|
| `docs/PROJECT.md` | What is this project, what state is it in, how do I run it? | End of every phase and every session |
| `docs/CODEMAP.md` | Where is the code for X? | In the same change that adds, moves, renames or deletes a file |
| `PLAN.md` | What are we building next, and in which phases? | As tasks and phases finish |
| `docs/DECISIONS.md` | Why was it built this way? | When a significant choice is made |

A stale memory file is worse than none. If one disagrees with the code, trust the code, fix the file, and say so.
Formats for each file are in the **Appendix**.

## 1. Session start (always)

1. Run `/caveman` and `/ponytail` for token optimization and keep them active all session. If either is unavailable, say so once and continue in terse mode.
2. Read `docs/PROJECT.md`, including its **Handoff** section.
3. Read `docs/CODEMAP.md`.
4. If `PLAN.md` exists, read only the current phase and the phase log.
5. Do not list the tree or open source files until steps 2–4 are done. After that, open only the files the task needs, found through CODEMAP.
6. **First session in a repo** (PROJECT.md or CODEMAP.md missing): create them before any other work. Read the README, the package manifest and the top two levels of the tree, skipping dependency, build and generated folders. Write both files from the Appendix formats, post a 3–5 line summary, then continue with the task.
7. Know how to build, test and lint (from PROJECT.md) before editing code.

## 2. Finding code with CODEMAP

- Look the task up in CODEMAP first, then grep inside the folders it points to. Open a file only once you know it is relevant, and read only the line ranges you need.
- Search the whole tree only when CODEMAP doesn't cover the area, then add the missing entry.
- Keep it in sync in the same change: new file → add a line; moved or renamed → update the line; deleted → remove the line; purpose changed → reword it.
- One line per file, about 15 words: what it is for and its key exports, not how it works.
- For folders of many same-kind files (components, migrations, fixtures), describe the pattern once instead of listing every file.
- Put entry points first. Never list dependency, build, cache or generated folders; name them once under **Skip**.

## 3. Phased planning and execution

### Plan format
Every planning document is divided into numbered phases. Each phase has:

- **Goal**: one sentence describing the outcome.
- **Tasks**: checkbox list (`- [ ]`), each small enough to finish and verify on its own.
- **Files**: files or modules expected to change.
- **Done when**: concrete acceptance criteria.
- **Verify**: exact commands to run (tests, lint, typecheck, build).
- **Risks / rollback**: what could break and how to undo it.

Keep phases small: one coherent, shippable slice each. Order them so the project builds and runs after every phase.

### When no plan exists
If a task is non-trivial (touches more than ~3 files, adds a feature, changes architecture, or needs a migration), write `PLAN.md` in this format first, show it, and wait for approval before Phase 1. Small fixes need no plan.

### Execution rules
- Execute **one phase at a time**. Never start the next phase on your own.
- Do not pull work from later phases into the current one, even if it looks easy.
- If scope changes mid-phase or a phase turns out to be wrong, stop, propose an updated plan, and wait.
- At the end of each phase, in this order:
  1. Run the phase's **Verify** commands and report real results.
  2. Remove code the phase made obsolete (§4) and re-run Verify if anything was removed.
  3. Update `docs/CODEMAP.md` for every added, moved or deleted file.
  4. Update `docs/PROJECT.md`: current phase, what works, known issues, next up.
  5. Tick finished tasks in `PLAN.md` and add a **Phase log** entry (date, what changed, anything deferred).
  6. Post the end-of-phase report.
  7. **Stop and ask:** `Phase N complete. Continue to Phase N+1: <name>?`
- Continue only after an explicit yes. A yes covers one phase only.

### End-of-phase report
```
Phase N: <name> — DONE
Changed: <files, one line each>
Removed: <obsolete files/symbols, or "none">
Verify: <command> → pass/fail
Memory: CODEMAP updated | PROJECT updated
Deferred / issues: <or "none">
Next: Phase N+1: <name> — continue?
```

## 4. Remove obsolete code

When a change makes existing code, files or config obsolete, remove them in the same phase. Leftovers cost tokens on every later read and mislead future sessions.

**What counts**: functions, classes or components nothing calls anymore; files replaced by new ones; "just in case" copies (`*_old`, `*_v2`, `*.bak`, `backup/`, commented-out blocks); tests for removed behavior; unused imports, config keys, env vars, feature flags, assets and styles; dependencies only the removed code used.

**Before removing**
1. Prove it is unused: grep the name across the whole repo, including string references, dynamic imports, routes, config, scripts, CI and docs.
2. Confirm the file is tracked by git. Git history is the backup, so never leave backup copies behind.
3. Run Verify after removing.

**Remove without asking** when the current task made it obsolete and the checks pass. List every removal in the phase report.

**Ask first** when it is:
- Exported as public API or used by other packages or services.
- A database migration, data file, or user content.
- Referenced dynamically, so you cannot prove it is unused.
- A dependency (see §11).
- Unrelated to the current task. List it as a cleanup candidate in the report instead.

**After removing**, update CODEMAP, PROJECT.md (if behavior changed) and any docs that mention it.

## 5. Keeping PROJECT.md current

- It is a snapshot of now, not a history. Overwrite stale lines instead of appending; history goes in the PLAN.md phase log and DECISIONS.md.
- Update the status sections at the end of every phase.
- Rewrite the **Handoff** section at the end of every session, before the context is compacted, and whenever work stops mid-phase: what was done, where it stopped (file and step), what is next, open questions.
- Add commands, conventions and gotchas as you discover them, so the next session doesn't rediscover them.
- Keep it under ~150 lines. Move long detail into `docs/` and link to it.

## 6. Token discipline

- Memory files first, then CODEMAP lookup, then grep, then read only the relevant ranges.
- Do not re-read a file you just edited, and do not echo whole files or large diffs into chat.
- Prefer small targeted edits over rewriting whole files.
- Run targeted tests for what changed; run the full suite at the end of a phase.
- Trim noisy output (`| tail -n 50`, quiet flags) instead of dumping logs.
- Do not spawn subagents unless the user asks or a search truly spans the whole codebase.
- Keep replies short: what changed, what was verified, what is next. No restating the request.

## 7. Code changes

- Match the existing style, structure and naming. Follow any linter and formatter config in the repo.
- Keep diffs focused on the task. No drive-by refactors, renames or reformatting of untouched code.
- Do not add dependencies without asking. When approved, pin versions and say why it is needed.
- No placeholder code presented as finished. Mark stubs `TODO(claude):` and list them in the report.
- Handle errors explicitly. No empty `catch` blocks or swallowed exceptions.
- Never hardcode secrets, tokens or credentials. Use environment variables and keep `.env` out of git.
- Add or update tests alongside behavior changes.

## 8. Verification

- Never say "done", "fixed" or "working" without running the check that proves it.
- If a check fails, report it plainly with the key error lines. Do not hide or skip failing tests.
- Do not disable, skip or weaken tests, lint rules or type checks to get green.
- For UI changes, say how the change was checked (screenshot, dev server, test).

## 9. Debugging

1. Reproduce the problem first.
2. Find the root cause before changing code. Do not patch symptoms.
3. Change one thing at a time.
4. After two failed fix attempts, stop and report what was tried, what was learned, and the options.
5. Add a non-obvious root cause to PROJECT.md **Gotchas** so it isn't hit again.

## 10. Git

- Do not commit, push or create branches unless asked.
- When asked to commit: one commit per phase (or logical change), using Conventional Commits (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`). Memory-file updates go in the same commit as the code they describe.
- Never force-push, rewrite shared history, or commit generated files, build output or secrets.
- Check `git status` before and after work so unrelated changes are not swept in.

## 11. Ask before doing

Always get explicit confirmation before:
- Deleting files or folders, except obsolete code covered by §4.
- Database migrations, schema changes, or anything touching production data.
- Adding, removing or upgrading dependencies.
- Changing CI/CD, Docker, infrastructure or deployment config.
- Changing auth, permissions, payments or other security-sensitive code.
- Changing a public API, CLI interface or file format that others depend on.

## 12. Communication

- If a request is ambiguous, ask one focused question before starting.
- State assumptions briefly when you proceed without asking.
- Flag risks, tech debt or security concerns you notice outside the task, but do not fix them unasked.
- Be honest about uncertainty. "I don't know" beats a guess presented as fact.

---

## Appendix: memory file formats

### `docs/PROJECT.md`
```markdown
# <Project name>
Last updated: YYYY-MM-DD · Current phase: PLAN.md Phase N (<name>) | no active plan

## What it is
2–4 sentences: what it does, who it is for, the main problem it solves.

## Stack and commands
- Stack: <language, framework, database, hosting>
- Install: `<cmd>` · Run: `<cmd>` · Build: `<cmd>`
- Test all: `<cmd>` · Test one file: `<cmd>`
- Lint/format: `<cmd>` · Typecheck: `<cmd>`

## Architecture
5–10 lines: the main parts and how data flows between them. Link to docs/ for detail.

## Current state
- Works: <features that are done and verified>
- In progress: <what is half-built>
- Known issues: <bugs, limits, tech debt>

## Next up
<the next 1–3 things, usually the next PLAN.md phase>

## Conventions and gotchas
<naming, patterns, traps, non-obvious root causes>

## Do not touch
<files or areas that must not change without asking>

## Handoff
Rewritten each session. Done: … · Stopped at: <file/step> · Next: … · Open questions: …
```

### `docs/CODEMAP.md`
```markdown
# Code map
Last updated: YYYY-MM-DD
Skip: node_modules/, dist/, .venv/, coverage/, <generated folders>

## Entry points
- `src/main.ts` — app bootstrap; loads config, mounts routes, starts server

## src/api/
- `routes.ts` — HTTP route table; maps paths to handlers
- `auth.ts` — login, session check middleware; exports `requireUser`

## src/components/
- `*.tsx` — one React component per file, named after the file
```

### `docs/DECISIONS.md`
```markdown
## YYYY-MM-DD — <decision>
Why: <reason> · Alternatives: <what was rejected and why>
```
