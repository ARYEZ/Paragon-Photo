//! Paragon Photo: the Paragon family's finishes (OBSIDIAN, AURORA) painted into craft's surfaces.
//!
//! The Paragon PR7 plugins draw their lit accent as a pink → red → orange gradient wherever a fill
//! *is* the family red (`ParagonLookAndFeel::setFill`), and their controls as black piano keys. The
//! same rule is applied here, keyed on the exact colours Paragon Photo's themes pin
//! (`crates/ui-egui/src/themes/paragon-*.json`; values in `docs/paragon-finish-spec.md`). No other
//! theme uses these colours, so every other theme paints exactly as craft does.
//!
//! | Fill | Painted as |
//! |---|---|
//! | accent `#F4353A` | the family gradient × 1.18 |
//! | accent dim `#4E1016` (on / pressed) | the family gradient × 0.42, and on a control the 2 px gradient bar at its foot |
//! | selected `#411418` | the family gradient × 1.18 at 22% (the PR7 selected list row) |
//! | raised `#1C1C20`, hover `#303034` (a control) | a piano key: dark face gradient, gloss, red glow edge on hover |
//! | strong `#DE0639` (primary buttons, both finishes) | the family gradient × 1.18 |
//! | AURORA selected / on `#E4B6B9` | the family gradient × 1.18 at 22% over the pearl; on a control, the gradient bar too |
//! | AURORA pressed `#C8BFC3` | the family gradient × 1.18 at 30% |
//! | knob `#1A1216` (both finishes) | a black knob in a neon ring (the PR7 keys' and knobs' rings) |
//! | OBSIDIAN outlined button: clear fill, `#8A8A92` edge | a black piano key, as a raised one |
//! | AURORA pearl surfaces | the satin grain over them, when the app registered its texture |
//!
//! Everything is a mesh built from [`super::kit::fill_polygon`] and recoloured per vertex, so edges
//! keep their anti-aliasing and no texture (per egui context) is needed.

use egui::epaint::{CornerRadius, Mesh, RectShape};
use egui::{Color32, Pos2, Rect, Shape, Stroke, StrokeKind, TextureId, pos2};
use std::sync::RwLock;

/// The family red, lit (`ParagonColours::accent`).
const ACCENT: [u8; 3] = [0xF4, 0x35, 0x3A];
/// The family red, dim (`ParagonColours::accentDim`): OBSIDIAN's pressed and on fill.
const ACCENT_DIM: [u8; 3] = [0x4E, 0x10, 0x16];
/// OBSIDIAN's selected row: the accent at 22% over the panel.
const SELECTED: [u8; 3] = [0x41, 0x14, 0x18];
/// OBSIDIAN's raised control (`drawButtonBackground`'s 1C1C20) and its hover.
const KEY_REST: [u8; 3] = [0x1C, 0x1C, 0x20];
const KEY_HOVER: [u8; 3] = [0x30, 0x30, 0x34];
/// The strong accent (primary buttons) both finishes pin: the family pink.
const STRONG: [u8; 3] = [0xDE, 0x06, 0x39];
/// AURORA's selected row and on control (the accent at 22% over its pearl panel), and its pressed fill.
const AURORA_SELECTED: [u8; 3] = [0xE4, 0xB6, 0xB9];
const AURORA_PRESSED: [u8; 3] = [0xC8, 0xBF, 0xC3];
/// The knob both finishes pin (`surface.knob`): the PR7 key surround's inner fill.
const KNOB: [u8; 3] = [0x1A, 0x12, 0x16];
/// OBSIDIAN's outlined (secondary) button edge at rest: its muted text colour, which it uses for no border.
const OUTLINE_EDGE: [u8; 3] = [0x8A, 0x8A, 0x92];
/// AURORA's pearl surfaces (panel, raised, background, chrome, sunken), dimmed 10% as the finish draws them.
const AURORA_PEARL: [[u8; 3]; 5] = [[0xE0, 0xDB, 0xDD], [0xE1, 0xDC, 0xDE], [0xD9, 0xD0, 0xD4], [0xD6, 0xCC, 0xD2], [0xE6, 0xE4, 0xE5]];
/// The satin grain tile's side, in points: the texture repeats every this many points.
const GRAIN_TILE: f32 = 128.0;

/// The satin grain texture the app registered ([`set_grain_texture`]), tiled over AURORA's pearl.
static GRAIN: RwLock<Option<TextureId>> = RwLock::new(None);

