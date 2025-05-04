import streamlit as st
from PIL import Image, ImageDraw
import io, random, json, base64

# ─── Inline & blur the background image ────────────────────────────────────
def _inline_bg(path, blur_px=8, darken=0.7):
    try:
        data = open(path, "rb").read()
        b64  = base64.b64encode(data).decode()
        st.markdown(
            f"""
            <style>
              .stApp::before {{
                content: "";
                position: fixed;
                top: 0; left: 0;
                width: 100%; height: 100%;
                background-image: url("data:image/png;base64,{b64}");
                background-size: cover;
                filter: blur({blur_px}px) brightness({darken});
                z-index: -1;
              }}
              .block-container, .sidebar-content {{
                background: transparent !important;
              }}
            </style>
            """,
            unsafe_allow_html=True,
        )
    except FileNotFoundError:
        pass

_inline_bg("main_splash_rivers.png", blur_px=8, darken=0.8)

# ─── Embed sidebar logo via Base64 ─────────────────────────────────────────
def _sidebar_logo(path, width=120):
    try:
        data = open(path, "rb").read()
        b64  = base64.b64encode(data).decode()
        st.sidebar.markdown(
            f"<img src='data:image/png;base64,{b64}' width='{width}'/>",
            unsafe_allow_html=True,
        )
    except FileNotFoundError:
        pass

_sidebar_logo("logo.png", 120)

# ─── Page config ───────────────────────────────────────────────────────────
st.set_page_config(page_title="Survev.io Skin Editor", layout="wide")

# ─── Utility & Pattern Helpers ─────────────────────────────────────────────
def random_color():
    return "#%06x" % random.randint(0,0xFFFFFF)

def make_linear_gradient(sz,c1,c2):
    img = Image.new("RGB",(1,sz)); d=ImageDraw.Draw(img)
    for y in range(sz):
        t=y/(sz-1)
        r=int((1-t)*int(c1[1:3],16)+t*int(c2[1:3],16))
        g=int((1-t)*int(c1[3:5],16)+t*int(c2[3:5],16))
        b=int((1-t)*int(c1[5:7],16)+t*int(c2[5:7],16))
        d.point((0,y),(r,g,b))
    return img.resize((sz,sz))

def make_radial_gradient(sz,c1,c2):
    img=Image.new("RGB",(sz,sz)); d=ImageDraw.Draw(img)
    cx=cy=sz//2; maxr=(2**0.5)*(sz/2)
    for y in range(sz):
        for x in range(sz):
            dn=((x-cx)**2+(y-cy)**2)**0.5/maxr
            t=min(dn,1)
            r=int((1-t)*int(c1[1:3],16)+t*int(c2[1:3],16))
            g=int((1-t)*int(c1[3:5],16)+t*int(c2[3:5],16))
            b=int((1-t)*int(c1[5:7],16)+t*int(c2[5:7],16))
            d.point((x,y),(r,g,b))
    return img

def get_fill_image(ftype,c1,c2,sz):
    if ftype=="Solid":  return Image.new("RGB",(sz,sz),c1)
    if ftype=="Linear": return make_linear_gradient(sz,c1,c2)
    return make_radial_gradient(sz,c1,c2)

def make_stripes(sz,col,w):
    p=Image.new("RGBA",(sz,sz),(0,0,0,0)); d=ImageDraw.Draw(p)
    for x in range(0,sz,w*2): d.rectangle([x,0,x+w,sz],fill=col)
    return p

def make_spots(sz,col,dr,sp):
    p=Image.new("RGBA",(sz,sz),(0,0,0,0)); d=ImageDraw.Draw(p)
    for y in range(0,sz,sp):
        for x in range(0,sz,sp):
            d.ellipse([x,y,x+dr,y+dr],fill=col)
    return p

def make_diag(sz,col,w):
    p=Image.new("RGBA",(sz,sz),(0,0,0,0)); d=ImageDraw.Draw(p)
    for x in range(-sz,sz,w*2): d.line([(x,sz),(x+sz,0)],fill=col,width=w)
    return p

