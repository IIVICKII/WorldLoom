"""Checks that no stage rule was lost: every non-blank line of the source instructions is in the plugin.

Run: python tests/test_verbatim.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins/worldloom"
SOURCES = ["P1_STORY_BIBLE_ARCHITECT_INSTRUCTIONS.md", "KB_GENRE_PROFILES.md",
           "P2_EDITORIAL_CRITIQUE_INSTRUCTIONS.md", "P3_NOVELAI_CONFIG_COMPILER_INSTRUCTIONS.md"]
# Source lines allowed to be absent, each with its reason. Empty: every adaptation keeps the original line in a reference file.
ALLOWED = {}


def main():
    have = {l.strip() for f in PLUGIN.rglob("*.md") for l in f.read_text(encoding="utf-8").split("\n")}
    missing = [(name, i + 1, line) for name in SOURCES
               for i, line in enumerate((ROOT / "worldloom_source" / name).read_text(encoding="utf-8").split("\n"))
               if line.strip() and line.strip() not in have and line.strip() not in ALLOWED]
    for name, number, line in missing:
        print("MISSING %s:%d: %s" % (name, number, line[:100]))
    assert not missing, "%d source lines are not in the plugin" % len(missing)
    print("verbatim: every non-blank line of %d source files is in the plugin" % len(SOURCES))

    # The stage rules must be in the files a stage always loads, not only somewhere in the tree.
    moved = {l.strip() for f in PLUGIN.rglob("references/*.md") if f.name in ("chat-mode.md", "manual-json.md")
             for l in f.read_text(encoding="utf-8").split("\n")}
    for skill, source, extra in [("worldloom-bible", SOURCES[0], []), ("worldloom-critique", SOURCES[2], []),
                                 ("worldloom-compile", SOURCES[3], ["references/system-prompt-template.md"])]:
        loaded = {l.strip() for f in ["SKILL.md"] + extra
                  for l in (PLUGIN / "skills" / skill / f).read_text(encoding="utf-8").split("\n")}
        lost = [l for l in (ROOT / "worldloom_source" / source).read_text(encoding="utf-8").split("\n")
                if l.strip() and l.strip() not in loaded and l.strip() not in moved]
        assert not lost, (skill, lost[:3])
    print("always-loaded: each stage's rules are in its SKILL.md, except lines moved to chat-mode.md or manual-json.md")

    for skill in sorted((PLUGIN / "skills").iterdir()):
        text = (skill / "SKILL.md").read_text(encoding="utf-8")
        front = re.match(r"---\n(.*?)\n---\n", text, re.S).group(1).split("\n")
        keys = [l.split(":")[0] for l in front]
        assert keys == ["name", "description"], (skill.name, keys)
        assert front[0] == "name: " + skill.name and len(skill.name) <= 64, skill.name
        assert len(front[1]) - len("description: ") <= 1024, skill.name
        value = front[1][len("description: "):]
        assert value.startswith('"') or ": " not in value, skill.name + ": unquoted description with a colon breaks YAML"
    for agent in sorted((PLUGIN / "agents").glob("*.md")):
        front = re.match(r"---\n(.*?)\n---\n", agent.read_text(encoding="utf-8"), re.S).group(1)
        assert "name: " + agent.stem in front and re.search(r"^model: (inherit|opus|sonnet|haiku)$", front, re.M), agent.name
    plugin = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    assert plugin["name"] == market["plugins"][0]["name"] == "worldloom"
    assert (ROOT / market["plugins"][0]["source"] / ".claude-plugin/plugin.json").is_file()
    assert not (PLUGIN / "bin").exists(), "a top-level bin/ blocks install on claude.ai and Cowork"
    print("manifests parse; skill frontmatter is name + description only; agents name a model; no bin/")
    print("ALL PASS")


if __name__ == "__main__":
    sys.exit(main())
