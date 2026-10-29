import glob, numpy as np
from PIL import Image
T='/root/.claude/projects/-home-claude/e10d4f4a-dff8-56ac-9f3c-454cc902bc83/tool-results/'
def f(tag): return Image.open(glob.glob(T+'*-'+tag+'.*')[0]).convert('RGB')
S={'wall':(2400,800,['kv576u','a0jfji','4e75qc','00nlij']),
   'sky':(2133,533,['rbp8cu','43bha7','2uptyi','jx84sx']),
   'street':(2000,400,['r7h4es','dx3n7f','00k1hr','y9ktoz']),
   'roof':(2133,533,['th2i4g','ie6fi8','0pc2me','jl4urd'])}
for n,(h,dy,t) in S.items():
    c=Image.new('RGB',(1600,h))
    for i,tag in enumerate(t):
        im=f(tag); x=(i%2)*800; y=(i//2)*dy
        c.paste(im.crop((0,0,800,min(1600,h-y))),(x,y))
    c.save(f'bg/{n}.png'); print(n,c.size)
