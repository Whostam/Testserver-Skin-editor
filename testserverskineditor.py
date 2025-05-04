import streamlit as st
from PIL import Image, ImageDraw
import io, random, json

# ─── Page Config and Branding ───────────────────────────────────────────────
st.set_page_config(page_title="Survev.io Skin Editor", layout="wide")

# Sidebar logo served from top-level static folder
st.sidebar.markdown(
    "<img src='/static/logo.png' width='120' alt='Logo'/>",
    unsafe_allow_html=True
)

# Blurred full-screen background via CSS from static folder
st.markdown(
    """
    <style>
      .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0;
        width: 100vw; height: 100vh;
        background: url('/static/main_splash_rivers.png') center/cover no-repeat;
        filter: blur(8px) brightness(0.7);
        z-index: -1;
      }
      .block-container, .sidebar-content {
        background-color: transparent !important;
      }
    </style>
    """,
    unsafe_allow_html=True
)

# Title and instructions
st.title("🎨 Survev.io Skin Editor")
st.write("Use the sidebar or the 🎲 Randomize button to configure your skin and see the live preview below.")

# Utility: random color
def random_color():
    return "#%06x" % random.randint(0, 0xFFFFFF)

# ─── Gradient Helper Functions ──────────────────────────────────────────────
def make_linear_gradient(size, c1, c2):
    img = Image.new("RGB", (1, size))
    draw = ImageDraw.Draw(img)
    for y in range(size):
        t = y / float(size - 1)
        r = int((1-t)*int(c1[1:3],16) + t*int(c2[1:3],16))
        g = int((1-t)*int(c1[3:5],16) + t*int(c2[3:5],16))
        b = int((1-t)*int(c1[5:7],16) + t*int(c2[5:7],16))
        draw.point((0, y), (r, g, b))
    return img.resize((size, size))

def make_radial_gradient(size, c1, c2):
    img = Image.new("RGB", (size, size))
    draw = ImageDraw.Draw(img)
    cx = cy = size // 2
    maxr = (2**0.5) * (size/2)
    for x in range(size):
        for y in range(size):
            d = ((x-cx)**2 + (y-cy)**2)**0.5 / maxr
            t = min(d, 1)
            r = int((1-t)*int(c1[1:3],16) + t*int(c2[1:3],16))
            g = int((1-t)*int(c1[3:5],16) + t*int(c2[3:5],16))
            b = int((1-t)*int(c1[5:7],16) + t*int(c2[5:7],16))
            draw.point((x, y), (r, g, b))
    return img

def get_fill_image(ftype, c1, c2, size):
    if ftype == "Solid":
        return Image.new("RGB", (size, size), c1)
    if ftype == "Linear":
        return make_linear_gradient(size, c1, c2)
    return make_radial_gradient(size, c1, c2)