/// Registers the satin grain the pearl surfaces show (a repeating texture, alpha only over white), or
/// `None` for none. The app makes the texture once per context (`theme::install_runtime`).
pub fn set_grain_texture(texture: Option<TextureId>) {
    *GRAIN.write().unwrap_or_else(std::sync::PoisonError::into_inner) = texture;
}

fn grain() -> Option<TextureId> {
    *GRAIN.read().unwrap_or_else(std::sync::PoisonError::into_inner)
}

/// The red-orange edge light (`ParagonColours::glow`).
const GLOW: Color32 = Color32::from_rgb(0xFF, 0x4A, 0x3A);

/// `ParagonLookAndFeel::litBrightness` / `dimBrightness`.
const LIT: f32 = 1.18;
const DIM: f32 = 0.42;

/// Controls are at most this tall; a taller surface (a panel, a popup) keeps a flat fill.
const CONTROL_MAX_HEIGHT: f32 = 48.0;

/// The family gradient's stops (`familyGradient`): pink, a deeper pink, red, a burnt orange, orange.
const STOPS: [(f32, [u8; 3]); 5] = [
    (0.0, [0xDE, 0x06, 0x39]),
    (0.25, [0xD9, 0x07, 0x38]),
    (0.5, [0xD4, 0x2E, 0x2A]),
    (0.75, [0xCF, 0x5C, 0x1C]),
    (1.0, [0xCD, 0x66, 0x19]),
];

/// The family gradient at `t` (0 at the left, 1 at the right) times `brightness`, clamped.
fn family(t: f32, brightness: f32) -> [f32; 3] {
    let t = t.clamp(0.0, 1.0);
    let mut out = STOPS[STOPS.len() - 1].1.map(f32::from);
    for pair in STOPS.windows(2) {
        let ((a, ca), (b, cb)) = (pair[0], pair[1]);
        if t <= b {
            let u = if b > a { (t - a) / (b - a) } else { 0.0 };
            out = [0, 1, 2].map(|i| f32::from(ca[i]) + (f32::from(cb[i]) - f32::from(ca[i])) * u);
            break;
        }
    }
    out.map(|c| (c * brightness).min(255.0))
}

fn rgb_of(c: Color32) -> Option<[u8; 3]> {
    let [r, g, b, a] = c.to_srgba_unmultiplied();
    (a > 0).then_some([r, g, b])
}

fn opacity_of(c: Color32) -> f32 {
    f32::from(c.a()) / 255.0
}

/// The outline of `rect` with corners `radius`, clockwise from the top left, as a polygon.
fn rounded_rect(rect: Rect, radius: CornerRadius) -> Vec<Pos2> {
    let max_r = rect.width().min(rect.height()) / 2.0;
    let corner = |r: u8| f32::from(r).min(max_r);
    let mut points = Vec::with_capacity(40);
    let mut arc = |center: Pos2, r: f32, start_deg: f32| {
        if r <= 0.0 {
            // A square corner: the corner point itself.
            let a = (start_deg + 45.0).to_radians();
            points.push(center + egui::vec2(a.cos(), a.sin()) * 0.0);
            return;
        }
        let steps = ((r / 2.0).ceil() as usize).clamp(2, 12);
        for s in 0..=steps {
            let a = (start_deg + 90.0 * s as f32 / steps as f32).to_radians();
            points.push(center + egui::vec2(a.cos(), a.sin()) * r);
        }
    };
    let (nw, ne, se, sw) = (corner(radius.nw), corner(radius.ne), corner(radius.se), corner(radius.sw));
    arc(pos2(rect.left() + nw, rect.top() + nw), nw, 180.0);
    arc(pos2(rect.right() - ne, rect.top() + ne), ne, 270.0);
    arc(pos2(rect.right() - se, rect.bottom() - se), se, 0.0);
    arc(pos2(rect.left() + sw, rect.bottom() - sw), sw, 90.0);
    points
}

/// The anti-aliased fill of `points`, each vertex coloured by `color(position)` at its own coverage.
fn shaded(points: &[Pos2], feather: f32, color: impl Fn(Pos2) -> [f32; 4]) -> Mesh {
    let mut mesh = super::kit::fill_polygon(points, Color32::WHITE, feather);
    for v in &mut mesh.vertices {
        // White at full coverage is (255, 255, 255, 255); the feathered edge is white times its coverage.
        let coverage = f32::from(v.color.a()) / 255.0;
        let [r, g, b, a] = color(v.pos);
        let alpha = (a * coverage).clamp(0.0, 1.0);
        let px = |c: f32| (c * alpha).round().clamp(0.0, 255.0) as u8;
        v.color = Color32::from_rgba_premultiplied(px(r), px(g), px(b), (alpha * 255.0).round() as u8);
    }
    mesh
}

