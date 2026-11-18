# Paragon finishes: OBSIDIAN and AURORA (design reference) <!-- paragon:keep -->

The look Paragon Photo takes from the Paragon family plugins. Extracted from the Paragon PR7-D
sources (JUCE/C++; the most up-to-date of the family: PR7-G lacks AURORA's dimming and still uses
the older flat orange accent). Paths: `D/` = PR7-D `source/ui/`, `LAF` = `D/ParagonLookAndFeel.cpp`,
`LAFh` = its header, `FIN`/`FINh` = `D/Finish.cpp/.h`, `PB` = `D/PedalBody.cpp`.

JUCE maths used below: `brighter(k)`: c' = 255 − (255−c)/(1+k); `darker(k)`: c' = c/(1+k). "≈"
values are computed by hand (±1 for rounding).

## 0. The two finishes

- `Finish::Type { retiredPearlWhite = 0, obsidian = 1, aurora = 2 }`; **OBSIDIAN is the default**.
  Names shown: "OBSIDIAN", "AURORA" (FINh:25-30).
- **AURORA is dimmed 10%** (`auroraDimming = 0.10`, FINh:69): every pearl surface (chassis, face,
  panels, insets and their sheen) gets black @0.10 laid over it; `pearl(c)` = RGB × 0.9 (white → 230).
  Lettering, badge, neon, keys and screens are not dimmed.
- **Only the pearl and the lettering printed on it change.** Screens, neon, the dark panels round
  the unit, menus, tabs, buttons, and the black keys and knobs are the same on both (FINh:7-14).

## 1. Colour

### 1a. Palette (`ParagonColours`, LAFh:9-50)

| Name | ARGB | Use |
|---|---|---|
| background | FF060407 | window / page background |
| panel | FF0C0A0D | tooltip background |
| panelEdge | FF27222A | every 1 px border, separators, knob track |
| accent | FFF4353A | the family red, lit (drawn as the family gradient, see 1b) |
| accentDim | FF4E1016 | pressed / dim accent |
| meterRed | FFFF3B2F | level-meter LEDs |
| text | FFE8E8EA | main light text |
| textDim | FF8A8A92 | secondary text, labels |
| ink / inkDim | FF26252A / FF6B6569 | AURORA lettering |
| glow | FFFF4A3A | red-orange edge light |
| familyPink / Red / Orange | FFDE0639 / FFD42E2A / FFCD6619 | the family colours |
| widget | FF151217 | widget background (LAF:90) |
| menu | FF050405 | popup menus (LAF:107) |
| ledOrange | FFFF7A1A | LED screens (D/LedDisplay.h:53) |
| over 0 dB | FFFFA53B | meter amber |
| litBrightness / dimBrightness | 1.18 / 0.42 | gradient strength |

**Colour rule** (PR7-D CLAUDE.md): only hues ≈318° → 0° → 42° (pink, red, orange) plus pearl white
and onyx/greys. No green, blue, purple, yellow or cyan anywhere, including framework defaults.

### 1b. Family gradient (LAF:11-44)

Stops (left→right or top→bottom): DE0639 @0, D90738 @.25, D42E2A @.5, CF5C1C @.75, CD6619 @1,
each channel × brightness, clamped. `accent` fills are drawn as this gradient × 1.18 (≈ FF0743 →
FF0842 → FA3632 → F46D21 → F2781D); `accentDim` as × 0.42 (≈ 5D0318 → 591312 → 562B0A).
**Text never carries the gradient:** accent text draws white, accentDim text white × 0.45 alpha.

### 1c. Neon gradient (rings, bezels, fader slots; FIN:107-121)

The same five stops × **0.75** (≈ A6042B → A3052A → 9F221F → 9B4515 → 9A4C13), horizontal across
the ring. Big-knob ring: each stop `.brighter(0.35)`. Plain neon FF2E3A (core FFD6D6); neon bar /
LED FF3A2A (core FFF2EE), unlit CF3324.

### 1d. Finish-dependent colours (FIN:86-105)

| | OBSIDIAN | AURORA |
|---|---|---|
| ink | FFF1EAEE | FF26252A |
| inkDim | FF9A8F96 | FF6B6569 |
| stampEdge | black @0.75 | ≈E6E6E6 @0.70 |
| printedRed | ≈FF6153 (glow.brighter(.15)) | ≈DD4032 (glow.darker(.15)) |

### 1e. Satin grain (`makeSatinGrain`, FIN:123-156)

