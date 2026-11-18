# Vendored craft-libs (Paragon Photo)

Paragon Photo paints the Paragon family's finishes (OBSIDIAN, AURORA) into craft's widgets. craft
draws its buttons, toggles, tabs, sliders and surfaces in `craft-ui-contract`, which a theme file
can only recolour, so that one crate is vendored here with Paragon Photo's changes. Every other
craft crate still comes from git.

- **Upstream:** https://github.com/storytold/craft-libs (MIT OR Apache-2.0; `LICENSE-MIT`,
  `LICENSE-APACHE` here).
- **Revision:** `a6b9d9c986f7c4c399632d72d9a4a8c8ea0b86e9`, the revision the root `Cargo.toml`
  pins for every craft crate. The vendored crate must stay on the same revision as the rest.
- **What's here:** `crates/ui-contract` (patched), and a trimmed copy of craft-libs' workspace
  `Cargo.toml` (it lists only that crate and takes every other craft crate from git at the
  revision above). The root `Cargo.toml` swaps it in with
  `[patch."https://github.com/storytold/craft-libs"]` and excludes `vendor` from the workspace.
- **Paragon Photo's changes:** `paragon.patch`, the diff from the pristine crate. In short:
  - `src/primitives/paragon.rs` (new): fills of the finishes' exact colours paint as the family
    gradient, the dim gradient with the "on" bar, the selected-row gradient, primary buttons in
    the gradient, AURORA's selected and on fills as the gradient over the pearl, and (OBSIDIAN)
    black piano keys with a red glow on hover (raised and outlined buttons), knobs as black bodies in
    neon rings, and AURORA's pearl with the satin grain the app registers
    (`primitives::paragon::set_grain_texture`, now a public module). No other theme uses those colours.
  - `src/primitives/surface.rs`, `src/primitives/draw.rs`, `src/primitives/state_layer.rs`: call it for
    surface, rect and state-layer (hover, pressed, selected, on) fills.
  - `src/fonts/stack/install.rs`, `src/fonts/stack.rs`, `src/fonts/mod.rs`, `src/style/tokens.rs`:
    Title and Heading text in the app's `display` family (Bebas Neue) at 1.3×, when it has one.
  - `Cargo.toml`: `craft-font-catalog` from git (it was a sibling path).

## Updating to a new craft-libs revision

When upstream PhotoCraft moves its craft-libs pin (after `git merge upstream/main`, the root
`Cargo.toml` names a new `rev`):

1. Put the new revision's `crates/ui-contract` here in place of the old one. Cargo fetches it to
   `~/.cargo/git/checkouts/craft-libs-*/<short rev>/` once the root `Cargo.toml` names it
   (`cargo fetch`), or clone craft-libs at that revision.
2. Apply Paragon Photo's changes: `git apply --directory=vendor/craft-libs vendor/craft-libs/paragon.patch`
   from the repository root (fix by hand any hunk that no longer applies).
3. Replace every `rev = "…"` in `vendor/craft-libs/Cargo.toml` with the new revision, and copy any
   new `[workspace.dependencies]` entries from upstream's `Cargo.toml` (as `git` + `rev` entries).
4. Build, then regenerate `paragon.patch` by diffing against the pristine crate.

Unit tests for the painting are in `src/primitives/paragon.rs`. They run in a checkout of
craft-libs (Cargo won't test a `[patch]`ed crate from Paragon Photo's workspace); the screenshots in
the session that added this are the visual check.
