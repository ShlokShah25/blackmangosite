"""Rebuild ../index.html from site.html, embedding every image in assets/ as a data URI.
Run: python3 source/build.py"""
import base64, json, os
here = os.path.dirname(os.path.abspath(__file__))
imgs = {}
for f in sorted(os.listdir(os.path.join(here, 'assets'))):
    stem, ext = os.path.splitext(f)
    mime = {'.webp': 'image/webp', '.jpg': 'image/jpeg', '.png': 'image/png'}[ext]
    with open(os.path.join(here, 'assets', f), 'rb') as fh:
        imgs[stem] = f'data:{mime};base64,' + base64.b64encode(fh.read()).decode()
src = open(os.path.join(here, 'site.html'), encoding='utf-8').read().replace('"__IMG_JSON__"', json.dumps(imgs))
head = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="Black Mango: hand-tufted rugs, tufted cushions and sculptural objects from Mumbai.">
<meta name="theme-color" content="#0C0A08">
<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>
'''
i = src.index('</style>') + len('</style>')
out = head + src[:i] + '\n</head>\n<body>\n' + src[i:] + '\n</body>\n</html>\n'
open(os.path.join(here, '..', 'index.html'), 'w', encoding='utf-8').write(out)
print(f'{len(imgs)} images, {len(out)/1e6:.2f} MB -> index.html')
