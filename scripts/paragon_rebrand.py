#!/usr/bin/env python3
"""Rebrand the PhotoCraft sources as Paragon Photo.

Paragon Photo is a personal fork of PhotoCraft (https://github.com/storytold/photocraft, MIT OR
Apache-2.0). This script changes what a person sees or types, and leaves the internals alone so
that upstream fixes keep merging cleanly. It is idempotent: run it again after merging upstream
(`git merge upstream/main`) and it rebrands whatever the merge brought in.

    python3 scripts/paragon_rebrand.py            # rewrite the tree
    python3 scripts/paragon_rebrand.py --check    # list files that still need it, change nothing

Renamed (user-facing):
  * the product name: "PhotoCraft" -> "Paragon Photo" in text, "ParagonPhoto" where it is part of
    a path or identifier (PhotoCraft.app, PhotoCraftData, ...);
  * the binaries: photocraft -> paragon-photo, photocraft-cli -> paragon-photo-cli (and the MCP
    server's name, the settings folder, the window title, installers, docs);
  * the app id: ai.storyteller.photocraft -> io.github.aryez.paragonphoto (file names too).

Kept on purpose:
  * every URL (upstream issues, the corpus, craft-libs and craft-i18n are real places);
  * Cargo package and crate names (photocraft-engine, photocraft_doc::, PhotocraftApp, ...),
    PHOTOCRAFT_* environment variables and log targets: renaming ~30,000 internal references would
    make every upstream merge conflict, and nobody sees them;
  * the .pcraft format, its MIME type (application/x-photocraft) and XMP namespace, so files stay
    compatible with PhotoCraft;
  * names that live in dependencies: craft::update::suite::PHOTOCRAFT, the craft.artcraft theme id,
    craft-i18n's photocraft.tsv, the photocraft-corpus repository;
  * LICENSE*, NOTICE, ATTRIBUTION.md and contributor credits: the MIT/Apache licences require the
    original copyright notices to stay.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

APP_ID_OLD = "ai.storyteller.photocraft"
APP_ID_NEW = "io.github.aryez.paragonphoto"
NAME = "Paragon Photo"  # prose
IDENT = "ParagonPhoto"  # paths, bundle names, identifiers
BIN = "paragon-photo"
CLI = "paragon-photo-cli"

# Files never touched (licences and credits must keep the original notices; generated or vendored
# data; the web apps are no longer built; this script and the logo generator).
EXCLUDE = [
    re.compile(p)
    for p in (
        r"^\.git/",
        r"(^|/)Cargo\.lock$",
        r"(^|/)Cargo\.toml$",  # manifests: package names stay; binaries are edited below
        r"^LICENSE",
        r"^NOTICE$",
        r"^ATTRIBUTION\.md$",
        r"^AGENTS\.md$",  # upstream's contributor rules; Paragon Photo's own guide is CLAUDE.md
        r"^README\.md$",  # hand-written for Paragon Photo (credits PhotoCraft by name)
        r"^CLAUDE\.md$",
        r"^contributors/",
        r"^licenses/",
        r"(^|/)LICENSE[^/]*$",
        r"^book/src/project/(licenses|credits)\.md$",
        r"^docs/brand/",
        r"^apps/photocraft-web",
        r"^craft-i18n\.rev$",
        r"^scripts/paragon_",
        r"(^|/)tests?/fixtures/",
    )
]
# Binary files: renamed when their path carries the app id, never edited.
BINARY = re.compile(r"\.(png|jpe?g|gif|ico|icns|psd|tif+|webp|wasm|bin|gz|zip|pdf|ttf|otf|woff2?|DS_Store)$")

# Text kept verbatim wherever it appears (masked before the rules run, restored after).
PROTECT = [
    re.compile(p, re.M)
    for p in (
        r"^.*paragon:keep.*$",  # a line that names upstream PhotoCraft on purpose
        r"https?://[^\s\"'<>)\]`]+",  # every URL
        r"\bstorytold[/_][A-Za-z0-9_.-]+",
        r"photocraft-corpus",
        r"photocraft\.tsv",
        r"suite::PHOTOCRAFT",
        r"application/x-photocraft",
        r"craft\.artcraft",
        r"(?:-p|--package)[ =]+photocraft[\w-]*",
        r"\"-p\",\s*\"photocraft[\w-]*\"",
        r"\bapps/photocraft[\w-]*",  # the app directories (not the hicolor .../apps/<app id> icons)
        r"package\.photocraft[\w-]*",
        r"package\s*=\s*\"photocraft[\w-]*\"",
        r"photocraft::[\w:]+",  # log targets and module paths
        r"\bPhotocraft[A-Z]\w*",  # Rust type names (PhotocraftApp, PhotocraftMcp, ...)
        r"\bPHOTOCRAFT\w*",  # constants and environment variables
    )
]

# Exact edits in Rust sources, where a lowercase "photocraft" may be a package name, a log target
# or a test word, so no pattern can tell them apart: (path, old, new). Each is applied if `old` is
# still there.
RUST_EDITS = [
    # The settings folder (craft-settings' APP_ID, craft-ui's AppInfo.id) and the config/state dirs.
    ("crates/engine/src/prefs.rs", 'const APP_ID: &\'static str = "photocraft";', f'const APP_ID: &\'static str = "{BIN}";'),
    ("crates/ui-egui/src/app/framework.rs", 'AppInfo { id: "photocraft",', f'AppInfo {{ id: "{BIN}",'),
    ("crates/ui-egui/src/dialogs/tests.rs", 'AppInfo { id: "photocraft",', f'AppInfo {{ id: "{BIN}",'),
    ("crates/automation/src/app_dirs.rs", '.map(|c| c.join("photocraft"))', f'.map(|c| c.join("{BIN}"))'),
    ("apps/photocraft/src/app_dirs.rs", 'state.join("photocraft")', f'state.join("{BIN}")'),
    ("apps/photocraft/src/app_dirs/tests.rs", '.join(".config").join("photocraft")', f'.join(".config").join("{BIN}")'),
    ("apps/photocraft/src/app_dirs/tests.rs", '.join("state").join("photocraft")', f'.join("state").join("{BIN}")'),
    # The MCP server's name, as clients list it.
    ("crates/automation/src/server/conventions.rs", 'Implementation::new("photocraft",', f'Implementation::new("{BIN}",'),
    ("crates/automation/tests/it/mcp.rs", '.name, "photocraft");', f'.name, "{BIN}");'),
    ("apps/photocraft-cli/tests/it/cli.rs", '["serverInfo"]["name"], "photocraft",', f'["serverInfo"]["name"], "{BIN}",'),
    ("apps/photocraft-cli/tests/it/cli.rs", '["serverInfo"]["name"], "photocraft");', f'["serverInfo"]["name"], "{BIN}");'),
    # The desktop binary, wherever code names it.
    ("crates/automation/src/live.rs", '{ "photocraft.exe" } else { "photocraft" }', f'{{ "{BIN}.exe" }} else {{ "{BIN}" }}'),
    ("apps/photocraft/src/services.rs", '|| "photocraft".to_string()', f'|| "{BIN}".to_string()'),
    ("apps/photocraft/src/launch_args.rs", '#[command(name = "photocraft",', f'#[command(name = "{BIN}",'),
    ("apps/photocraft/src/launch_args.rs", 'OsString::from("photocraft")', f'OsString::from("{BIN}")'),
    ("apps/photocraft/src/app_icon.rs", 'Path::new("photocraft")', f'Path::new("{BIN}")'),
    ("apps/photocraft/build.rs", '.set("InternalName", "photocraft")', f'.set("InternalName", "{BIN}")'),
    ("apps/photocraft/tests/it/main.rs", 'NEXTEST_BIN_EXE_photocraft"', 'NEXTEST_BIN_EXE_paragon_photo"'),
    ("apps/photocraft-cli/tests/it/main.rs", "NEXTEST_BIN_EXE_photocraft_cli", "NEXTEST_BIN_EXE_paragon_photo_cli"),
    # The case-sensitivity probe makes `.ParagonPhotoCaseProbe-*` and looks for its lower-case twin:
    # the name it replaces must be the probe's (identifier form), not the prose form.
    ("crates/engine/src/cmd/file_cmds/paths.rs", 'name.replacen("Paragon Photo", "photocraft", 1)', 'name.replacen("ParagonPhoto", "paragonphoto", 1)'),
]

# Binary names in the two app manifests (the packages keep their names).
MANIFEST_EDITS = [
    ("apps/photocraft/Cargo.toml", 'default-run = "photocraft"\n', f'default-run = "{BIN}"\n'),
    ("apps/photocraft/Cargo.toml", 'description = "PhotoCraft: an open-source, native image editor"',
     f'description = "{NAME}: a personal build of PhotoCraft, an open-source native image editor"'),
    ("apps/photocraft-cli/Cargo.toml", 'description = "Headless PhotoCraft:', f'description = "Headless {NAME}:'),
    ("apps/photocraft-cli/Cargo.toml", '[[bin]]\nname = "photocraft-cli"', f'[[bin]]\nname = "{CLI}"'),
]
# apps/photocraft has no [[bin]] table (the binary is named after the package), so one is added.
DESKTOP_BIN_TABLE = f'\n[[bin]]\nname = "{BIN}"\npath = "src/main.rs"\n'

# Rules for every rebranded file, in order.
GLOBAL_RULES = [
    (re.compile(re.escape(APP_ID_OLD)), APP_ID_NEW),
    (re.compile(r"CARGO_BIN_EXE_photocraft-cli"), f"CARGO_BIN_EXE_{CLI}"),
    (re.compile(r"CARGO_BIN_EXE_photocraft(?![\w-])"), f"CARGO_BIN_EXE_{BIN}"),
    # The product name: identifier/path form when glued to more name, prose form otherwise.
    (re.compile(r"PhotoCraft(?=[A-Za-z0-9_]|-[A-Za-z0-9]|\.[A-Za-z])"), IDENT),
    (re.compile(r"(?<=[/\\])PhotoCraft(?=[/\\\"']|$)", re.M), IDENT),
    (re.compile(r"PhotoCraft"), NAME),
    (re.compile(r"\bPhotocraft(?![A-Za-z0-9_])"), IDENT),
]
CLI_RULE = (re.compile(r"photocraft-cli"), CLI)
# Lowercase "photocraft" as a command or path word, outside Rust (docs, scripts, packaging).
BARE_RULE = (
    re.compile(r"(?:(?<=^)|(?<=[\s/\"'`(\\=]))photocraft(?=$|[\s\"'`),/:\]]|\.exe\b|\.(?=\s|$))(?!::)", re.M),
    BIN,
)
# Rust files where "photocraft-cli" is a package name, not the binary.
CLI_RULE_SKIP = {"xtask/src/layers.rs"}


def tracked_files(root: Path) -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=root, check=True, capture_output=True).stdout
    return [p for p in out.decode().split("\0") if p]


def excluded(path: str) -> bool:
    return any(r.search(path) for r in EXCLUDE)


def is_text(data: bytes) -> bool:
    return b"\0" not in data[:8192]


def mask(text: str):
    saved: list[str] = []

    def keep(m):
        saved.append(m.group(0))
        return f"\x00{len(saved) - 1}\x00"

    for r in PROTECT:
        text = r.sub(keep, text)
    return text, saved


def unmask(text: str, saved: list[str]) -> str:
    # Nested masks (a URL inside a later match) unwind innermost-last, so loop until stable.
    while "\x00" in text:
        new = re.sub(r"\x00(\d+)\x00", lambda m: saved[int(m.group(1))], text)
        if new == text:
            break
        text = new
    return text


def rebrand_text(path: str, text: str) -> str:
    body, saved = mask(text)
    for r, new in GLOBAL_RULES:
        body = r.sub(new, body)
    if path not in CLI_RULE_SKIP:
        body = CLI_RULE[0].sub(CLI_RULE[1], body)
    if not path.endswith(".rs"):
        body = BARE_RULE[0].sub(BARE_RULE[1], body)
    return unmask(body, saved)


def apply_exact(root: Path, edits, check: bool, changed: list[str]):
    for rel, old, new in edits:
        f = root / rel
        if not f.exists():
            continue
        s = f.read_text()
        if old in s:
            changed.append(rel)
            if not check:
                f.write_text(s.replace(old, new))


def main() -> int:
    ap = argparse.ArgumentParser(description="Rebrand PhotoCraft as Paragon Photo (idempotent).")
    ap.add_argument("--root", default=".", help="repository root")
    ap.add_argument("--check", action="store_true", help="list what would change, change nothing")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    changed: list[str] = []

    # 1. Files whose names carry the app id.
    for rel in tracked_files(root):
        if APP_ID_OLD in rel and not excluded(rel):
            dst = rel.replace(APP_ID_OLD, APP_ID_NEW)
            changed.append(f"{rel} -> {dst}")
            if not args.check:
                (root / dst).parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(["git", "mv", "-f", rel, dst], cwd=root, check=True)

    # 2. Text rules.
    for rel in tracked_files(root):
        if excluded(rel) or BINARY.search(rel):
            continue
        f = root / rel
        if not f.is_file() or f.is_symlink():
            continue
        data = f.read_bytes()
        if not is_text(data):
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        new = rebrand_text(rel, text)
        if new != text:
            changed.append(rel)
            if not args.check:
                f.write_bytes(new.encode("utf-8"))

    # 3. Exact edits: Rust sources and the app manifests.
    apply_exact(root, RUST_EDITS, args.check, changed)
    apply_exact(root, MANIFEST_EDITS, args.check, changed)
    desktop = root / "apps/photocraft/Cargo.toml"
    if desktop.exists() and f'name = "{BIN}"' not in desktop.read_text():
        changed.append("apps/photocraft/Cargo.toml [[bin]]")
        if not args.check:
            s = desktop.read_text()
            # Before the first table after [package] so it sits with the package's own targets.
            s = s.replace("\n[features]", DESKTOP_BIN_TABLE + "\n[features]", 1)
            desktop.write_text(s)

    for c in changed:
        print(c)
    print(f"{len(changed)} change(s){' needed' if args.check else ''}.", file=sys.stderr)
    return 1 if (args.check and changed) else 0


if __name__ == "__main__":
    sys.exit(main())
