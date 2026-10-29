"""Editorial floating film: four real places, pieces that float like fabric (ripple, billow, lift off the ground)."""
import os, sys, subprocess, numpy as np, cv2
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
from refs import bg, grade
FPS, SCENE = 30, 4.0
TAU = 2 * np.pi

def load(name, width=None, height=None):
    im = Image.open(os.path.join(D, 'cut', name + '.png')).convert('RGBA')
    s = (width / im.width) if width else (height / im.height)
    im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    a = np.array(im).astype(np.float32); a[..., :3] *= a[..., 3:4] / 255.0       # premultiplied
    return a

class Wave:
    """Precomputed grids for one piece; frame(t) returns premultiplied RGBA with a travelling wave and its shading."""
    def __init__(self, rgba, kind, amp, lam, period, shade=0.22):
        self.kind, self.amp, self.lam, self.T, self.k = kind, amp, lam, period, shade
        P = self.P = int(amp * 1.6) + 4
        self.src = cv2.copyMakeBorder(rgba, P, P, P, P, cv2.BORDER_CONSTANT, value=0)
        h, w = rgba.shape[:2]; self.h, self.w = h, w
        yy, xx = np.mgrid[-P:h + P, -P:w + P].astype(np.float32); self.yy, self.xx = yy, xx
    def frame(self, t):
        yy, xx, P = self.yy, self.xx, self.P
        if self.kind == 'carpet':     # wave travels across the piece, lifting it up and down
            ph = TAU * (xx / self.lam - t / self.T) + TAU * 0.35 * yy / self.lam
            d = self.amp * np.sin(ph); mx, my = xx + P, yy + P - d; sh = 1 + self.k * np.cos(ph)
        else:                          # flag: top edge fixed, billow grows towards the free end
            f = np.clip(yy / self.h, 0, 1) ** 1.25
            ph = TAU * (yy / self.lam - t / self.T) + 1.3 * xx / self.w
            d = self.amp * f * np.sin(ph); mx, my = xx + P - d, yy + P - 0.25 * self.amp * f * (1 - np.cos(ph)) * 0.5
            sh = 1 + self.k * f * np.cos(ph)
        out = cv2.remap(self.src, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderValue=0)
        out[..., :3] *= sh[..., None]
        return out

