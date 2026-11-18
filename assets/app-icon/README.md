# Paragon Photo app icon

The Paragon family's app icon, as the PR7 plugins draw it (Paragon-PR7-S `source/ui/Logo.cpp`,
`Logo::drawAppIcon`), with a **PP** monogram and the **PARAGON PHOTO** mark.

Every file here is generated. Change `scripts/paragon_logo.py` and run, from the repository root:

```bash
python3 scripts/paragon_logo.py
```

## Design

- **Tile:** a rounded square (corner 20% of the size) in pearl onyx, `#1d171c` at the top to
  `#070508` at the foot, with the family's red glow edge `#ff4a3a` and a fainter inner glow ring.
- **Monogram:** heavy, wide, forward-slanted block letters (slant 0.3), drawn from vector outlines
  on the PR7 mark's grid (1 unit tall, stems 0.24, bars 0.2, bevelled corners), with two "speed
  cuts" through their lower half (63–68% and 79–83% of the height). The first P is in the family
  gradient, pink `#de0639` to orange `#cd6619`; the second in pearl white `#f4eeea`.
- **Name:** the family's neon stripe (pink → red → orange at 75%), then PARAGON in pearl white and
  PHOTO in the accent red `#e0103c`, as the PR7 mark draws its 7. Left out at 16 and 32 px, where it
  can't be read.

## Files

File names are PhotoCraft's, so the build and packaging scripts find them unchanged. <!-- paragon:keep -->

- `photocraft.svg`, `photocraft-small.svg`: vector master (1024-unit tile).
- `photocraft-1024.png`: 1024 px render on Apple's 824/1024 icon grid; `photocraft.icns` from it.
- `photocraft.ico`: Windows icon, 16–256 px, embedded in the `.exe` by `apps/photocraft/build.rs`.
- `hicolor/<size>/apps/io.github.aryez.paragonphoto.png` (16–512) and
  `hicolor/scalable/apps/io.github.aryez.paragonphoto.svg`: Linux icon theme.

Licence: see `LICENSE.txt` (the repository owner's; not covered by the code licence).
