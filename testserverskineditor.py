import streamlit as st
from PIL import Image, ImageDraw
import io, random, json

# ─── Page Config & Branding ────────────────────────────────────────────────
st.set_page_config(page_title="Survev.io Skin Editor", layout="wide")

# Favicon (served from /static/)
st.markdown(
    "<link rel='icon' href='/static/logo-surviv.png' />",
    unsafe_allow_html=True
)
# Sidebar logo via HTML <img>
st.sidebar.markdown(
    "<img src='/static/logo-surviv.png' width='120' />",
    unsafe_allow_html=True
)

# Blurred background
st.markdown(
    """
    <style>
      .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background: url('/static/main_splash_rivers.png') center/cover no-repeat;
        filter: blur(8px) brightness(0.7);
        z-index: -1;
      }
      .block-container, .sidebar-content {
        background-color: rgba(255,255,255,0.8) !important;
        border-radius: 8px;
        padding: 1rem;
      }
    </style>
    """,
    unsafe_allow_html=True
)

# Title
st.title("🎨 Survev.io Skin Editor")
st.write("Use the sidebar to configure or randomize your skin, then preview and export.")

# ─── Utility Functions ──────────────────────────────────────────────────────
def random_color():
    return "#%06x" % random.randint(0, 0xFFFFFF)

# Gradient generators
from functools import lru_cache
@lru_cache(maxsize=None)
def make_linear_gradient(sz, c1, c2):
    base = Image.new('RGB', (1, sz))
    draw = ImageDraw.Draw(base)
    for y in range(sz):
        t = y/(sz-1)
        r = int((1-t)*int(c1[1:3],16) + t*int(c2[1:3],16))
        g = int((1-t)*int(c1[3:5],16) + t*int(c2[3:5],16))
        b = int((1-t)*int(c1[5:7],16) + t*int(c2[5:7],16))
        draw.point((0,y), (r,g,b))
    return base.resize((sz,sz))

@lru_cache(maxsize=None)
def make_radial_gradient(sz, c1, c2):
    img = Image.new('RGB', (sz, sz))
    draw = ImageDraw.Draw(img)
    cx = cy = sz//2
    maxr = (2**0.5)*(sz/2)
    for y in range(sz):
        for x in range(sz):
            d = ((x-cx)**2 + (y-cy)**2)**0.5 / maxr
            t = min(d,1)
            r = int((1-t)*int(c1[1:3],16) + t*int(c2[1:3],16))
            g = int((1-t)*int(c1[3:5],16) + t*int(c2[3:5],16))
            b = int((1-t)*int(c1[5:7],16) + t*int(c2[5:7],16))
            draw.point((x,y), (r,g,b))
    return img

def get_fill_image(ftype, c1, c2, sz):
    if ftype=='Solid': return Image.new('RGB', (sz,sz), c1)
    if ftype=='Linear': return make_linear_gradient(sz, c1, c2)
    return make_radial_gradient(sz, c1, c2)

# Pattern generators
def make_stripes(sz, col, w):
    pat = Image.new('RGBA',(sz,sz),(0,0,0,0))
    draw = ImageDraw.Draw(pat)
    for x in range(0, sz, w*2): draw.rectangle([x,0,x+w,sz], fill=col)
    return pat

def make_spots(sz, col, r, sp):
    pat = Image.new('RGBA',(sz,sz),(0,0,0,0))
    draw = ImageDraw.Draw(pat)
    for y in range(0, sz, sp):
        for x in range(0, sz, sp): draw.ellipse([x,y,x+r,y+r], fill=col)
    return pat

def make_diag(sz, col, w):
    pat = Image.new('RGBA',(sz,sz),(0,0,0,0))
    draw = ImageDraw.Draw(pat)
    for x in range(-sz, sz, w*2): draw.line([(x,sz),(x+sz,0)], fill=col, width=w)
    return pat

