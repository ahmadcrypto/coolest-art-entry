#!/usr/bin/env python3
"""Generate the artwork for make.fun bounty "coolest-art-01".

Original generative art, built from scratch for this entry: a ringed
copper-banded planet drifting through a teal/violet nebula, with a
starfield and a small crescent moon. Everything is procedural and
fully deterministic (fixed seed) -- no network, no copied artwork,
no trademarked characters.

Local build tool only: it needs numpy + Pillow. The submitted entry
itself is main.py, which only copies the finished art.png into
/output/entry.png with the Python standard library, so the grader
needs no third-party package at all.

Run:  python3 generate.py            (writes art.png, 896x896)
"""

import math

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

SEED = 20261113
W = H = 1024
OUT = 896  # final size: 1024 render, Lanczos-downscaled (keeps PNG < 1 MiB)


def value_noise(rng, cells):
    """Smooth value-noise field in [0, 1] over the canvas.

    A small random grid, bilinearly upsampled with Pillow.
    """
    grid = rng.random((cells + 1, cells + 1))
    img = Image.fromarray((grid * 255).astype(np.uint8))
    img = img.resize((W, H), Image.BILINEAR)
    return np.asarray(img, dtype=np.float32) / 255.0


def fbm(rng, cells_list, weights):
    """Fractal Brownian motion: weighted sum of value-noise octaves."""
    total = np.zeros((H, W), dtype=np.float32)
    wsum = 0.0
    for cells, w in zip(cells_list, weights):
        total += w * value_noise(rng, cells)
        wsum += w
    return total / wsum


def screen(base, layer):
    """Screen blend of two float RGB arrays in [0, 1]."""
    return 1.0 - (1.0 - base) * (1.0 - layer)