/// `rect` in the family gradient at `brightness`, left to right, at `opacity`.
fn gradient(rect: Rect, radius: CornerRadius, brightness: f32, opacity: f32, feather: f32) -> Shape {
    let width = rect.width().max(1.0);
    Shape::mesh(shaded(&rounded_rect(rect, radius), feather, |p| {
        let [r, g, b] = family((p.x - rect.left()) / width, brightness);
        [r, g, b, opacity]
    }))
}

/// `rect` from `top` to `bottom`, vertically, at `opacity`.
fn vertical(rect: Rect, radius: CornerRadius, top: [u8; 3], bottom: [u8; 3], opacity: f32, feather: f32) -> Shape {
    let height = rect.height().max(1.0);
    Shape::mesh(shaded(&rounded_rect(rect, radius), feather, |p| {
        let t = ((p.y - rect.top()) / height).clamp(0.0, 1.0);
        let c = |i: usize| f32::from(top[i]) + (f32::from(bottom[i]) - f32::from(top[i])) * t;
        [c(0), c(1), c(2), opacity]
    }))
}

/// The 2 px family-gradient bar at the foot of a chosen control (the PR7 "on" button's bar): its width
/// less 12, centred in the bottom 4 px.
fn on_bar(rect: Rect, feather: f32) -> Option<Shape> {
    (rect.width() >= 24.0 && rect.height() >= 12.0).then(|| {
        let bar = Rect::from_min_max(pos2(rect.left() + 6.0, rect.bottom() - 3.0), pos2(rect.right() - 6.0, rect.bottom() - 1.0));
        gradient(bar, CornerRadius::same(1), LIT, 1.0, feather)
    })
}

/// A black piano key over `rect` (`drawPianoKey`'s top face, gloss and edge): a dark face from
/// 1C1B20 to 060607, a white gloss over its top 55%, and on hover a red glow edge.
fn piano_key(rect: Rect, radius: CornerRadius, hover: bool, opacity: f32, feather: f32) -> Vec<Shape> {
    let (top, bottom) = if hover { ([0x2A, 0x29, 0x30], [0x0E, 0x0E, 0x10]) } else { ([0x1C, 0x1B, 0x20], [0x06, 0x06, 0x07]) };
    let mut out = vec![vertical(rect, radius, top, bottom, opacity, feather)];
    let gloss = Rect::from_min_max(rect.min, pos2(rect.right(), rect.top() + rect.height() * 0.55)).shrink2(egui::vec2(rect.width() * 0.03, 1.0));
    if gloss.height() > 1.0 && gloss.width() > 1.0 {
        let h = gloss.height();
        let gloss_radius = CornerRadius { nw: radius.nw, ne: radius.ne, sw: 0, se: 0 };
        out.push(Shape::mesh(shaded(&rounded_rect(gloss, gloss_radius), feather, |p| {
            let t = ((p.y - gloss.top()) / h).clamp(0.0, 1.0);
            [255.0, 255.0, 255.0, 0.13 * (1.0 - t) * opacity]
        })));
    }
    if hover {
        out.push(Shape::Rect(RectShape::stroke(rect, radius, Stroke::new(1.0, GLOW.gamma_multiply(0.8 * opacity)), StrokeKind::Inside)));
    }
    out
}

/// The neon of the PR7 rings at `t` across the ring: the family gradient at 75% (`Finish::neonGradient`),
/// each stop `brighter(0.35)` as the knob rings draw it.
fn neon(t: f32) -> [f32; 3] {
    family(t, 0.75).map(|c| 255.0 - (255.0 - c) / 1.35)
}