def blit(canvas, prgba, cx, cy, angle=0.0, scale=1.0, shadow=None):
    """Composite premultiplied RGBA centred at (cx, cy); optional shadow=(dx, dy, blur, opacity, tone)."""
    h, w = prgba.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, scale); M[0, 2] += cx - w / 2; M[1, 2] += cy - h / 2
    H, W = canvas.shape[:2]
    out = cv2.warpAffine(prgba, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    A = out[..., 3] / 255.0
    if shadow:
        dx, dy, blur, op, tone = shadow
        S = cv2.GaussianBlur(cv2.warpAffine(A, np.float32([[1, 0, dx], [0, 1, dy]]), (W, H)), (0, 0), max(.5, blur)) * op
        canvas[:] = canvas * (1 - S[..., None]) + np.array(tone, np.float32) * S[..., None]
    canvas[:] = canvas * (1 - A[..., None]) + np.clip(out[..., :3], 0, 255)
    return A

def gradeP(p, **kw):
    a = p[..., 3:4] / 255.0; rgb = np.where(a > 0, p[..., :3] / np.maximum(a, 1e-3), 0)
    p = p.copy(); p[..., :3] = grade(rgb, **kw) * a; return p

# ---------- scenes: each returns render(t) -> canvas (float32) ----------
def scene_wall(asp):
    B = bg('wall'); base = B[200:2200] if asp == '4x5' else B[700:1600]
    H, W = base.shape[:2]; yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    light = 0.80 + 0.32 * np.clip(1.1 - (xx / W) * 0.8 - (yy / H) * 0.35, 0, 1)
    base = base * light[..., None] * np.array([1.06, 1.0, 0.92], np.float32)
    p = gradeP(load('flow-rug', height=1180 if asp == '4x5' else 760), sat=1.05, mul=(1.04, 1.0, 0.94))
    wv = Wave(p, 'flag', 9, p.shape[0] * 0.9, 2.0, 0.12)
    def render(t):
        c = base.copy(); d = 38 + 26 * np.sin(TAU * t / SCENE)            # distance off the wall
        blit(c, wv.frame(t), W / 2, H * (0.53 if asp == '4x5' else 0.5) - 0.3 * d, -1.5 + 1.2 * np.sin(TAU * t / SCENE),
             1 + d / 2500, (d * 1.1, d * 1.4, 6 + d * 0.3, 0.72 - d * 0.002, (18, 16, 14)))
        return c
    return render

def scene_crossing(asp):
    B = bg('street'); base = B if asp == '4x5' else B[820:1720]
    H, W = base.shape[:2]; cy0 = 1640 if asp == '4x5' else 585
    cx0 = 900 if asp == '4x5' else 1060
    p = gradeP(load('balance-rug', width=560 if asp == '4x5' else 400), sat=0.82, mul=(1.05, 0.98, 0.86), bright=0.92)
    wv = Wave(p, 'carpet', 13, p.shape[1] * 1.1, 2.0, 0.2)
    def render(t):
        c = base.copy(); h = 70 + 45 * np.sin(TAU * t / SCENE - np.pi / 2) + 45  # lifts off the crossing and settles back
        blit(c, wv.frame(t), cx0, cy0 - h * 0.08, -14 + 6 * np.sin(TAU * t / SCENE), 1 + h / 1800,
             (0.55 * h + 4, -0.65 * h - 4, 2 + h * 0.09, 0.62 - h * 0.0012, (14, 12, 10)))
        return np.clip((c - 128) * 1.03 + 128, 0, 255)
    return render

def scene_roof(asp):
    B = bg('roof'); y0 = 0 if asp == '4x5' else 180
    base = B[y0:y0 + (2000 if asp == '4x5' else 900)].copy(); H, W = base.shape[:2]
    # same sky swap as the still: overcast -> blue

    full = np.array(Image.open(os.path.join(D, 'refs', '_roof_plate.png'))).astype(np.float32)
    base = full[y0:y0 + H]
    im = np.array(Image.open(os.path.join(D, 'cut', 'fit-in-rug.png')).convert('RGBA')).astype(np.float32)
    im = im[int(im.shape[0] * .13):]; im[..., :3] *= im[..., 3:4] / 255.0
    im = gradeP(im, sat=1.06, mul=(1.0, 0.99, 0.97), bright=0.93)
    hh, ww = im.shape[:2]
    TL, TR, BL, BR = (188, 531 - y0), (706, 228 - y0), (196, 1050 - y0), (712, 912 - y0)
    M = cv2.getPerspectiveTransform(np.float32([[0, 0], [ww, 0], [ww, hh], [0, hh]]), np.float32([TL, TR, BR, BL]))
    wv = Wave(im, 'flag', 34, hh * 0.75, 2.0, 0.26); P = wv.P
    T = np.float32([[1, 0, -P], [0, 1, -P], [0, 0, 1]]); MP = M @ T
    def render(t):
        c = base.copy(); f = wv.frame(t)
        out = cv2.warpPerspective(f, MP, (W, H), flags=cv2.INTER_LINEAR, borderValue=0); A = out[..., 3] / 255.
        S = cv2.GaussianBlur(np.roll(np.roll(A, 14, 0), -10, 1), (0, 0), 12) * .42
        c = c * (1 - S[..., None]) + np.array([40, 40, 44], np.float32) * S[..., None]
        c = c * (1 - A[..., None]) + np.clip(out[..., :3], 0, 255)
        lip = np.zeros((H, W), np.uint8); cv2.line(lip, TL, TR, 255, 9, cv2.LINE_AA)
        lv = lip[..., None] / 255. * .9; return c * (1 - lv) + np.array([235, 236, 230], np.float32) * lv
    return render

def scene_sky(asp):
    B = bg('sky'); base = B[60:2060] if asp == '4x5' else B[400:1300]; H, W = base.shape[:2]
    k = 1.0 if asp == '4x5' else 0.62
    specs = [('adrift-rug', 470, (300, 560), (70, -10)), ('zig-cushion-cover', 300, (1180, 980), (-55, 8)), ('fantasy-rug', 360, (520, 1500), (45, -14))]
    if asp != '4x5': specs = [('adrift-rug', 470, (330, 380), (70, -10)), ('zig-cushion-cover', 300, (1240, 330), (-55, 8)), ('fantasy-rug', 360, (820, 610), (45, -14))]
    items = []
    for i, (n, w, pos, vel) in enumerate(specs):
        p = gradeP(load(n, width=w * k), sat=1.08, bright=1.03)
        items.append((Wave(p, 'carpet', 16 * k + 6, p.shape[1] * 0.95, 2.0, 0.24), pos, vel, i))
    def render(t):
        c = base.copy()
        for wv, (x, y), (vx, vy), i in items:
            ph = TAU * t / SCENE + i * 2.1
            blit(c, wv.frame(t + i * 0.4), x + vx * t, y + vy * t + 18 * np.sin(ph), 8 * np.sin(ph + 1) - 4 * i, 1.0)
        return c
    return render

SCENES = [scene_wall, scene_crossing, scene_roof, scene_sky]

def render(asp, out_w, out_h, path):
    rs = [s(asp) for s in SCENES]; n = int(FPS * SCENE)
    rng = np.random.default_rng(1)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{out_w}x{out_h}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-crf', '19', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', path], stdin=subprocess.PIPE)
    for si, r in enumerate(rs):
        for f in range(n):
            t = f / FPS; c = r(t); H, W = c.shape[:2]
            z = 1.0 + 0.045 * t / SCENE                                       # slow push-in per scene
            cw, ch = W / z, H / z; x0, y0 = (W - cw) / 2, (H - ch) / 2
            M = np.float32([[out_w / cw, 0, -x0 * out_w / cw], [0, out_h / ch, -y0 * out_h / ch]])
            o = cv2.warpAffine(np.clip(c, 0, 255), M, (out_w, out_h), flags=cv2.INTER_AREA)
            o += rng.normal(0, 1.8, (out_h, out_w, 1)).astype(np.float32)
            ff.stdin.write(np.clip(o, 0, 255).astype(np.uint8).tobytes())
            if f == n // 2: Image.fromarray(np.clip(o, 0, 255).astype(np.uint8)).save(path.replace('.mp4', f'-s{si}.jpg'), quality=85)
        print(asp, 'scene', si, flush=True)
    ff.stdin.close(); ff.wait()

if __name__ == '__main__':
    os.makedirs(os.path.join(D, 'film'), exist_ok=True)
    which = sys.argv[1:] or ['4x5', '16x9']
    for a in which:
        w, h = (1080, 1350) if a == '4x5' else (1920, 1080)
        render(a, w, h, os.path.join(D, 'film', f'black-mango-editorial-{a}.mp4'))
