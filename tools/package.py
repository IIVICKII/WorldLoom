"""Build the upload zips in dist/: the whole plugin, and one zip per skill.

Run: python tools/package.py
Each zip has one top-level folder (the plugin, or the skill) and forward-slash entry names.
"""
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins/worldloom"
DIST = ROOT / "dist"


def pack(folder, zip_name):
    files = sorted(f for f in folder.rglob("*") if f.is_file() and "__pycache__" not in f.parts)
    with zipfile.ZipFile(DIST / zip_name, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, (Path(folder.name) / f.relative_to(folder)).as_posix())
    with zipfile.ZipFile(DIST / zip_name) as z:
        names = z.namelist()
        assert z.testzip() is None and len(names) == len(files)
        assert all(n.startswith(folder.name + "/") and "\\" not in n for n in names), names
    print("%-28s %3d files %7d bytes" % (zip_name, len(files), (DIST / zip_name).stat().st_size))


if __name__ == "__main__":
    DIST.mkdir(exist_ok=True)
    pack(PLUGIN, "worldloom-plugin.zip")
    for skill in sorted((PLUGIN / "skills").iterdir()):
        assert (skill / "SKILL.md").is_file(), skill
        pack(skill, skill.name + ".zip")
