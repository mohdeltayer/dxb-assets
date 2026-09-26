import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
DF='/root/fonts-private/dubai/Dubai-'
def F(w,size): return ImageFont.truetype(DF+w+'.ttf',size)
def hx(h): h=h.lstrip('#'); return tuple(int(h[i:i+2],16) for i in (0,2,4))
AR=dict(direction='rtl',language='ar')
P=dict(ground='#141332',panel='#1E1D4A',edge='#3F3DA8',azure='#28B6F6',magenta='#EE33DD',ink='#F4F3FF',body='#C9C8E6')
C={k:hx(v) for k,v in P.items()}

def radial(S):
    """The current avatar's ground: indigo edge falling to deep centre."""
    im=Image.new('RGB',(S,S)); px=im.load(); c=S/2
    for y in range(S):
        for x in range(S):
            t=min(1,math.hypot(x-c,y-c)/(S*0.62))
            px[x,y]=tuple(int(C['ground'][i]+(C['edge'][i]-C['ground'][i])*t**1.4) for i in range(3))
    return im

def mark(kind,size):
    S=size*3 if size>100 else 400
    im=radial(S); d=ImageDraw.Draw(im)
    if kind=='A':
        f=F('Bold',int(S*0.80))
        d.text((S*0.58,S*0.44),'د',font=f,fill=C['azure'],anchor='mm',**AR)
        y=int(S*0.62)
        for x,p in ((0.30,0.07),(0.215,0.05),(0.15,0.035)):
            x=int(S*x); p=int(S*p); d.rectangle((x,y-p//2,x+p,y+p//2),fill=C['magenta'])
    elif kind=='B':
        w,h=S*0.54,S*0.64; cx=S/2; top=S*0.18; bot=top+h; r=w/2; lw=int(S*0.07)
        d.pieslice((cx-r,top,cx+r,top+w),180,360,fill=C['azure']); d.rectangle((cx-r,top+r,cx+r,bot),fill=C['azure'])
        r2=r-lw; inner=radial(S)
        m=Image.new('L',(S,S),0); md=ImageDraw.Draw(m)
        md.pieslice((cx-r2,top+lw,cx+r2,top+lw+2*r2),180,360,fill=255); md.rectangle((cx-r2,top+r,cx+r2,bot-lw),fill=255)
        im.paste(inner,(0,0),m); d=ImageDraw.Draw(im)
        d.text((cx,top+h*0.55),'د',font=F('Bold',int(S*0.58)),fill=C['magenta'],anchor='mm',**AR)
    else:
        arm=S*0.20; L=S*0.64; cx=cy=S/2; rr=int(S*0.04)
        d.rounded_rectangle((cx-L/2,cy-arm/2,cx+L/2,cy+arm/2),radius=rr,fill=C['azure'])
        d.rounded_rectangle((cx-arm/2,cy-L/2,cx+arm/2,cy+L/2),radius=rr,fill=C['azure'])
        t=S*0.05; e=L/2-S*0.07
        for dx,dy in ((0,-1),(0,1),(-1,0),(1,0)):
            tx,ty=cx+dx*e,cy+dy*e
            pts=[(tx,ty+dy*t),(tx-t,ty-dy*t*0.2),(tx+t,ty-dy*t*0.2)] if dx==0 else [(tx+dx*t,ty),(tx-dx*t*0.2,ty-t),(tx-dx*t*0.2,ty+t)]
            d.polygon(pts,fill=C['ground'])
        c=S*0.06; d.ellipse((cx-c,cy-c,cx+c,cy+c),fill=C['magenta'])
    return im.resize((size,size),Image.LANCZOS)

def circle(im):
    m=Image.new('L',(im.width*4,im.height*4),0); ImageDraw.Draw(m).ellipse((0,0,m.width-1,m.height-1),fill=255)
    m=m.resize(im.size,Image.LANCZOS); out=Image.new('RGBA',im.size,(0,0,0,0)); out.paste(im,(0,0),m); return out

def waves(W,H,k=2):
    """Redraw of the current banner: flowing lines, magenta left to azure right."""
    big=Image.new('RGB',(W*k,H*k),C['ground']); d=ImageDraw.Draw(big)
    for j in range(-6,40):
        base=j*34*k; pts=[]
        for x in range(0,W*k+20,12):
            u=x/(W*k)
            y=base+60*k*math.sin(u*5.2+j*0.18)+40*k*math.sin(u*11+0.7)*math.exp(-((u-0.33)/0.12)**2)+30*k*math.sin(u*3+j*0.1)
            pts.append((x,y))
        for i in range(len(pts)-1):
            u=pts[i][0]/(W*k)
            col=tuple(int(C['magenta'][c]+(C['azure'][c]-C['magenta'][c])*u) for c in range(3))
            col=tuple(int(C['ground'][c]+(col[c]-C['ground'][c])*0.75) for c in range(3))
            d.line((pts[i],pts[i+1]),fill=col,width=3*k)
    return big.resize((W,H),Image.LANCZOS)

def banner():
    W,H=1500,500; im=waves(W,H)
    ov=Image.new('RGBA',(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov)
    od.rounded_rectangle((360,95,1140,415),radius=22,fill=C['ground']+(235,))
    im=Image.alpha_composite(im.convert('RGBA'),ov).convert('RGB'); d=ImageDraw.Draw(im)
    d.text((W/2,200),'ديجيتال لاونج',font=F('Bold',112),fill=C['ink'],anchor='mm',**AR)
    d.text((W/2,318),'أخبار الألعاب',font=F('Medium',44),fill=C['azure'],anchor='mm',**AR)
    d.text((W/2,372),'D I G I T A L   L O U N G E',font=F('Medium',26),fill=C['body'],anchor='mm')
    return im

def footer(kind):
    W=1600; im=Image.new('RGB',(W,330),C['ground']); d=ImageDraw.Draw(im)
    d.rectangle((0,0,W,200),fill=(70,74,80))
    for i in range(0,W+200,40): d.line((i,0,i-200,200),fill=(80,84,90),width=12)
    ch=F('Bold',42); t='رسمي'; tw=d.textlength(t,font=ch,**AR); x2=W-40; y=200-34-60
    d.rounded_rectangle((x2-tw-56,y,x2,y+60),radius=10,fill=C['magenta'])
    d.text((x2-28,y+32),t,font=ch,fill=C['ink'],anchor='rm',**AR)
    d.rectangle((0,200,W,206),fill=C['magenta'])
    m=circle(mark(kind,72)); im.paste(m,(W-40-72,206+26),m)
    d.text((W-40-72-20,206+64),'ديجيتال لاونج',font=F('Bold',46),fill=C['ink'],anchor='rm',**AR)
    d.text((W/2,206+64),'فاميتسو',font=F('Medium',36),fill=C['body'],anchor='mm',**AR)
    d.text((40,206+64),'26 سبتمبر 2026',font=F('Medium',36),fill=C['ink'],anchor='lm',**AR)
    return im

NAMES={'A':'A · Pixel dal','B':'B · Arch','C':'C · D-pad'}
bn=banner(); bn.save('digi2-banner.png')
for k in 'ABC':
    B=Image.new('RGB',(1700,1560),(18,18,22)); d=ImageDraw.Draw(B)
    d.text((50,30),NAMES[k],font=F('Bold',52),fill=(245,245,245))
    d.text((50,100),'Current palette, Dubai font throughout',font=F('Regular',32),fill=(170,170,180))
    av=circle(mark(k,360)); B.paste(av,(50,170),av)
    s=circle(mark(k,48)); B.paste(s,(440,482),s)
    d.text((500,506),'48px, as in the timeline',font=F('Regular',30),fill=(170,170,180),anchor='lm')
    B.paste(bn.resize((1150,383),Image.LANCZOS),(500,170))
    x=500
    for name in ('ground','panel','edge','azure','magenta','ink'):
        d.rounded_rectangle((x,580,x+170,670),radius=12,fill=C[name],outline=(60,60,70))
        d.text((x,688),name,font=F('Medium',28),fill=(210,210,220)); d.text((x,722),P[name],font=F('Regular',26),fill=(160,160,170)); x+=192
    d.text((50,590),'Dubai Bold',font=F('Bold',40),fill=(230,230,240)); d.text((50,640),'Dubai Medium, Regular',font=F('Regular',30),fill=(170,170,180))
    d.text((50,770),'Fast card footer, right to left (رسمي = OFFICIAL)',font=F('Regular',30),fill=(170,170,180))
    B.paste(footer(k),(50,815))
    box=Image.new('RGB',(1600,330),C['ground']); dd=ImageDraw.Draw(box)
    dd.rectangle((1552,24,1560,48),fill=C['magenta'])
    dd.text((1560,105),'هنا يظهر عنوان الخبر',font=F('Bold',66),fill=C['ink'],anchor='rm',**AR)
    dd.text((1560,200),'وهنا نص الخبر بالحجم الذي يُقرأ على الهاتف،',font=F('Regular',40),fill=C['body'],anchor='rm',**AR)
    dd.text((1560,262),'سطران أو ثلاثة على الأكثر.',font=F('Regular',40),fill=C['body'],anchor='rm',**AR)
    B.paste(box,(50,1175))
    B.save(f'digi2-direction-{k}.png'); mark(k,400).save(f'digi2-avatar-{k}.png')
print('ok')