# ─── Pattern Generator Functions ────────────────────────────────────────────
def make_stripes(size, color, stripe_w):
    pat = Image.new("RGBA", (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(pat)
    for x in range(0, size, stripe_w*2):
        draw.rectangle([x, 0, x+stripe_w, size], fill=color)
    return pat

def make_spots(size, color, dot_r, spacing):
    pat = Image.new("RGBA", (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(pat)
    for y in range(0, size, spacing):
        for x in range(0, size, spacing):
            draw.ellipse([x, y, x+dot_r, y+dot_r], fill=color)
    return pat

def make_diagonal_stripes(size, color, stripe_w):
    pat = Image.new("RGBA", (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(pat)
    for x in range(-size, size, stripe_w*2):
        draw.line([(x, size), (x+size, 0)], fill=color, width=stripe_w)
    return pat

def make_checkerboard(size, color, block):
    pat = Image.new("RGBA", (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(pat)
    for y in range(0, size, block):
        for x in range(0, size, block):
            if (x//block + y//block) % 2 == 0:
                draw.rectangle([x, y, x+block, y+block], fill=color)
    return pat

# ─── Sidebar Controls & Randomizer ──────────────────────────────────────────
randomize = st.sidebar.button("🎲 Randomize Skin")
if randomize:
    for part in ["Backpack", "Body", "Hands"]:
        st.session_state[f"{part}_fill"] = random.choice(["Solid","Linear","Radial"])
        st.session_state[f"{part}_c1"] = random_color()
        st.session_state[f"{part}_c2"] = random_color()
        st.session_state[f"{part}_pat"] = random.choice(["None","Stripes","Spots","Diagonal","Checker","Custom"])
        st.session_state[f"{part}_pc"] = random_color()
        st.session_state[f"{part}_sw"] = random.randint(5,50)
        st.session_state[f"{part}_dr"] = random.randint(5,30)
        st.session_state[f"{part}_sp"] = random.randint(20,100)
        st.session_state[f"{part}_dw"] = random.randint(5,50)
        st.session_state[f"{part}_bl"] = random.randint(20,80)
        st.session_state[f"{part}_alpha"] = round(random.random(),2)

# Render part UI
with st.sidebar:
    def part_ui(name, c1_def, c2_def):
        fill = st.selectbox(f"{name} fill", ["Solid","Linear","Radial"], key=f"{name}_fill")
        c1 = st.color_picker(f"{name} primary", c1_def, key=f"{name}_c1")
        c2 = c1 if fill=="Solid" else st.color_picker(f"{name} secondary", c2_def, key=f"{name}_c2")
        pat = st.selectbox(f"{name} pattern", ["None","Stripes","Spots","Diagonal","Checker","Custom"], key=f"{name}_pat")
        pc=sw=dr=sp=dw=bl=up=None
        if pat=="Stripes": pc=st.color_picker("Stripe color",c2_def,key=f"{name}_pc"); sw=st.slider("Stripe w",1,100,20,key=f"{name}_sw")
        if pat=="Spots": pc=st.color_picker("Spot color",c2_def,key=f"{name}_pc"); dr=st.slider("Dot r",1,50,15,key=f"{name}_dr"); sp=st.slider("Spacing",5,200,60,key=f"{name}_sp")
        if pat=="Diagonal": pc=st.color_picker("Diag color",c2_def,key=f"{name}_pc"); dw=st.slider("Diag w",1,100,20,key=f"{name}_dw")
        if pat=="Checker": pc=st.color_picker("Check color",c2_def,key=f"{name}_pc"); bl=st.slider("Block sz",5,200,50,key=f"{name}_bl")
        if pat=="Custom": up=st.file_uploader(f"{name} tile PNG", type="png", key=f"{name}_up")
        alpha=st.slider("Opacity",0.0,1.0,1.0,key=f"{name}_alpha")
        return fill,c1,c2,pat,pc,sw,dr,sp,dw,bl,up,alpha
    bp = part_ui("Backpack","#A0522D","#8B4513"); st.markdown("---")
    bd = part_ui("Body","#FFD39F","#FFC071"); st.markdown("---")
    hd = part_ui("Hands","#A0522D","#8B4513")
    oc = st.color_picker("Outline color","#000000")
    ow = st.slider("Outline width",0,50,10)
    by = st.slider("Backpack Y offset",-300,300,-150)
    hx = st.slider("Hands X offset",0,300,180)
    hy = st.slider("Hands Y offset",0,300,220)
    bg_file = st.file_uploader("Background (PNG)", type="png")

# ─── Canvas Construction ───────────────────────────────────────────────────
bg_img=None
if bg_file:
    bg_img=Image.open(bg_file).convert("RGBA").resize((1024,1024),Image.Resampling.LANCZOS)
canvas=Image.new("RGBA",(1024,1024),(0,0,0,0))
for data, center, r in [(bp,(512,512+by),240),(bd,(512,512),280),(hd,(512-hx,512+hy),100),(hd,(512+hx,512+hy),100)]:
    fill,c1,c2,pat,pc,sw,dr,sp,dw,bl,up,alpha = data
    base=get_fill_image(fill,c1,c2,2*r).convert("RGBA")
    pattern=None
    if pat=="Stripes": pattern=make_stripes(2*r,pc,sw)
    elif pat=="Spots":   pattern=make_spots(2*r,pc,dr,sp)
    elif pat=="Diagonal":pattern=make_diagonal_stripes(2*r,pc,dw)
    elif pat=="Checker":pattern=make_checkerboard(2*r,pc,bl)
    elif pat=="Custom" and up:
        tile=Image.open(up).convert("RGBA"); ow_t,oh_t=tile.size; nw=int(2*r*0.2);nh=int(nw*oh_t/ow_t)
        small=tile.resize((nw,nh),Image.Resampling.LANCZOS)
        pattern=Image.new("RGBA",(2*r,2*r),(0,0,0,0))
        for yy in range(0,2*r,nh):
            for xx in range(0,2*r,nw):pattern.paste(small,(xx,yy),small)
    if pattern:
        mask=pattern.split()[3].point(lambda px:int(px*alpha)); pattern.putalpha(mask)
        base=Image.alpha_composite(base,pattern)
    m=Image.new("L",(2*r,2*r),0);ImageDraw.Draw(m).ellipse((0,0,2*r,2*r),fill=255)
    canvas.paste(base,(center[0]-r,center[1]-r),m)
    ImageDraw.Draw(canvas).ellipse((center[0]-r,center[1]-r,center[0]+r,center[1]+r),outline=oc,width=ow)
if bg_img:canvas=Image.alpha_composite(bg_img,canvas)

# ─── Preview & Export ──────────────────────────────────────────────────────
st.subheader("Preview")
ps=st.selectbox("Preview size",[256,320,512],index=1)
st.image(canvas.resize((ps,ps),Image.Resampling.LANCZOS))
col1,col2=st.columns(2)
with col1:
    res=st.selectbox("Resolution",[256,512,1024],index=1)
    fmt=st.selectbox("Format",["PNG","JPEG","SVG"],index=0)
    out=canvas.resize((res,res),Image.Resampling.LANCZOS)
    buf=io.BytesIO();mime='image/png'
    if fmt=='JPEG':out.convert('RGB').save(buf,'JPEG');mime='image/jpeg'
    else:out.save(buf,'PNG')
    buf.seek(0)
    st.download_button("Download Skin",data=buf,file_name=f"skin.{fmt.lower()}",mime=mime)
with col2:
    cfg={name:{'fill':ft,'c1':c1,'c2':c2,'pattern':pat,'pattern_col':pc,'sw':sw,'dr':dr,'sp':sp,'dw':dw,'bl':bl,'alpha':alpha}
          for name,(ft,c1,c2,pat,pc,sw,dr,sp,dw,bl,up,alpha) in zip(["Backpack","Body","Hands"],[bp,bd,hd])}
    cfg['outline']={'color':oc,'width':ow}
    cfg['offsets']={'by':by,'hx':hx,'hy':hy}
    st.download_button("Download Config",data=json.dumps(cfg,indent