def make_check(sz,col,b):
    p=Image.new("RGBA",(sz,sz),(0,0,0,0)); d=ImageDraw.Draw(p)
    for y in range(0,sz,b):
        for x in range(0,sz,b):
            if ((x//b+y//b)%2)==0: d.rectangle([x,y,x+b,y+b],fill=col)
    return p

# ─── Sidebar Controls & Randomizer ─────────────────────────────────────────
randomize = st.sidebar.button("🎲 Randomize Skin")
if randomize:
    for name in ["Backpack","Body","Hands"]:
        st.session_state[f"{name}_fill"]     = random.choice(["Solid","Linear","Radial"])
        st.session_state[f"{name}_c1"]       = random_color()
        st.session_state[f"{name}_c2"]       = random_color()
        st.session_state[f"{name}_pat"]      = random.choice(
            ["None","Stripes","Spots","Diagonal","Checker","Custom"]
        )
        st.session_state[f"{name}_pc"]      = random_color()
        st.session_state[f"{name}_sw"]      = random.randint(5,50)
        st.session_state[f"{name}_dr"]      = random.randint(5,30)
        st.session_state[f"{name}_sp"]      = random.randint(20,100)
        st.session_state[f"{name}_dw"]      = random.randint(5,50)
        st.session_state[f"{name}_bl"]      = random.randint(20,80)
        st.session_state[f"{name}_alpha"]   = round(random.random(),2)

def part_ui(name, def1, def2):
    st.sidebar.header(name)
    f = st.sidebar.selectbox(f"{name} fill", ["Solid","Linear","Radial"], key=f"{name}_fill")
    c1 = st.sidebar.color_picker(f"{name} primary", def1, key=f"{name}_c1")
    c2 = c1 if f=="Solid" else st.sidebar.color_picker(f"{name} secondary", def2, key=f"{name}_c2")
    p = st.sidebar.selectbox(f"{name} pattern", ["None","Stripes","Spots","Diagonal","Checker","Custom"], key=f"{name}_pat")
    pc=sw=dr=sp=dw=bl=up=None
    if p=="Stripes":
        pc = st.sidebar.color_picker("Stripe col", def2, key=f"{name}_pc")
        sw = st.sidebar.slider("Stripe w", 1,100,20, key=f"{name}_sw")
    if p=="Spots":
        pc = st.sidebar.color_picker("Spot col", def2, key=f"{name}_pc")
        dr = st.sidebar.slider("Dot r", 1,50,15, key=f"{name}_dr")
        sp = st.sidebar.slider("Spacing",5,200,60, key=f"{name}_sp")
    if p=="Diagonal":
        pc = st.sidebar.color_picker("Diag col", def2, key=f"{name}_pc")
        dw = st.sidebar.slider("Diag w",1,100,20, key=f"{name}_dw")
    if p=="Checker":
        pc = st.sidebar.color_picker("Check col", def2, key=f"{name}_pc")
        bl = st.sidebar.slider("Block",5,200,50, key=f"{name}_bl")
    if p=="Custom":
        up = st.sidebar.file_uploader("Tile PNG", type="png", key=f"{name}_up")
    alpha = st.sidebar.slider("Opacity", 0.0,1.0,1.0, key=f"{name}_alpha")
    return f,c1,c2,p,pc,sw,dr,sp,dw,bl,up,alpha

bp = part_ui("Backpack","#A0522D","#8B4513")
bd = part_ui("Body",    "#FFD39F","#FFC071")
hd = part_ui("Hands",   "#A0522D","#8B4513")

oc = st.sidebar.color_picker("Outline color", "#000000")
ow = st.sidebar.slider("Outline width", 0,50,10)
by = st.sidebar.slider("Backpack Y offset",-300,300,-150)
hx = st.sidebar.slider("Hands X offset",0,300,180)
hy = st.sidebar.slider("Hands Y offset",0,300,220)
bg_file = st.sidebar.file_uploader("Optional BG (PNG)", type="png")

# ─── Build Canvas ──────────────────────────────────────────────────────────
# load bg underlay
bg_img = None
if bg_file:
    bg_img = Image.open(bg_file).convert("RGBA").resize((1024,1024), Image.Resampling.LANCZOS)

canvas = Image.new("RGBA",(1024,1024),(0,0,0,0))
for data, center, r in [
    (bp, (512,512+by),    240),
    (bd, (512,512),       280),
    (hd, (512-hx,512+hy), 100),
    (hd, (512+hx,512+hy), 100),
]:
    f,c1,c2,p,pc,sw,dr,sp,dw,bl,up,alpha = data
    fill_img = get_fill_image(f,c1,c2,2*r).convert("RGBA")
    # pattern
    pattern=None
    if   p=="Stripes":  pattern=make_stripes(2*r,pc,sw)
    elif p=="Spots":    pattern=make_spots(2*r,pc,dr,sp)
    elif p=="Diagonal": pattern=make_diag(2*r,pc,dw)
    elif p=="Checker":  pattern=make_check(2*r,pc,bl)
    elif p=="Custom" and up:
        tile=Image.open(up).convert("RGBA")
        ow_t,oh_t=tile.size
        nw=max(1,int(2*r*0.2)); nh=int(nw*oh_t/ow_t)
        small=tile.resize((nw,nh),Image.Resampling.LANCZOS)
        pattern=Image.new("RGBA",(2*r,2*r),(0,0,0,0))
        for yy in range(0,2*r,nh):
            for xx in range(0,2*r,nw):
                pattern.paste(small,(xx,yy),small)
    if pattern:
        am = pattern.split()[3].point(lambda px: int(px*alpha))
        pattern.putalpha(am)
        fill_img = Image.alpha_composite(fill_img,pattern)
    # mask & paste
    mask=Image.new("L",(2*r,2*r),0)
    ImageDraw.Draw(mask).ellipse((0,0,2*r,2*r),fill=255)
    canvas.paste(fill_img,(center[0]-r,center[1]-r),mask)
    ImageDraw.Draw(canvas).ellipse((center[0]-r,center[1]-r,center[0]+r,center[1]+r), outline=oc,width=ow)

if bg_img:
    canvas = Image.alpha_composite(bg_img,canvas)

# ─── Preview & Export ──────────────────────────────────────────────────────
st.subheader("Preview")
ps = st.selectbox("Preview size",[256,320,512], index=1)
st.image(canvas.resize((ps,ps),Image.Resampling.LANCZOS), use_container_width=False)

col1,col2 = st.columns([1,1])
with col1:
    res = st.selectbox("Resolution",[256,512,1024],index=1)
    fmt = st.selectbox("Format",["PNG","JPEG","SVG"],index=0)
    out = canvas.resize((res,res),Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    if fmt=="JPEG":
        out.convert("RGB").save(buf,"JPEG"); mime="image/jpeg"
    else:
        out.save(buf,"PNG");    mime="image/png"
    buf.seek(0)
    st.download_button("Download Skin", data=buf, file_name=f"skin.{fmt.lower()}", mime=mime)
with col2:
    cfg = {}
    for name, data in [("Backpack",bp),("Body",bd),("Hands",hd)]:
        f,c1,c2,p,pc,sw,dr,sp,dw,bl,up,alpha = data
        cfg[name] = {"fill":f,"c1":c1,"c2":c2,"pattern":p,
                     "pattern_col":pc,"stripe":sw,"dot":dr,
                     "spacing":sp,"diag":dw,"block":bl,"opacity":alpha}
    cfg["outline"] = {"color":oc,"width":ow}
    cfg["offsets"] = {"by":by,"hx":hx,"hy":hy}
    json_str = json.dumps(cfg, indent=2)
    st.download_button("Download config (JSON)", data=json_str,
                       file_name="skin_config.json", mime="application/json")
