"""Overlay the 'Objects with presence' line on the editorial film (Instrument Serif + Geist Mono)."""
import os, sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
F = '/mnt/skills/examples/canvas-design/canvas-fonts/'
D = os.path.dirname(os.path.abspath(__file__))
SER, ITA, MONO = F + 'InstrumentSerif-Regular.ttf', F + 'InstrumentSerif-Italic.ttf', F + 'GeistMono-Regular.ttf'

def spaced(d, xy, text, font, track, fill):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill); x += d.textlength(ch, font=font) + track
    return x

def overlay(W, H, scene):
    """RGBA overlay: white type plus a soft shadow so it reads on sky, concrete and stripes alike."""
    vert = H > W; m = round(W * (0.06 if vert else 0.042))
    size = round(W * (0.155 if vert else 0.074))
    ser, ita, mono = ImageFont.truetype(SER, size), ImageFont.truetype(ITA, size), ImageFont.truetype(MONO, round(W * (0.019 if vert else 0.0105)))
    T = Image.new('L', (W, H), 0); d = ImageDraw.Draw(T)
    asc, desc = ser.getmetrics(); lh = round(size * 0.92)
    if vert:                                   # two lines, stacked tight
        y2 = H - m - asc + round(size * 0.04); y1 = y2 - lh
        d.text((m - round(size * .03), y1), 'Objects', font=ser, fill=255)
        x = m - round(size * .03) + d.textlength('with ', font=ser)
        d.text((m - round(size * .03), y2), 'with', font=ser, fill=255); d.text((x, y2), 'presence', font=ita, fill=255)
    else:
        y = H - m - asc + round(size * 0.04); x = m - round(size * .03)
        d.text((x, y), 'Objects with ', font=ser, fill=255); d.text((x + d.textlength('Objects with ', font=ser), y), 'presence', font=ita, fill=255)
    tr = round(mono.size * 0.32)
    spaced(d, (m, m), 'BLACK MANGO', mono, tr, 255)
    lbl = f'{scene + 1:02d} / 04'; w = sum(d.textlength(c, font=mono) + tr for c in lbl) - tr
    spaced(d, (W - m - w, m), lbl, mono, tr, 255)
    sh = np.array(T.filter(ImageFilter.GaussianBlur(size * 0.12)), np.float32) / 255 * 0.42
    sh = np.maximum(sh, np.array(T.filter(ImageFilter.GaussianBlur(2)), np.float32) / 255 * 0.25)
    t = np.array(T, np.float32) / 255
    return sh, t

def run(src, dst, W, H, fps=30, scene_len=4.0):
    ovs = [overlay(W, H, s) for s in range(4)]
    for s in range(4):
        sh, t = ovs[s]; Image.fromarray((np.clip(t, 0, 1) * 255).astype(np.uint8)).save(dst.replace('.mp4', f'-type{s}.png'))
    dec = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-i', src, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(fps), '-i', '-',
                            '-c:v', 'libx264', '-crf', '19', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', dst], stdin=subprocess.PIPE)
    n = 0; ink = np.array([255, 252, 246], np.float32)
    while True:
        b = dec.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        f = np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(np.float32)
        sh, t = ovs[min(3, int(n / fps // scene_len))]
        f = f * (1 - sh[..., None]) + 10 * sh[..., None]
        f = f * (1 - t[..., None]) + ink * t[..., None]
        enc.stdin.write(np.clip(f, 0, 255).astype(np.uint8).tobytes()); n += 1
    enc.stdin.close(); enc.wait(); print(dst, n, 'frames')

if __name__ == '__main__':
    V = '/home/claude/blackmangosite/videos/'
    for a, (W, H) in (('4x5', (1080, 1350)), ('16x9', (1920, 1080))):
        if len(sys.argv) > 1 and a not in sys.argv[1:]: continue
        run(os.path.join(D, 'film', f'black-mango-editorial-{a}.mp4'), os.path.join(D, 'film', f'black-mango-objects-with-presence-{a}.mp4'), W, H)
