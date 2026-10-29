"""Editorial comps in Manasi's reference aesthetic: real raw places, daylight, rugs as art objects out of context."""
import os, sys, numpy as np, cv2
from PIL import Image, ImageFilter
D = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(D, 'refs'); os.makedirs(OUT, exist_ok=True)
W, H = 1600, 2000
rng = np.random.default_rng(11)

def bg(n): return np.array(Image.open(os.path.join(D, 'bg', n + '.png')).convert('RGB')).astype(np.float32)

def piece(name, width=None, height=None, rot=0.0):
    im = Image.open(os.path.join(D, 'cut', name + '.png')).convert('RGBA')
    s = (width / im.width) if width else (height / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    rgb = im.convert('RGB').filter(ImageFilter.UnsharpMask(radius=1.2, percent=45, threshold=2)); rgb.putalpha(im.getchannel('A'))
    if rot: rgb = rgb.rotate(rot, resample=Image.BICUBIC, expand=True)
    a = np.array(rgb).astype(np.float32)
    return a[..., :3], a[..., 3] / 255.0

def grade(rgb, sat=1.0, mul=(1, 1, 1), bright=1.0):
    g = rgb.mean(-1, keepdims=True)
    return np.clip((g + (rgb - g) * sat) * np.array(mul, np.float32) * bright, 0, 255)

def place(canvas, rgb, a, x, y):
    """Alpha-composite (rgb, a) with its top-left at (x, y); returns the full-canvas alpha used."""
    h, w = a.shape; A = np.zeros(canvas.shape[:2], np.float32); C = np.zeros_like(canvas)
    x0, y0, x1, y1 = max(0, x), max(0, y), min(canvas.shape[1], x + w), min(canvas.shape[0], y + h)
    A[y0:y1, x0:x1] = a[y0 - y:y1 - y, x0 - x:x1 - x]; C[y0:y1, x0:x1] = rgb[y0 - y:y1 - y, x0 - x:x1 - x]
    canvas[:] = canvas * (1 - A[..., None]) + C * A[..., None]
    return A

def shadow(canvas, A, dx, dy, blur, op, tone=(20, 18, 16)):
    M = np.roll(np.roll(A, dy, 0), dx, 1); M = cv2.GaussianBlur(M, (0, 0), blur) * op
    canvas[:] = canvas * (1 - M[..., None]) + np.array(tone, np.float32) * M[..., None]

def finish(img, name, grain=2.0):
    img = img + rng.normal(0, grain, (img.shape[0], img.shape[1], 1)).astype(np.float32)
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    out.save(os.path.join(OUT, name + '.jpg'), quality=91, optimize=True, progressive=True); return out

# 1 · GALLERY WALL — a rug hung like a canvas on raw concrete, raking afternoon sun
def gallery():
    img = bg('wall')[200:2200].copy()
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # warm raking light from the upper left, falling off to the right
    light = 0.80 + 0.32 * np.clip(1.1 - (xx / W) * 0.8 - (yy / H) * 0.35, 0, 1)
    img = img * light[..., None] * np.array([1.06, 1.0, 0.92], np.float32)
    rgb, a = piece('flow-rug', height=1180, rot=-1.5)
    rgb = grade(rgb, sat=1.05, mul=(1.04, 1.0, 0.94))
    x, y = W // 2 - a.shape[1] // 2, 470
    A = np.zeros((H, W), np.float32); A[y:y + a.shape[0], x:x + a.shape[1]] = a
    # wires up to the rail: from the rug's two top shoulders straight up out of frame
    cols = np.where(A.max(0) > .5)[0]; wx = [int(cols.min() + (cols.max() - cols.min()) * f) for f in (.3, .7)]
    wires = np.zeros((H, W), np.float32)
    for x_ in wx:
        top = int(np.argmax(A[:, x_] > .5)) + 18
        cv2.line(wires, (x_ + (3 if x_ < W // 2 else -3), 0), (x_, top), 1.0, 2, cv2.LINE_AA)
    shadow(img, A, 34, 46, 22, .55); shadow(img, wires, 14, 18, 2.5, .35)
    img = img * (1 - wires[..., None] * .85) + np.array([40, 38, 36], np.float32) * wires[..., None] * .85
    r = rgb * (0.9 + 0.12 * light[y:y + a.shape[0], x:x + a.shape[1]][..., None] / light.max())
    place(img, r, a, x, y)
    return finish(img, '1-gallery-wall')

# 2 · SKY LINE — rugs and cushions pegged on yellow rope against a blue sky
ROPE = (238, 190, 40); PEGS = [(236, 92, 140), (255, 128, 46), (40, 70, 190), (120, 190, 70), (236, 92, 140), (255, 128, 46)]
def rope_y(x, x0, y0, x1, y1, sag): t = (x - x0) / (x1 - x0); return y0 + (y1 - y0) * t + 4 * sag * t * (1 - t)

def skyline():
    img = bg('sky')[60:2060].copy() * np.array([0.98, 1.0, 1.03], np.float32)
    lines = [((-60, 360, W + 60, 470, 150), [('adrift-rug', 440, 330, -3), ('fantasy-rug', 420, 1090, 4)]),
             ((-60, 1180, W + 60, 1100, 170), [('groove-cushion-cover', 360, 300, 2), ('jolt-cushion-cover', 360, 790, -2), ('zig-cushion-cover', 360, 1270, 3)])]
    pegs = []
    for (x0, y0, x1, y1, sag), items in lines:
        for name, w, cx, rot in items:
            rgb, a = piece(name, width=w, rot=rot)
            rgb = grade(rgb, sat=1.08, bright=1.03)
            # sunlit from the upper left: a gentle gradient across each piece
            h_, w_ = a.shape; g = np.linspace(1.06, 0.9, w_)[None, :] * np.linspace(1.04, 0.92, h_)[:, None]
            rgb = np.clip(rgb * g[..., None], 0, 255)
            cols = np.where(a.max(0) > .5)[0]
            px = [int(cols.min() + (cols.max() - cols.min()) * f) for f in (.22, .78)]
            tops = [int(np.argmax(a[:, p] > .5)) for p in px]
            x = cx - w_ // 2
            ry = [rope_y(x + p, x0, y0, x1, y1, sag) for p in px]
            y = int(min(r - t for r, t in zip(ry, tops)) + 6)
            place(img, rgb, a, x, y)
            for p, r in zip(px, ry): pegs.append((x + p, r))
    for (x0, y0, x1, y1, sag), _ in lines:                     # ropes in front of the pieces
        xs = np.arange(-60, W + 61, 4); pts = np.stack([xs, rope_y(xs, x0, y0, x1, y1, sag)], 1).astype(np.int32)
        m = np.zeros((H, W), np.uint8); cv2.polylines(m, [pts], False, 255, 11, cv2.LINE_AA)
        hl = np.zeros((H, W), np.uint8); cv2.polylines(hl, [pts - [0, 2]], False, 255, 3, cv2.LINE_AA)
        mv = m[..., None] / 255.; img = img * (1 - mv) + np.array(ROPE, np.float32) * 0.86 * mv
        hv = hl[..., None] / 255. * .7; img = img * (1 - hv) + np.array([255, 236, 150], np.float32) * hv
    for i, (px_, py_) in enumerate(pegs):                       # wooden-style pegs, coloured
        m = np.zeros((H, W), np.uint8)
        cv2.rectangle(m, (int(px_ - 11), int(py_ - 34)), (int(px_ + 11), int(py_ + 40)), 255, -1)
        m = cv2.GaussianBlur(m, (0, 0), 1.2); mv = m[..., None] / 255.
        col = np.array(PEGS[i % len(PEGS)], np.float32)
        shade = np.linspace(1.12, 0.82, W)[None, :, None]
        img = img * (1 - mv) + np.clip(col * shade, 0, 255) * mv
    return finish(img, '2-sky-line', 1.6)

# 3 · CROSSING — a zebra rug on the zebra crossing, people passing in low sun
def crossing():
    img = bg('street').copy()
    rgb, a = piece('balance-rug', width=560, rot=-14)
    rgb = grade(rgb, sat=0.82, mul=(1.05, 0.98, 0.86), bright=0.92)
    x, y = 900 - a.shape[1] // 2, 1645 - a.shape[0] // 2
    A = np.zeros((H, W), np.float32); A[y:y + a.shape[0], x:x + a.shape[1]] = np.clip(a, 0, 1)[:H - y]
    shadow(img, A, 7, -8, 2.2, .62, (14, 12, 10))               # sun low from lower-left, like the people's shadows
    shadow(img, A, 2, -2, 6, .30, (14, 12, 10))
    place(img, rgb, a, x, y)
    img = np.clip((img - 128) * 1.03 + 128, 0, 255)
    return finish(img, '3-crossing', 2.4)

# 4 · ROOFTOP — a giant rug draped from the parapet of a brutalist block, blue sky
def rooftop():
    img = bg('roof')[0:2000].copy()
    sky = bg('sky')
    # replace the flat overcast sky (bright, low-saturation, connected to the top edge) with blue
    u8 = np.clip(img, 0, 255).astype(np.uint8)
    roofline = np.array([(0, 795), (135, 735), (152, 735), (157, 545), (800, 170), (1600, 605), (1600, 0), (0, 0)], np.int32)
    above = np.zeros((H, W), np.uint8); cv2.fillPoly(above, [roofline], 1)
    k = np.ones((41, 41), np.uint8)
    gc = np.full((H, W), cv2.GC_BGD, np.uint8)
    gc[cv2.dilate(above, k) > 0] = cv2.GC_PR_BGD; gc[above > 0] = cv2.GC_PR_FGD; gc[cv2.erode(above, k) > 0] = cv2.GC_FGD
    y1 = 900; sub = gc[:y1].copy(); b, f = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.grabCut(cv2.cvtColor(u8[:y1], cv2.COLOR_RGB2BGR), sub, None, b, f, 6, cv2.GC_INIT_WITH_MASK)
    m = np.zeros((H, W), np.uint8); m[:y1] = np.where((sub == 1) | (sub == 3), 255, 0)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n > 1: m = np.where(lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]), 255, 0).astype(np.uint8)
    mv = cv2.GaussianBlur(m, (0, 0), 1.1)[..., None] / 255.
    S = cv2.resize(sky[0:1400, 0:1600], (W, H)) * np.array([0.96, 1.0, 1.02], np.float32)
    img = img * (1 - mv) + S * mv
    # facade a touch warmer and brighter, as if the sun came out
    img = np.where(mv > .5, img, np.clip(img * np.array([1.05, 1.02, 0.97], np.float32) + 4, 0, 255))

    im = Image.open(os.path.join(D, 'cut', 'fit-in-rug.png')).convert('RGBA')
    arr = np.array(im); cut = int(arr.shape[0] * .13); arr = arr[cut:]           # the top is folded over the parapet
    hh, ww = arr.shape[:2]
    src = np.float32([[0, 0], [ww, 0], [ww, hh], [0, hh]])
    TL, TR = (188, 531), (706, 228)
    BL, BR = (196, 1050), (712, 912)
    M = cv2.getPerspectiveTransform(src, np.float32([TL, TR, BR, BL]))
    warp = cv2.warpPerspective(arr, M, (W, H), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0)).astype(np.float32)
    A = warp[..., 3] / 255.; rgb = warp[..., :3]
    # soft vertical drape folds and the facade's light
    uu = cv2.warpPerspective(np.tile(np.linspace(0, 1, ww, dtype=np.float32), (hh, 1)), M, (W, H))
    folds = 1 + 0.07 * np.sin(uu * np.pi * 7.0) - 0.05 * np.sin(uu * np.pi * 2.3)
    rgb = grade(rgb, sat=1.06, mul=(1.0, 0.99, 0.97), bright=0.93) * folds[..., None]
    shadow(img, A, -10, 14, 12, .42, (40, 40, 44))
    img = img * (1 - A[..., None]) + rgb * A[..., None]
    # thickness of the rug where it bends over the coping
    lip = np.zeros((H, W), np.uint8); cv2.line(lip, TL, TR, 255, 9, cv2.LINE_AA)
    lv = lip[..., None] / 255. * .9; img = img * (1 - lv) + np.array([235, 236, 230], np.float32) * lv
    return finish(img, '4-rooftop', 1.8)

if __name__ == '__main__':
    fns = {'gallery': gallery, 'skyline': skyline, 'crossing': crossing, 'rooftop': rooftop}
    outs = [fns[k]() for k in (sys.argv[1:] or fns)]
    if len(outs) == 4:
        S = Image.new('RGB', (4 * 400 + 50, 520), (255, 255, 255))
        for i, o in enumerate(outs): t = o.copy(); t.thumbnail((400, 500)); S.paste(t, (10 + i * 410, 10))
        S.save(os.path.join(OUT, 'overview.jpg'), quality=88)
    print('ok')