/// A knob over `rect`: a faint neon glow round it, a neon ring and a black body inside it (the PR7 knobs and
/// keys, black in neon rings on both finishes).
fn knob(rect: Rect, radius: CornerRadius, opacity: f32, feather: f32) -> Vec<Shape> {
    let side = rect.width().min(rect.height());
    let ring = (side * 0.16).clamp(1.5, 3.0);
    let width = rect.width().max(1.0);
    let neon_at = |p: Pos2, alpha: f32| {
        let [r, g, b] = neon((p.x - rect.left()) / width);
        [r, g, b, alpha]
    };
    let grow = |r: CornerRadius, by: f32| {
        let f = |c: u8| (f32::from(c) + by).clamp(0.0, 255.0) as u8;
        CornerRadius { nw: f(r.nw), ne: f(r.ne), sw: f(r.sw), se: f(r.se) }
    };
    let glow = rect.expand(ring * 0.8);
    let body = rect.shrink(ring);
    vec![
        Shape::mesh(shaded(&rounded_rect(glow, grow(radius, ring * 0.8)), feather * 2.0, |p| neon_at(p, 0.3 * opacity))),
        Shape::mesh(shaded(&rounded_rect(rect, radius), feather, |p| neon_at(p, opacity))),
        vertical(body, grow(radius, -ring), [0x2A, 0x29, 0x30], [0x08, 0x08, 0x0A], opacity, feather),
    ]
}

/// The Paragon painting of a whole surface (fill and edge): `None` when it is none of the finishes' keyed
/// surfaces. `edge` is its border colour, if it has a plain border. The edge is the caller's to draw only when
/// the result says so (`true`): a key or a knob draws its own.
pub(crate) fn surface(rect: Rect, radius: CornerRadius, fill: Color32, edge: Option<Color32>, feather: f32) -> Option<(Vec<Shape>, bool)> {
    let control = rect.height() <= CONTROL_MAX_HEIGHT;
    let rgb = rgb_of(fill);
    if rgb == Some(KNOB) && rect.width().max(rect.height()) <= CONTROL_MAX_HEIGHT {
        return Some((knob(rect, radius, opacity_of(fill), feather), false));
    }
    // An outlined button at rest: a clear fill inside OBSIDIAN's muted edge.
    if control && rgb.is_none() && edge.and_then(rgb_of) == Some(OUTLINE_EDGE) {
        return Some((piano_key(rect, radius, false, 1.0, feather), false));
    }
    if control && (rgb == Some(KEY_REST) || rgb == Some(KEY_HOVER)) {
        return Some((piano_key(rect, radius, rgb == Some(KEY_HOVER), opacity_of(fill), feather), false));
    }
    if let Some(shapes) = fill_shapes(rect, radius, fill, feather) {
        return Some((shapes, true));
    }
    // AURORA's pearl: its flat fill, then the satin grain over it.
    if let (Some(c), Some(texture)) = (rgb, grain())
        && AURORA_PEARL.contains(&c)
    {
        let uv = Rect::from_min_size(pos2(0.0, 0.0), egui::vec2(rect.width() / GRAIN_TILE, rect.height() / GRAIN_TILE));
        return Some((
            vec![
                Shape::Rect(RectShape::filled(rect, radius, fill)),
                Shape::Rect(RectShape::filled(rect, radius, Color32::WHITE).with_texture(texture, uv)),
            ],
            true,
        ));
    }
    None
}

/// The Paragon painting of a fill of `color` over `rect`, or `None` when `color` is not one of the
/// finishes' keyed colours (paint it as craft does).
pub(crate) fn fill(rect: Rect, radius: CornerRadius, color: Color32, feather: f32) -> Option<Vec<Shape>> {
    if rgb_of(color) == Some(KNOB) && rect.width().max(rect.height()) <= CONTROL_MAX_HEIGHT {
        return Some(knob(rect, radius, opacity_of(color), feather));
    }
    fill_shapes(rect, radius, color, feather)
}

