import sys; sys.path.insert(0,'/home/user/dxb-assets/templates')
from PIL import Image, ImageDraw
import flex
F,M,W,H=flex.F,flex.M,flex.W,flex.H
OUT=sys.argv[1]; BGMODE=sys.argv[2] if len(sys.argv)>2 else 'voiced'
bg,panel,panel2,edge=flex.ground(BGMODE); acc=flex.resolve('cold')
INK,BODY=flex.INK,flex.BODY; muted=flex.lift(BODY,-0.30,bg)
im=Image.new('RGB',(W,H),bg); d=ImageDraw.Draw(im)
header='The missing console'
cap=Image.open('/home/user/dxb-assets/live/2026-09-26/req-capsule616.jpg').convert('RGB').crop((0,62,380,272)).resize((340,188),Image.LANCZOS)
mk=Image.new('L',cap.size,0); ImageDraw.Draw(mk).rounded_rectangle([0,0,cap.width-1,cap.height-1],radius=18,fill=255)
im.paste(cap,(M,104),mk); d=ImageDraw.Draw(im)
tx=M+cap.width+36
d.text((tx,116),header,font=F(70,800),fill=INK)
d.text((tx,214),'Resident Evil Requiem, official vs estimated',font=F(38,450),fill=BODY)
flex.filled_label(d,'analysis',W-M,128,acc,bg,anchor='rt')

top=340; GAP=36; LW=560; lx0,lx1=M,M+LW; rx0,rx1=M+LW+GAP,W-M
bot=1590
# ---- left: official / counted
d.rounded_rectangle([lx0,top,lx1,bot],radius=24,fill=panel)
x=lx0+44; y=top+48
d.text((x,y),'OFFICIAL',font=F(30,800),fill=acc); y+=46
d.text((x,y),'30 June 2026',font=F(34,600),fill=BODY); y+=76
d.text((x,y),'8.06M',font=F(150,800),fill=INK); y+=190
for ln in ['Capcom, worldwide, all four','platforms. Shipped + digital']:
    d.text((x,y),ln,font=F(36,450),fill=BODY); y+=48
y+=50
d.line([x,y,lx1-44,y],fill=edge,width=2); y+=44
d.text((x,y),'HARDWARE · 30 JUNE',font=F(28,800),fill=acc); y+=44
d.text((x,y),'Sony, Nintendo, official',font=F(32,450),fill=muted); y+=70
for name,val in [('PS5','95.3M'),('Switch 2','23.68M')]:
    d.text((x,y),name,font=F(44,600),fill=BODY)
    d.text((lx1-44,y),val,font=F(60,800),fill=INK,anchor='ra'); y+=90
y+=30
d.line([x,y,lx1-44,y],fill=edge,width=2); y+=44
d.text((x,y),'COUNTED · JAPAN BOXED',font=F(28,800),fill=acc); y+=44
d.text((x,y),'Famitsu, to late May',font=F(32,450),fill=muted); y+=70
for name,val in [('PS5','207K'),('Switch 2','66K')]:
    d.text((x,y),name,font=F(44,600),fill=BODY)
    d.text((lx1-44,y),val,font=F(60,800),fill=INK,anchor='ra'); y+=90

# ---- right: estimate as of 25 Sep
d.rounded_rectangle([rx0,top,rx1,bot],radius=24,fill=panel)
x=rx0+44; y=top+48
d.text((x,y),'ESTIMATE',font=F(30,800),fill=acc); y+=46
d.text((x,y),'25 September 2026',font=F(34,600),fill=BODY); y+=76
d.text((x,y),'~8.9M',font=F(150,800),fill=INK)
d.text((rx1-44,y+120),'range 8.75 to 9.06M',font=F(32,450),fill=muted,anchor='rs'); y+=190
for ln in ['All platforms. Copies bought by players']:
    d.text((x,y),ln,font=F(36,450),fill=BODY); y+=48
y+=60
rows=[('PS5',4.01,None,'a'),('Steam',3.69,None,'a'),('Xbox + Windows',0.73,None,'a'),
      ('Switch 2',0.41,(0.29,0.53),'d'),('Epic',0.07,(0.04,0.09),'d')]
labw=290; valw=140; bx0=x+labw; bx1=rx1-44-valw; vmax=4.2
sc=lambda v: bx0+(bx1-bx0)*v/vmax
BH=46; STEP=96
for name,v,rng,kind in rows:
    cy=y+BH/2
    d.text((x,cy),name,font=F(34,600),fill=BODY,anchor='lm')
    d.line([bx0,y-10,bx0,y+BH+10],fill=edge,width=2)
    e=max(sc(v),bx0+8)
    if kind=='a':
        d.rounded_rectangle([bx0,y,e,y+BH],radius=4,fill=acc)
    else:
        hat=Image.new('RGBA',(int(e-bx0)+1,BH),(0,0,0,0)); hd=ImageDraw.Draw(hat)
        for t in range(-BH,hat.width+BH,14): hd.line([t,BH,t+BH,0],fill=acc+(255,),width=3)
        m=Image.new('L',hat.size,0); ImageDraw.Draw(m).rounded_rectangle([0,0,hat.width-1,BH-1],radius=4,fill=255)
        im.paste(hat,(bx0,int(y)),Image.composite(hat,Image.new('RGBA',hat.size,(0,0,0,0)),m)); d=ImageDraw.Draw(im)
        d.rounded_rectangle([bx0,y,e,y+BH],radius=4,outline=acc,width=3)
        l,h=sc(rng[0]),sc(rng[1])
        d.line([l,cy,h,cy],fill=INK,width=3); d.line([l,cy-12,l,cy+12],fill=INK,width=3); d.line([h,cy-12,h,cy+12],fill=INK,width=3)
    d.text((rx1-44,cy),f'{v:.2f}M',font=F(36,800),fill=INK,anchor='rm')
    y+=STEP
y+=20
# legend
d.rounded_rectangle([x,y,x+40,y+28],radius=4,fill=acc); d.text((x+56,y+14),'Alinea estimate',font=F(28,600),fill=BODY,anchor='lm')
lx=x+330
hat=Image.new('RGBA',(40,28),(0,0,0,0)); hd=ImageDraw.Draw(hat)
for t in range(-28,68,10): hd.line([t,28,t+28,0],fill=acc+(255,),width=2)
im.paste(hat,(lx,int(y)),hat); d=ImageDraw.Draw(im); d.rounded_rectangle([lx,y,lx+40,y+28],radius=4,outline=acc,width=2)
d.text((lx+56,y+14),'Our estimate',font=F(28,600),fill=BODY,anchor='lm')
y+=80
d.line([x,y,rx1-44,y],fill=edge,width=2); y+=40
for ln,c,f in [('Xbox is ~8.2% of all copies, not 8.6%',INK,F(38,700)),('Switch 2 is about half of Xbox',INK,F(38,700))]:
    d.text((x,y),ln,font=f,fill=c); y+=56

# his take
y=bot+34
for ln in ['Switch 2 is left out of the numbers going round, so this fills in the','whole picture. It is a guess, not a count.']:
    d.text((M,y),ln,font=F(38,700),fill=INK); y+=50
y+=16
# method line
for ln in ['Method: Capcom official total · Alinea platform estimates (no Switch 2 or Epic)',
           '· Switch 2: Japan owners buy at 41% of the PS5 rate (Famitsu), scaled like PS5 worldwide']:
    d.text((M,y),ln,font=F(28,450),fill=muted); y+=40
flex.footer(im,bg,'Capcom · Alinea · Famitsu',"Sep 26, 2026",edge).save(OUT); print(OUT, d.textlength(header,font=F(96,800)))
