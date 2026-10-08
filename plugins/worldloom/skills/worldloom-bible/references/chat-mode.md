# Stage 1 without file tools

Use this when you cannot write files. These are the original output rules; they replace the OUTPUT FORMAT section of SKILL.md. Every other rule in SKILL.md still applies.

=====================================================================
OUTPUT FORMAT
=====================================================================

The whole bible in one plain code block, so it copies in one action. First line inside the block, exactly: "TIER: <tier>", then a blank line, then Section 1 through the last line of Section 7. If the user gave no tier, write "TIER: Tablet" and put one line above the block: "No tier given; using Tablet." Nothing else outside the block.

Inside the block: plain text; no markdown headers, bold, italics, or inline code; section headings are the numbered lines above; "-" bullets only; never a line made only of three or more -, *, or _; never four asterisks or three dashes; at most one blank line between blocks.

=====================================================================
CONTINUATION
=====================================================================

If cut off, the user sends CONTINUE. Open a new code block and resume exactly where the text stopped, mid-sentence if necessary, with no repetition, no TIER line, and no commentary. The user joins the two blocks.

Self-check line that replaces the file line in SKILL.md:
- Code block; first line "TIER: <tier>"; seven sections in order; nothing outside except the permitted tier line.

=====================================================================
COMMANDS
=====================================================================

- CONTINUE — resume a cut-off bible as described above.
- REVISE <instruction> — re-emit the complete bible with the change applied, never a diff.
- TIER: <name> — regenerate against another tier's ceilings.
- GENRE: <tags> — regenerate with a different genre reading, re-running the Genre Contract first.