/// [`fill`] for the gradients and keys (everything but the knob).
fn fill_shapes(rect: Rect, radius: CornerRadius, color: Color32, feather: f32) -> Option<Vec<Shape>> {
    let rgb = rgb_of(color)?;
    let opacity = opacity_of(color);
    let control = rect.height() <= CONTROL_MAX_HEIGHT;
    // A list row is much wider than tall; a tool button or a key is not.
    let compact_control = control && rect.width() < rect.height() * 4.0;
    if rgb == ACCENT || rgb == STRONG {
        Some(vec![gradient(rect, radius, LIT, opacity, feather)])
    } else if rgb == ACCENT_DIM {
        let mut out = vec![gradient(rect, radius, DIM, opacity, feather)];
        if control {
            out.extend(on_bar(rect, feather));
        }
        Some(out)
    } else if rgb == SELECTED {
        Some(vec![gradient(rect, radius, LIT, 0.22 * opacity, feather)])
    } else if rgb == AURORA_SELECTED {
        // The pearl shows through, as PR7-D's row gradient at 22% over the panel.
        let mut out = vec![gradient(rect, radius, LIT, 0.22 * opacity, feather)];
        if compact_control {
            out.extend(on_bar(rect, feather));
        }
        Some(out)
    } else if rgb == AURORA_PRESSED {
        Some(vec![gradient(rect, radius, LIT, 0.30 * opacity, feather)])
    } else if control && (rgb == KEY_REST || rgb == KEY_HOVER) {
        Some(piano_key(rect, radius, rgb == KEY_HOVER, opacity, feather))
    } else {
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_family_gradient_runs_pink_to_orange_and_brightens_clamped() {
        assert_eq!(family(0.0, 1.0), [222.0, 6.0, 57.0]);
        assert_eq!(family(1.0, 1.0), [205.0, 102.0, 25.0]);
        assert_eq!(family(0.5, 1.0), [212.0, 46.0, 42.0]);
        // Lit: pink's red channel clamps at 255.
        assert_eq!(family(0.0, LIT)[0], 255.0);
    }

    #[test]
    fn only_the_keyed_colours_change_how_a_fill_paints() {
        let rect = Rect::from_min_size(pos2(0.0, 0.0), egui::vec2(80.0, 24.0));
        let r = CornerRadius::same(4);
        assert!(fill(rect, r, Color32::from_rgb(0xF4, 0x35, 0x3A), 1.0).is_some());
        assert!(fill(rect, r, Color32::from_rgb(0x4E, 0x10, 0x16), 1.0).is_some_and(|s| s.len() == 2), "dim fill and its bar");
        assert!(fill(rect, r, Color32::from_rgb(0x1C, 0x1C, 0x20), 1.0).is_some());
        // Another theme's accent, a panel, a clear fill: as craft paints them.
        assert!(fill(rect, r, Color32::from_rgb(0x37, 0x8E, 0xF0), 1.0).is_none());
        assert!(fill(rect, r, Color32::TRANSPARENT, 1.0).is_none());
        // AURORA: a selected row is a translucent gradient; a selected tool gets the bar as well.
        let row = Rect::from_min_size(pos2(0.0, 0.0), egui::vec2(300.0, 28.0));
        let tool = Rect::from_min_size(pos2(0.0, 0.0), egui::vec2(36.0, 32.0));
        let aurora = Color32::from_rgb(0xE4, 0xB6, 0xB9);
        assert!(fill(row, r, aurora, 1.0).is_some_and(|s| s.len() == 1));
        assert!(fill(tool, r, aurora, 1.0).is_some_and(|s| s.len() == 2));
        assert!(fill(rect, r, Color32::from_rgb(0xDE, 0x06, 0x39), 1.0).is_some(), "primary buttons");
        // A knob: glow, neon ring, black body.
        let knob_rect = Rect::from_min_size(pos2(0.0, 0.0), egui::vec2(14.0, 14.0));
        assert!(fill(knob_rect, CornerRadius::same(7), Color32::from_rgb(0x1A, 0x12, 0x16), 1.0).is_some_and(|s| s.len() == 3));
        // OBSIDIAN's outlined button is a key; the same clear fill with another edge (AURORA's) is not.
        let edge = |c: [u8; 3]| Some(Color32::from_rgb(c[0], c[1], c[2]));
        assert!(surface(rect, r, Color32::TRANSPARENT, edge([0x8A, 0x8A, 0x92]), 1.0).is_some_and(|(_, edge)| !edge));
        assert!(surface(rect, r, Color32::TRANSPARENT, edge([0x6B, 0x65, 0x69]), 1.0).is_none());
        // A raised panel (taller than a control) keeps its flat fill.
        let panel = Rect::from_min_size(pos2(0.0, 0.0), egui::vec2(300.0, 200.0));
        assert!(fill(panel, r, Color32::from_rgb(0x1C, 0x1C, 0x20), 1.0).is_none());
    }

    #[test]
    fn a_gradient_fill_is_a_feathered_mesh_inside_its_rect() {
        let rect = Rect::from_min_size(pos2(10.0, 10.0), egui::vec2(100.0, 20.0));
        let Shape::Mesh(mesh) = gradient(rect, CornerRadius::same(4), LIT, 1.0, 1.0) else { panic!("a mesh") };
        assert!(!mesh.vertices.is_empty());
        assert!(mesh.vertices.iter().all(|v| rect.expand(1.0).contains(v.pos)));
        // Opaque inside, clear at the feathered rim.
        assert!(mesh.vertices.iter().any(|v| v.color.a() == 255));
        assert!(mesh.vertices.iter().any(|v| v.color.a() == 0));
    }
}
