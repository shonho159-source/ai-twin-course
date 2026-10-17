"""Rebuild the purple echo of logo-1.png from the exact lime letters.

The lime type is unmixed pixel by pixel (lime / lilac / background), so the font stays
exactly as generated; only the lilac echo is replaced by one drawn from the real "כפול" shape.
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

SRC, OUT = sys.argv[1], sys.argv[2]   # python3 tools/logo/echo.py assets/logo/logo-1.png assets/logo
BG = np.array([12, 8, 39], float)
LIME = np.array([205, 251, 81], float)
LILAC = np.array([169, 155, 255], float)   # brand lilac #A99BFF

a = np.asarray(Image.open(SRC).convert('RGB')).astype(float)
H, W, _ = a.shape

# unmix: pixel = bg + al*(lime-bg) + av*(lilac_src-bg), least squares per pixel
M = np.stack([LIME - BG, np.array([154, 139, 245], float) - BG], 1)       # 3x2
with np.errstate(all='ignore'):
    coef = (a.reshape(-1, 3) - BG) @ np.linalg.pinv(M).T
al = np.clip(coef[:, 0], 0, 1).reshape(H, W)
al[~np.isfinite(al)] = 0
core = al > .5                                     # solid lime only; drops the faint residue of the old echo
al = al * (ndi.distance_transform_edt(~core) <= 3)

rows = np.where((al > .5).any(1))[0]
split = 960                                        # gap between the two lines (938..980)
K = al.copy(); K[:split] = 0                       # "כפול" only


def shift(m, dx, dy):
    return ndi.shift(m, (dy, dx), order=1, mode='constant')


def grow(m, r):
    """Soft dilation by r px (distance transform keeps the edge antialiased)."""
    d = ndi.distance_transform_edt(m < .5)
    return np.clip(r + .5 - d, 0, 1)


def stroke(m, w):
    inside = ndi.distance_transform_edt(m >= .5)
    outside = ndi.distance_transform_edt(m < .5)
    sd = np.where(m >= .5, -inside, outside)        # signed distance to the edge
    return np.clip(w / 2 + .5 - np.abs(sd), 0, 1)


def stripes(period, line, y0=0):
    y = np.arange(H)[:, None]
    return (((y - y0) % period) < line).astype(float) * np.ones((1, W))


def compose(echo, name, gap=14):
    echo = echo * (1 - grow(al, gap))               # dark gap around the lime letters
    img = BG + echo[..., None] * (LILAC - BG)
    img = img * (1 - al[..., None]) + LIME * al[..., None]
    # re-center the whole mark on the square
    ink = (al > .1) | (echo > .1)
    ys, xs = np.where(ink)
    cy, cx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2
    img = np.stack([ndi.shift(img[..., c], (H / 2 - cy, W / 2 - cx), order=1, mode='constant', cval=BG[c]) for c in range(3)], -1)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(f'{OUT}/{name}.png', optimize=True)
    print(name, 'ok')


DX, DY = -66, 150                                  # same direction and distance as the original echo
E = shift(K, DX, DY)
# v1: the original striped echo, drawn from the real letters with even lines
compose(E * stripes(16, 9), 'logo-1-v1')
# v2: solid lilac double, closer
compose(shift(K, -52, 64), 'logo-1-v2', gap=12)
# v3: a true reflection under the baseline, striped and fading out
ys = np.where((K > .5).any(1))[0]
base = ys.max()
gap_y = 26
R = np.roll(K[::-1], 2 * base + gap_y - H + 1, axis=0)  # mirror around the baseline
R[:base + gap_y] = 0
t = np.clip((np.arange(H)[:, None] - base - gap_y) / 230, 0, 1)
compose(R * stripes(14, 8) * (1 - t) ** 1.3, 'logo-1-v3', gap=0)