Per pixel, seeded random (seed 1234 for the unit, 7 for the drum machine; made at 2× and scaled):
- OBSIDIAN: 1/400 a fleck (white, FFC4DC or FFD8C8; alpha 30–89); else speckle alpha
  round(|s|×11), s ∈ [−1, 1], white if s > 0 else black.
- AURORA: 1/500 a fleck (white or FFD8E6; alpha 60–119); else speckle alpha round(|s|×9), white if
  s > 0 else 5A3A4A.

Drawn over every pearl surface, clipped to it. (Pixel-exact needs JUCE's LCG:
seed = (seed × 0x5DEECE66D + 11) & 0xFFFFFFFFFFFF.)

### 1f. Pearl surfaces (`PedalBody::paintUnit`, PB:131-263): AURORA / OBSIDIAN

- **Glow round the unit:** shadow in glow @0.42, radius 44g, offset (0, 14g); and FF3A5A @0.3,
  radius 14g, offset (0, 3g) (g = 1 for the unit, 0.4 for the drum machine).
- **Front edge:** vertical B49CA8 → 5E4652 / 141213 → 020202.
- **Rim top** (vertical): 0 FFFFFF / 3A3638 · .02 F3E9EE / 1E1C1D · .06 E2D3DB / 121112 ·
  .45 EEE3E9 / 181617 · .9 DCCBD4 / 0D0C0D · 1 C9B2BE / 080707.
- **Side banding** (horizontal): ends 4A2A3A @.3 / black @.5; white @.9L at .006; inner shade
  (4A2A3A @.16 / black @.26) at .018; white @.12L at .5; inner shade at .982; white @.85L at .994
  (L = 1 / 0.55). Then the grain.
- **Rim edges:** top highlight stroke 1.4, white @a → a×.85 at .15 → 0 by 42% (a = 1 / .75); red
  line FF8A8A @.7 along the rim's foot; outline 1 px 2A1420 @.7 / black @.9.
- **Face:** inset shadow 3A1A2A @.4 / black @.7 (radius 8, offset (0, −1)); lip white @.75 / @.2;
  gradient 0 FFFDFE / 1A1819 · .18 FAF4F7 / 121112 · .42 F1E7EC / 0A0A0A · .7 F8F1F4 / 0E0D0E ·
  1 EFE3E9 / 070707; grain; iridescence (diagonal) FFC8DC@.16 → FFE0C8@.12 → FFE0EC@.14 /
  FF6A9A@.05 → FFB07A@.025 → FF4A6A@.04; sheen streak white @.05s/.45s/.05s at .3/.38/.46
  (s = 1 / .22); vignette 8A4A66 @.16 / black @.6; bottom glow FF9AB3 to @.4 over 26 px.
- **Section panels** (radius 12): EEE3E9 → F9F3F6 / 070707 → 0F0E0F; grain; 5 inner-shadow rings
  (alpha (.11 − .019r) × (2.5 on OBSIDIAN), black or 4A2034); edge 3A2A32 @.55 / black @.85; bottom
  lip white @.9 / @.18.
- **Insets** (radius 8): 8A4A66 @.06 / black @.22; edge 2A1C24 @.5 / black @.85; catch white @.9 / @.15.
- **Radii:** chassis 28, face 16, front edge 8. Dimming (AURORA) after the pearl, before lettering.

## 2. Type

- **Inter** only (SIL OFL 1.1): `Inter-Regular` for text, `Inter-SemiBold` for bold,
  `InterDisplay-BlackItalic` for the PARAGON badge. (PR7-S also uses Bebas Neue for titles; PR7-D
  does not.)
- Sizes (px): 10.5 bold knob labels (textDim) and outlined buttons · 12 bold toggles · 12.5 bold
  panel titles (text @.9) · 13 regular body · 14.5 bold column titles · 16 bold section headings ·
  19 regular names · 20 bold numbers · 21 regular header "PARAGON".
- **Labels, headings, keys and stamped text are UPPER CASE**; body text sentence case. No tracking.
- Stamped text: drawn in stampEdge 1 px lower, then in its colour.

## 3. Widgets

- **Colour scheme:** window 060407, widget 151217, menu 050405, outline panelEdge, text `text`,
  highlighted text white, highlighted fill accentDim.
- **Button:** inset 0.5, radius 4, fill 1C1C20 (hover ≈303034, down accentDim gradient, disabled
  @.4), 1 px panelEdge outline. **When on:** a 2 px family-gradient bar (radius 1) at its foot,
  width − 12, centred in the bottom 4 px: *the gradient bar under the chosen item*.