def main():
    rng = np.random.default_rng(SEED)

    # ------------------------------------------------------------------
    # 1. Deep-space background: dark indigo vertical gradient + violet wash
    # ------------------------------------------------------------------
    yy = np.tile(np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None], (1, W))
    xx = np.tile(np.linspace(0.0, 1.0, W, dtype=np.float32)[None, :], (H, 1))
    top = np.array([10, 12, 34], dtype=np.float32) / 255.0
    mid = np.array([18, 14, 44], dtype=np.float32) / 255.0
    bot = np.array([5, 7, 18], dtype=np.float32) / 255.0
    t = np.clip(yy * 1.6, 0, 1)
    bg = top[None, None, :] * (1 - t)[..., None] + mid[None, None, :] * t[..., None]
    t2 = np.clip((yy - 0.55) * 2.2, 0, 1)
    bg = bg * (1 - t2[..., None]) + bot[None, None, :] * t2[..., None]
    # faint violet wash, upper-left
    wash = np.exp(-(((xx - 0.30) ** 2) / 0.28 + ((yy - 0.28) ** 2) / 0.32))
    bg += wash[..., None] * np.array([0.05, 0.03, 0.10], dtype=np.float32)

    # ------------------------------------------------------------------
    # 2. Nebula: fbm clouds + ridged filaments in magenta/violet/teal/gold
    # ------------------------------------------------------------------
    clouds = fbm(rng, [4, 9, 18, 36], [0.45, 0.30, 0.17, 0.08])
    ridge = 1.0 - np.abs(2.0 * fbm(rng, [6, 12, 24], [0.5, 0.32, 0.18]) - 1.0)
    ridge = ridge * ridge
    drift = fbm(rng, [3, 7], [0.65, 0.35])  # low-freq hue selector

    neb = np.zeros((H, W, 3), dtype=np.float32)
    magenta = np.array([0.85, 0.25, 0.62], dtype=np.float32)
    violet = np.array([0.45, 0.30, 0.95], dtype=np.float32)
    teal = np.array([0.15, 0.75, 0.72], dtype=np.float32)
    gold = np.array([0.95, 0.62, 0.25], dtype=np.float32)

    m_cloud = np.clip((clouds - 0.46) * 2.0, 0, 1) ** 1.6
    m_fila = np.clip((ridge - 0.62) * 2.6, 0, 1) ** 1.8
    warm = np.clip((drift - 0.50) * 3.0, 0, 1)
    cool = np.clip((0.50 - drift) * 3.0, 0, 1)

    neb += m_cloud[..., None] * (magenta[None, None, :] * (0.35 + 0.65 * warm[..., None])
                                  + violet[None, None, :] * (0.35 + 0.65 * cool[..., None])) * 0.45
    neb += m_fila[..., None] * (teal[None, None, :] * 0.55
                                 + gold[None, None, :] * 0.35 * warm[..., None]) * 0.55
    # bright nebula heart, upper-left of centre
    heart = np.exp(-(((xx - 0.34) ** 2) / 0.045 + ((yy - 0.30) ** 2) / 0.055))
    neb += heart[..., None] * np.array([0.85, 0.55, 0.75], dtype=np.float32) * 0.45
    # soften the clouds: blur removes hard blob edges (and helps PNG size)
    neb_img = Image.fromarray((np.clip(neb, 0, 1) * 255).astype(np.uint8), "RGB")
    neb = np.asarray(neb_img.filter(ImageFilter.GaussianBlur(9)),
                     dtype=np.float32) / 255.0

    img = screen(bg, np.clip(neb, 0, 1))

    # ------------------------------------------------------------------
    # 3. Starfield (drawn on its own layer, then screened in)
    # ------------------------------------------------------------------
    stars = np.zeros((H, W, 3), dtype=np.float32)
    star_img = Image.new("RGB", (W, H), (0, 0, 0))
    draw = ImageDraw.Draw(star_img)
    n_stars = 1800
    sx = rng.random(n_stars) * W
    sy = rng.random(n_stars) * H
    # power-law brightness: mostly faint, a few brilliant
    bright = rng.random(n_stars) ** 3.2
    tint_pick = rng.random(n_stars)
    # only the 12 brightest stars get diffraction spikes
    spike_idx = set(np.argsort(bright)[-12:].tolist())
    for i, (x, y, b, tp) in enumerate(zip(sx, sy, bright, tint_pick)):
        if b < 0.04:
            continue
        v = 0.25 + 0.75 * b
        if tp < 0.55:
            col = (int(235 * v), int(240 * v), 255)
        elif tp < 0.85:
            col = (255, int(235 * v), int(200 * v))
        else:
            col = (int(200 * v), int(225 * v), 255)
        r = 1 if b < 0.70 else 2
        draw.ellipse([x - r, y - r, x + r, y + r], fill=col)
        if i in spike_idx:  # short, subtle spikes on the very brightest
            L = 6 + 8 * b
            draw.line([x - L, y, x + L, y], fill=col, width=1)
            draw.line([x, y - L, x, y + L], fill=col, width=1)
    stars = np.asarray(star_img, dtype=np.float32) / 255.0
    glow = star_img.filter(ImageFilter.GaussianBlur(2.2))
    stars = np.clip(stars + np.asarray(glow, dtype=np.float32) / 255.0 * 0.5, 0, 1)
    img = screen(img, stars * 0.9)

    # ------------------------------------------------------------------
    # 4. Ringed planet, lower-right. Copper/rose bands, lit from top-left.
    # ------------------------------------------------------------------
    cx, cy, R = 700.0, 660.0, 215.0
    # rings first (behind the planet), then the planet, then the rings' front half
    ring_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring_img)
    tilt = math.radians(-16)
    # ring annulus in planet-centred, tilted coordinates
    Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
    dx = X - cx
    dy = Y - cy
    ct, st = math.cos(tilt), math.sin(tilt)
    rx = dx * ct - dy * st
    ry = dx * st + dy * ct
    ry_s = ry / 0.34  # squash: ring plane seen nearly edge-on
    rr = np.sqrt(rx * rx + ry_s * ry_s) / R
    ring_mask = (rr > 1.22) & (rr < 2.15)
    # banding + Cassini division
    band = 0.55 + 0.45 * np.sin(rr * 34.0)
    cassini = np.clip((np.abs(rr - 1.62) - 0.045) / 0.05, 0, 1)
    ring_alpha = np.where(ring_mask, band * cassini * 0.85, 0.0).astype(np.float32)
    # planet shadow falls on the rings to the lower-right (light is top-left)
    shadow = np.clip(((rx / R) * 0.7 + (ry_s / R) * 0.7 + 0.55), 0, 1)
    ring_alpha = ring_alpha * (0.35 + 0.65 * shadow)
    ring_col = np.array([0.93, 0.78, 0.55], dtype=np.float32)
    front = ry > 0  # near side of the ring plane: drawn over the planet
    behind = ring_mask & (~front)
    img = img * (1 - np.where(behind, ring_alpha, 0)[..., None]) + \
        ring_col[None, None, :] * np.where(behind, ring_alpha, 0)[..., None]

    # planet disc
    px = (X - cx) / R
    py = (Y - cy) / R
    pr2 = px * px + py * py
    disc = pr2 <= 1.0
    nz = np.sqrt(np.clip(1.0 - pr2, 0, 1))
    # light direction: from upper-left, slightly toward viewer
    lx, ly, lz = -0.55, -0.55, 0.62
    diffuse = np.clip(px * lx + py * ly + nz * lz, 0, 1)
    # latitude bands, gently warped by the nebula noise
    warp = (clouds - 0.5) * 0.10
    lat = py + warp
    band_phase = np.sin(lat * 9.0 + 0.7 * np.sin(lat * 23.0))
    copper = np.array([0.78, 0.42, 0.26], dtype=np.float32)
    rose = np.array([0.85, 0.55, 0.48], dtype=np.float32)
    cream = np.array([0.93, 0.82, 0.66], dtype=np.float32)
    slate = np.array([0.45, 0.42, 0.55], dtype=np.float32)
    w_band = 0.5 + 0.5 * band_phase
    planet_col = (copper[None, None, :] * (1 - w_band[..., None])
                  + cream[None, None, :] * w_band[..., None] * 0.6
                  + rose[None, None, :] * (w_band[..., None] * 0.4))
    # polar caps: blend toward slate gradually, only near the poles
    pole_w = np.clip((np.abs(lat) - 0.62) / 0.25, 0, 1)[..., None]
    planet_col = planet_col * (1 - pole_w * 0.7) + slate[None, None, :] * (pole_w * 0.7)
    lit = 0.12 + 0.88 * (diffuse ** 1.15)[..., None]
    # terminator softness: a gentle dusk band
    dusk = np.clip((diffuse - 0.02) * 8.0, 0, 1)[..., None]
    planet_px = planet_col * lit * (0.25 + 0.75 * dusk)
    # thin bright atmosphere rim on the lit limb
    rim = np.clip((pr2 - 0.90) / 0.10, 0, 1) * np.clip(diffuse, 0, 1)
    planet_px = planet_px + rim[..., None] * np.array([0.55, 0.75, 0.95], dtype=np.float32) * 0.55
    img = np.where(disc[..., None], planet_px, img)

    # front half of the rings, over the planet's lower edge
    front_mask = ring_mask & front
    img = img * (1 - np.where(front_mask, ring_alpha, 0)[..., None]) + \
        ring_col[None, None, :] * np.where(front_mask, ring_alpha, 0)[..., None]

    # planet's soft outer glow (drawn as a blurred disc, screened in)
    glow_layer = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    gd.ellipse([cx - R * 1.28, cy - R * 1.28, cx + R * 1.28, cy + R * 1.28],
               fill=(70, 45, 60))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(26))
    img = screen(img, np.asarray(glow_layer, dtype=np.float32) / 255.0 * 0.55)

    # ------------------------------------------------------------------
    # 5. Small crescent moon, upper-left
    # ------------------------------------------------------------------
    mx, my, mr = 208.0, 205.0, 34.0
    mdx = (X - mx) / mr
    mdy = (Y - my) / mr
    mr2 = mdx * mdx + mdy * mdy
    moon = mr2 <= 1.0
    # cut the crescent: offset disc in shadow
    shx = (X - (mx + 16)) / mr
    shy = (Y - (my - 8)) / mr
    shadow_disc = (shx * shx + shy * shy) <= 1.0
    lit_moon = moon & (~shadow_disc)
    mdiff = np.clip(-mdx * 0.6 - mdy * 0.6 + 0.55, 0.15, 1.0)
    moon_col = np.array([0.92, 0.90, 0.82], dtype=np.float32) * mdiff[..., None]
    img = np.where(lit_moon[..., None], moon_col, img)

    # ------------------------------------------------------------------
    # 6. Vignette + grain, then save
    # ------------------------------------------------------------------
    vig = 1.0 - 0.16 * np.clip((pr2 * 0 + ((X - W / 2) / (W / 2)) ** 2
                                + ((Y - H / 2) / (H / 2)) ** 2) / 2.0 - 0.55, 0, 1) ** 1.5
    img = img * vig[..., None]
    grain = rng.normal(0, 1, (H, W, 1)).astype(np.float32) * (1.2 / 255.0)
    img = np.clip(img + grain, 0, 1)

    out = Image.fromarray((img * 255).astype(np.uint8), "RGB")
    out = ImageEnhance.Contrast(out).enhance(1.06)
    out = ImageEnhance.Color(out).enhance(1.08)
    out = out.resize((OUT, OUT), Image.LANCZOS)  # 896x896, PNG stays < 1 MiB
    out.save("art.png", optimize=True)
    print("wrote art.png", out.size)


if __name__ == "__main__":
    main()