def make_check(sz, col, b):
    pat = Image.new('RGBA',(sz,sz),(0,0,0,0))
    draw = ImageDraw.Draw(pat)
    for y in range(0, sz, b):
        for x in range(0, sz, b):
            if ((x//b + y//b)%2)==0: draw.rectangle([x,y,x+b,y+b], fill=col)
    return pat

# ─── Sidebar: Controls & Randomizer ──────────────────────────────────────────
if st.sidebar.button("🎲 Randomize Skin"):
    for nm,def1,def2 in [('Backpack','#A0522D','#8B4513'),('Body','#FFD39F','#FFC071'),('Hands','#A0522D','#8B4513')]:
        st.session_state[f"{nm}_fill"] = random.choice(['Solid','Linear','Radial'])
        st.session_state[f"{nm}_c1"]   = random_color()
        st.session_state[f"{nm}_c2"]   = random_color()
        st.session_state[f"{nm}_pat"]  = random.choice(['None','Stripes','Spots','Diagonal','Checker','Custom'])
        st.session_state[f"{nm}_pc"]   = random_color()
        st.session_state[f"{nm}_sw"]   = random.randint(5,50)
        st.session_state[f"{nm}_dr"]   = random.randint(5,30)
        st.session_state[f"{nm}_sp"]   = random.randint(20,100)
        st.session_state[f"{nm}_dw"]   = random.randint(5,50)
        st.session_state[f"{nm}_bl"]   = random.randint(20,80)
        st.session_state[f"{nm}_alpha"] = round(random.random(),2)

st.sidebar.header('Skin Parts')
parts=[]
for name,def1,def2 in [('Backpack','#A0522D','#8B4513'),('Body','#FFD39F','#FFC071'),('Hands','#A0522D','#8B4513')]:
    f = st.sidebar.selectbox(f'{name} fill',['Solid','Linear','Radial'], key=f'{name}_fill')
    c1=st.sidebar.color_picker(f'{name} primary', def1, key=f'{name}_c1')
    c2=c1 if f=='Solid' else st.sidebar.color_picker(f'{name} secondary', def2, key=f'{name}_c2')
    p = st.sidebar.selectbox(f'{name} pattern',['None','Stripes','Spots','Diagonal','Checker','Custom'], key=f'{name}_pat')
    pc=sw=dr=sp=dw=bl=up=None
    if p=='Stripes': pc=st.sidebar.color_picker('Stripe color',def2, key=f'{name}_pc'); sw=st.sidebar.slider('Stripe w',1,100,20,key=f'{name}_sw')
    if p=='Spots': pc=st.sidebar.color_picker('Spot color',def2, key=f'{name}_pc'); dr=st.sidebar.slider('Dot r',1,50,15,key=f'{name}_dr'); sp=st.sidebar.slider('Spacing',5,200,60,key=f'{name}_sp')
    if p=='Diagonal': pc=st.sidebar.color_picker('Diag color',def2, key=f'{name}_pc'); dw=st.sidebar.slider('Diag w',1,100,20,key=f'{name}_dw')
    if p=='Checker': pc=st.sidebar.color_picker('Check col',def2, key=f'{name}_pc'); bl=st.sidebar.slider('Block sz',5,200,50,key=f'{name}_bl')
    if p=='Custom': up=st.sidebar.file_uploader('Tile PNG', type='png', key=f'{name}_up')
    alpha=st.sidebar.slider('Pattern op',0.0,1.0,1.0,key=f'{name}_alpha')
    parts.append((name,f,c1,c2,p,pc,sw,dr,sp,dw,bl,up,alpha))
oc=st.sidebar.color_picker('Outline color','#000000')
ow=st.sidebar.slider('Outline width',0,50,10)
by=st.sidebar.slider('Backpack Y offset',-300,300,-150)
hx=st.sidebar.slider('Hands X offset',0,300,180)
hy=st.sidebar.slider('Hands Y offset',0,300,220)
bg_file=st.sidebar.file_uploader('Background (PNG)', type='png')

# ─── Build Canvas ───────────────────────────────────────────────────────────
bg_img=None
if bg_file:
    bg_img=Image.open(bg_file).convert('RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
canvas=Image.new('RGBA',(1024,1024),(0,0,0,0))
for name,f,c1,c2,p,pc,sw,dr,sp,dw,bl,up,alpha in parts:
    # Determine radius
    if name == 'Backpack':
        r = 240
    elif name == 'Body':
        r = 280
    else:
        r = 100
        # Determine centers
    if name == 'Backpack':
        centers = [(512, 512 + by)]
    elif name == 'Body':
        centers = [(512, 512)]
    else:
        centers = [(512 - hx, 512 + hy), (512 + hx, 512 + hy)]

    # Generate base fill image
    fill_img = get_fill_image(f, c1, c2, 2*r).convert('RGBA')(f,c1,c2,2*r).convert('RGBA')
    pattern=None
    if p=='Stripes':  pattern=make_stripes(2*r,pc,sw)
    elif p=='Spots':  pattern=make_spots(2*r,pc,dr,sp)
    elif p=='Diagonal':pattern=make_diag(2*r,pc,dw)
    elif p=='Checker': pattern=make_check(2*r,pc,bl)
    elif p=='Custom' and up:
        tile=Image.open(up).convert('RGBA')
        ow,oh=tile.size; nw=int(2*r*0.2); nh=int(nw*oh/ow)
        small=tile.resize((nw,nh),Image.Resampling.LANCZOS)
        pattern=Image.new('RGBA',(2*r,2*r),(0,0,0,0))
        for yy in range(0,2*r,nh):
            for xx in range(0,2*r,nw): pattern.paste(small,(xx,yy),small)
    if pattern:
        m=pattern.split()[3].point(lambda px:int(px*alpha))
        pattern.putalpha(m)
        fill_img=Image.alpha_composite(fill_img,pattern)
    for cx,cy in centers:
        mask=Image.new('L',(2*r,2*r),0);md=ImageDraw.Draw(mask);md.ellipse((0,0,2*r,2*r),255)
        canvas.paste(fill_img,(cx-r,cy-r),mask)
        ImageDraw.Draw(canvas).ellipse((cx-r,cy-r,cx+r,cy+r),outline=oc,width=ow)
if bg_img:canvas=Image.alpha_composite(bg_img,canvas)

# ─── Tabs: Editor / Preview / Export ─────────────────────────────────────────
tab1,tab2,tab3=st.tabs(['Editor','Preview','Export'])

with tab1:
    st.write('### Editor')
    st.write('Use the sidebar to tweak colors, patterns & offsets.')

with tab2:
    st.write('### Preview')
    st.image(canvas.resize((256,256),Image.Resampling.LANCZOS))

with tab3:
    st.write('### Export')
    c1,c2,c3=st.columns([1,1,2])
    with c1: res=st.selectbox('Resolution',[128,256,512,1024],index=1)
    with c2: fmt=st.selectbox('Format',['PNG','JPEG','SVG'])
    with c3:
        buf=io.BytesIO()
        out=canvas.resize((res,res),Image.Resampling.LANCZOS)
        mime='image/png'
        if fmt=='JPEG': out.convert('RGB').save(buf,'JPEG');mime='image/jpeg'
        else: out.save(buf,'PNG')
        buf.seek(0)
        btn1,btn2=st.columns(2)
        btn1.download_button('Skin',data=buf,file_name=f'skin.{fmt.lower()}',mime=mime)
        cfg={name:{'fill':f,'c1':c1,'c2':c2,'pattern':p,'pattern_col':pc,'sw':sw,'dr':dr,'sp':sp,'dw':dw,'bl':bl,'alpha':alpha}
            for name,f,c1,c2,p,pc,sw,dr,sp,dw,bl,up,alpha in parts}
        cfg['outline']={'color':oc,'width':ow};cfg['offsets']={'by':by,'hx':hx,'hy':hy}
        btn2.download_button('Config (JSON)',data=json.dumps(cfg,indent=2),file_name='config.json',mime='application/json')
