from PIL import Image, ImageDraw, ImageFont, ImageFilter
FD='fonts/'
def F(name,size,var=None):
    f=ImageFont.truetype(FD+name,size)
    if var: f.set_variation_by_name(var)
    return f
def hx(h): h=h.lstrip('#'); return tuple(int(h[i:i+2],16) for i in (0,2,4))
AR=dict(direction='rtl',language='ar')

DIRS={
 'A':dict(title='A · Arcade',note='Lime on charcoal. Loud, playful, reads as games at a glance.',
   ground='#121412',panel='#1C201B',accent='#C6F432',ink='#F4F6EF',body='#B9C0B2',
   disp=('Lalezar-Regular.ttf',None),text=('Tajawal-Bold.ttf',None),mark='pixel'),
 'B':dict(title='B · Majlis',note='Emerald and cream. Calm, premium, rooted in the region.',
   ground='#0D2A23',panel='#143A30',accent='#4FD3A0',ink='#F3EEE3',body='#BFD3C8',
   disp=('Alexandria[wght].ttf',b'Bold'),text=('IBMPlexSansArabic-Medium.ttf',None),mark='arch'),
 'C':dict(title='C · Sand',note='Light sand, ink and terracotta. Editorial, stands out in a dark timeline.',
   ground='#EFE5D3',panel='#E4D6BE',accent='#C9502B',ink='#1A1714',body='#4A423A',
   disp=('Changa[wght].ttf',b'ExtraBold'),text=('Almarai-Bold.ttf',None),mark='dpad'),
}