- **Text-only button:** no box; hover white @.04, down @.08, radius 4.
- **Key (small pedal key):** neon-gradient surround (radius 5) with black @.3 → white @.25
  overlay, inner fill 1A1216 (inset 1.5, radius 4), black @.55 0.8 px outline; then a piano key
  (below). Text bold ≤12 px, `text` (white when on, textDim when disabled). No text: an LED stripe
  (60% × 4 px neon bar).
- **Piano key** (LAF:755-807): drop shadow black @.6; chamfer 57565C → 2A292E (.18) → 111113 (.7)
  → 020203; red glow in the side chamfers (glow @0 → @.75 down the sides); top face 1C1B20 →
  060607; gloss white @.13 over the top 55%; top edge white @.45; outline black @.6 0.8 px; outer
  1 px black, glow @.8 on hover. Pressed: down 1, smaller shadow.
- **Neon bezel** (footswitches, pads): shadow black @.45 (radius 10, offset 4); neon fill; light
  overlay white @.45 → @.12 (.12) → clear (.6) → black @.45; side overlay white @.35 → black @.12
  → clear → black @.12 → white @.35; stroke black @.6; well 120B0E inset 4.5.
- **Neon bar / LED:** lit = glow @.18 and @.4 halos, neon FF3A2A, core FFF2EE; off = FF3A2A @.2
  halo and CF3324.
- **Toggle = round LED** (≤12 px): on = accent gradient with an @.25 glow; off = accentDim
  gradient × 0.5; ring black (`text` on hover); label 12 bold, @.6 when off.
- **Small knob:** track arc panelEdge 3 px; value arc family gradient × 1.18, 3 px; body 3A3A40 →
  101012 with a black outline; pointer `text`, 3 px rounded. Label 10.5 bold textDim above, value
  below (white).
- **Slider:** track ≤6 px, rounded; value and thumb in the accent gradient. EQ fader: groove 050406
  4 px with a panelEdge-bright edge, lit part 3 px with a halo, piano-key cap. MIN/MAX slider: 4 px
  panelEdge track, gradient range, 14 px ring thumbs with an @.25 glow.
- **Popup menu:** fill 050405, 1 px panelEdge border; separators panelEdge inset 6; highlight =
  family gradient × 1.18, radius 3; text white (disabled @.35), inset 8; tick white 1.8 px.
- **Scroll bar:** thumb only, radius 4, accent gradient; × 1.25 on hover. (PR7-S: track 0B090C
  with a panelEdge border.)
- **Tabs:** box only when on/down: accentDim @.55 fill, accent gradient border @.8, radius 4; icon
  white when on with a gradient glow (3.5× stroke @.25), `text` on hover, @.85 otherwise. Tab group
  frame 0D0A0E, radius 5, panelEdge 1 px, panelEdge dividers.
- **Text editor:** text and caret accent F4353A; selection accentDim.
- **Tooltip:** background panel 0C0A0D, outline panelEdge, text `text`; radius 4, padding 9×5, 13 px.
- **Selected list row:** accent gradient @.22 (@.08 unchosen), radius 3, gradient border.
- **Learn / focus outline:** dashed glow, 4/3 dashes, 1.5 px, radius 4.
- **Level meter:** LED dots 6 × 3.5 px every 6 px, meterRed with a @.3 halo, unlit @.2; amber over 0 dB.

## 4. Layout

- Page background 060407 with a faint radial glow @.06. Header 64 px with a panelEdge line under it.
- **Dock panel:** vertical 0E0B0F → 09070A, radius 8, 1 px panelEdge; title 12.5 bold; padding
  24 × 18; headings 16 bold; body 13 textDim; 12 px between panels; buttons 30–32 px high with
  8–12 px gaps.
- **LED screen:** chrome frame (FAF3F6 → CBBAC3 → 8F7D87 → B7A4AE → 5E4F57, radius 11), bezel
  2B292C → 070607, glass radial 1C0B06 → 070302 with scanlines (black @.16 every 2 px) and two
  diagonal reflections; content ledOrange, upper case.

## 5. OBSIDIAN vs AURORA

Different: the pearl values (§1f: AURORA warm rose-whites, OBSIDIAN neutral near-blacks), the grain
(§1e), AURORA's 10% dimming, ink / inkDim / stampEdge / printedRed (§1d), and the strength of sheen,
banding and highlights. The same: everything in §1a-c and §2-4.
