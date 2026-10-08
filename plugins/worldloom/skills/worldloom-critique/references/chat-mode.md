# Stage 2 without file tools

Use this when you cannot write files. These are the original output rules; they replace the OUTPUT FORMAT section of SKILL.md. Every other rule in SKILL.md still applies.

=====================================================================
OUTPUT FORMAT
=====================================================================

First the critique, in plain text under these four headers, in order:

Genre Fit Corrections
Inconsistencies Fixed
Plot Holes Fixed
Interest Improvements

One "-" bullet per change: what was wrong, what you changed, naming the entities involved. Keep each bullet to one or two sentences. Write "None found." under an empty header. If you derived or corrected the Genre Contract, or assumed Tablet, say so in one line above the first header.

Then the complete revised bible in one plain code block, ready to copy. Its first line is the tier, exactly "TIER: <tier>", then a blank line, then "1. Working Title, Tags & Logline" through the end of Section 7. Nothing after the code block.

Inside the block: plain text, no markdown headers, bold, or italics; "-" bullets only; never a line made only of three or more -, *, or _; never four asterisks or three dashes; at most one blank line between blocks.

=====================================================================
CONTINUATION
=====================================================================

If cut off, the user sends CONTINUE. Resume exactly where the text stopped with no repetition and no commentary. If the cut fell inside the code block, open a new code block and continue mid-text without a TIER line; the user joins the two.

Self-check line that replaces the file line in SKILL.md:
- Structure intact; code block with the TIER line first; no banned names (Elara, Lyra, Thorne, Valerius, Kael/Kaelen, Ava, Marcus).

=====================================================================
COMMANDS
=====================================================================

- CONTINUE — resume a cut-off response.
- CRITIQUE ONLY — the four-header critique with no revised bible.
- RE-RUN — a second pass over a revision the user pastes back. It should find markedly less; if the bible is sound, write "None found." under all four headers and re-emit it verbatim.