def mark(D,size):
    """Square avatar art; X crops it to a circle."""
    g,a,ink=hx(D['ground']),hx(D['accent']),hx(D['ink'])
    S=size*4
    im=Image.new('RGB',(S,S),g); d=ImageDraw.Draw(im)
    if D['mark']=='pixel':
        im=Image.new('RGB',(S,S),a); d=ImageDraw.Draw(im)
        f=F(D['disp'][0],int(S*0.78))
        d.text((S*0.58,S*0.47),'د',font=f,fill=g,anchor='mm',**AR)
        y=int(S*0.60)
        for x,p in ((0.31,0.07),(0.225,0.05),(0.16,0.035)):
            x=int(S*x); p=int(S*p); d.rectangle((x,y-p//2,x+p,y+p//2),fill=g)
    elif D['mark']=='arch':
        w,h=S*0.54,S*0.64; cx=S/2; top=S*0.19; bot=top+h; r=w/2; lw=int(S*0.07)
        # arch: semicircle top + straight sides
        d.pieslice((cx-r,top,cx+r,top+w),180,360,fill=ink)
        d.rectangle((cx-r,top+r,cx+r,bot),fill=ink)
        r2=r-lw
        d.pieslice((cx-r2,top+lw,cx+r2,top+lw+2*r2),180,360,fill=g)
        d.rectangle((cx-r2,top+r,cx+r2,bot-lw),fill=g)
        f=F(D['disp'][0],int(S*0.40),D['disp'][1])
        d.text((cx,top+h*0.60),'د',font=f,fill=a,anchor='mm',**AR)
    else:
        arm=S*0.20; L=S*0.64; cx=cy=S/2; rr=int(S*0.04)
        d.rounded_rectangle((cx-L/2,cy-arm/2,cx+L/2,cy+arm/2),radius=rr,fill=ink)
        d.rounded_rectangle((cx-arm/2,cy-L/2,cx+arm/2,cy+L/2),radius=rr,fill=ink)
        t=S*0.05; e=L/2-S*0.07
        for dx,dy in ((0,-1),(0,1),(-1,0),(1,0)):
            tx,ty=cx+dx*e,cy+dy*e
            if dx==0: pts=[(tx,ty+dy*t),(tx-t,ty-dy*t*0.2),(tx+t,ty-dy*t*0.2)]
            else: pts=[(tx+dx*t,ty),(tx-dx*t*0.2,ty-t),(tx-dx*t*0.2,ty+t)]
            d.polygon(pts,fill=g)
        c=S*0.055; d.ellipse((cx-c,cy-c,cx+c,cy+c),fill=a)
    return im.resize((size,size),Image.LANCZOS)

def circle(im):
    m=Image.new('L',(im.width*4,im.height*4),0); ImageDraw.Draw(m).ellipse((0,0,m.width-1,m.height-1),fill=255)
    m=m.resize(im.size,Image.LANCZOS); out=Image.new('RGBA',im.size,(0,0,0,0)); out.paste(im,(0,0),m); return out

def banner(D):
    W,H=1500,500; g,a,ink,body,panel=[hx(D[k]) for k in ('ground','accent','ink','body','panel')]
    im=Image.new('RGB',(W,H),g); d=ImageDraw.Draw(im)
    if D['mark']=='pixel':
        s=22
        for yy in range(0,H,s):
            for xx in range(0,W,s):
                if (xx*7+yy*13)%97<5: d.rectangle((xx,yy,xx+s-4,yy+s-4),fill=panel)
        d.rectangle((0,H-10,W,H),fill=a)
    elif D['mark']=='arch':
        r=70
        for i,xx in enumerate(range(-40,W+140,150)):
            top=H-230 if i%2 else H-190
            d.pieslice((xx,top,xx+2*r,top+2*r),180,360,fill=panel); d.rectangle((xx,top+r,xx+2*r,H),fill=panel)
    else:
        d.rectangle((0,0,W,H),fill=g)
        d.rectangle((0,0,W,14),fill=a)
    fd=F(D['disp'][0],132,D['disp'][1]); ft=F(D['text'][0],40,D['text'][1]); fl=F(D['disp'][0],30,D['disp'][1])
    d.text((W/2,H*0.40),'ديجيتال لاونج',font=fd,fill=ink,anchor='mm',**AR)
    d.text((W/2,H*0.65),'أخبار الألعاب',font=ft,fill=a if D['mark']!='dpad' else a,anchor='mm',**AR)
    d.text((W/2,H*0.79),'D I G I T A L   L O U N G E',font=fl,fill=body,anchor='mm')
    return im

def footer(D):
    W=1600; g,a,ink,body=[hx(D[k]) for k in ('ground','accent','ink','body')]
    im=Image.new('RGB',(W,330),g); d=ImageDraw.Draw(im)
    # media strip stand-in
    d.rectangle((0,0,W,200),fill=(70,74,80)); 
    for i in range(0,W,40): d.line((i,0,i-200,200),fill=(80,84,90),width=12)
    ch=F(D['text'][0],40,D['text'][1]); t='رسمي'
    tw=d.textlength(t,font=ch,**AR); x2=W-40; y=200-34-58
    d.rounded_rectangle((x2-tw-56,y,x2,y+58),radius=10,fill=a)
    d.text((x2-28,y+29),t,font=ch,fill=g,anchor='rm',**AR)
    d.rectangle((0,200,W,206),fill=a)
    m=mark(D,72); m=circle(m); im.paste(m,(W-40-72,206+26),m)
    fn=F(D['disp'][0],44,D['disp'][1]); fs=F(D['text'][0],36,D['text'][1])
    d.text((W-40-72-20,206+62),'ديجيتال لاونج',font=fn,fill=ink,anchor='rm',**AR)
    d.text((W/2,206+62),'فاميتسو',font=fs,fill=body,anchor='mm',**AR)
    d.text((40,206+62),'26 سبتمبر 2026',font=fs,fill=ink,anchor='lm',**AR)
    return im

for k,D in DIRS.items():
    g=hx(D['ground']); dark=sum(g)<380
    bg=(24,24,24) if not dark else (236,236,236)
    B=Image.new('RGB',(1700,1560),(20,20,20)); d=ImageDraw.Draw(B)
    lf=F('Tajawal-Bold.ttf',46); sf=F('Tajawal-Medium.ttf',30)
    d.text((50,40),D['title'],font=lf,fill=(245,245,245))
    d.text((50,100),D['note'],font=sf,fill=(170,170,170))
    av=circle(mark(D,360)); B.paste(av,(50,170),av)
    small=circle(mark(D,48)); B.paste(small,(440,482),small)
    d.text((500,506),'48px, as in the timeline',font=sf,fill=(170,170,170),anchor='lm')
    bn=banner(D).resize((1150,383),Image.LANCZOS); B.paste(bn,(500,170))
    # palette
    x=500
    for name in ('ground','panel','accent','ink','body'):
        d.rounded_rectangle((x,580,x+200,680),radius=12,fill=hx(D[name]),outline=(60,60,60))
        d.text((x,700),f"{name}  {D[name]}",font=sf,fill=(200,200,200)); x+=230
    d.text((50,580),'Display: '+D['disp'][0].split('[')[0].replace('.ttf',''),font=sf,fill=(200,200,200))
    d.text((50,625),'Text: '+D['text'][0].split('[')[0].replace('.ttf',''),font=sf,fill=(200,200,200))
    d.text((50,760),'Fast card footer (right to left, chip رسمي = OFFICIAL)',font=sf,fill=(170,170,170))
    ft=footer(D).resize((1600,330)); B.paste(ft,(50,810))
    # Headline sample
    hf=F(D['disp'][0],60,D['disp'][1])
    box=Image.new('RGB',(1600,340),hx(D['ground'])); dd=ImageDraw.Draw(box)
    dd.text((1560,90),'هنا يظهر عنوان الخبر',font=hf,fill=hx(D['ink']),anchor='rm',**AR)
    tf=F(D['text'][0],38,D['text'][1])
    dd.text((1560,190),'وهنا نص الخبر بالحجم الذي يُقرأ على الهاتف،',font=tf,fill=hx(D['body']),anchor='rm',**AR)
    dd.text((1560,250),'سطران أو ثلاثة على الأكثر.',font=tf,fill=hx(D['body']),anchor='rm',**AR)
    dd.rectangle((1560-8,20,1560,40),fill=hx(D['accent']))
    B.paste(box,(50,1170))
    B.save(f'digi-direction-{k}.png'); banner(D).save(f'digi-banner-{k}.png'); mark(D,400).save(f'digi-avatar-{k}.png')
print('ok')
