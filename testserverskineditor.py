import streamlit as st
from PIL import Image, ImageDraw
import io, random, json

# ─── Page config & Branding ────────────────────────────────────────────────
st.set_page_config(page_title="Survev.io Skin Editor", layout="wide")

# Sidebar logo served from top-level static folder
st.sidebar.image('/static/logo.png', width=120)

# Blurred fullscreen background via CSS from static folder
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
st.write("Use the sidebar (or the 🎲 Randomize button) to customize or auto‑generate a skin.")

# Utility: random hex color
def random_color():
    return "#%06x" % random.randint(0, 0xFFFFFF)

# ─── Gradient helpers ──────────────────────────────────────────────────────
def make_linear_gradient(size, c1, c2):
    base = Image.new("RGB", (1, size))
    draw = ImageDraw.Draw(base)
    for y in range(size):
        t = y / (size - 1)
        r = int((1-t)*int(c1[1:3],16) + t*int(c2[1:3],16))
        g = int((1-t)*int(c1[3:5],16) + t*int(c2[3:5],16))
        b = int((1-t)*int(c1[5:7],16) + t*int(c2[5:7],16))
        draw.point((0,y), fill=(r,g,b))
    return base.resize((size, size))

def make_radial_gradient(size, c1, c2):
    grad = Image.new("RGB", (size, size))
    draw = ImageDraw.Draw(grad)
    cx, cy = size//2, size//2
    maxr = (2**0.5)*(size/2)
    for y in range(size):
        for x in range(size):
            d = ((x-cx)**2 + (y-cy)**2)**0.5 / maxr
            t = min(d,1.0)
            r = int((1-t)*int(c1[1:3],16) + t*int(c2[1:3],16))
            g = int((1-t)*int(c1[3:5],16) + t*int(c2[3:5],16))
            b = int((1-t)*int(c1[5:7],16) + t*int(c2[5:7],16))
            draw.point((x,y), fill=(r,g,b))
    return grad

def get_fill_image(ftype, c1, c2, size):
    if ftype == "Solid":
        return Image.new("RGB", (size, size), c1)
    if ftype == "Linear":
        return make_linear_gradient(size, c1, c2)
    return make_radial_gradient(size, c1, c2)

# ─── Pattern generators ────────────────────────────────────────────────────
def make_stripes(size, color, stripe_w):
    pat = Image.new("RGBA", (size,size), (0,0,0,0))
    d = ImageDraw.Draw(pat)
    for x in range(0, size, stripe_w*2):
        d.rectangle([x,0,x+stripe_w,size], fill=color)
    return pat

def make_spots(size, color, dot_r, spacing):
    pat = Image.new("RGBA", (size,size), (0,0,0,0))
    d = ImageDraw.Draw(pat)
    for y in range(0, size, spacing):
        for x in range(0, size, spacing):
            d.ellipse([x,y,x+dot_r,y+dot_r], fill=color)
    return pat

def make_diagonal_stripes(size, color, stripe_w):
    pat = Image.new("RGBA", (size,size), (0,0,0,0))
    d = ImageDraw.Draw(pat)
    for x in range(-size, size, stripe_w*2):
        d.line([(x,size),(x+size,0)], fill=color, width=stripe_w)
    return pat

def make_checkerboard(size, color, block):
    pat = Image.new("RGBA", (size,size), (0,0,0,0))
    d = ImageDraw.Draw(pat)
    for y in range(0, size, block):
        for x in range(0, size, block):
            if ((x//block)+(y//block))%2 == 0:
                d.rectangle([x,y,x+block,y+block], fill=color)
    return pat

# ─── Sidebar & Randomize ───────────────────────────────────────────────────
randomize = st.sidebar.button("🎲 Randomize Skin")
def init_random():
    if randomize:
        for name in ["Backpack","Body","Hands"]:
            st.session_state[f"{name}_fill"]    = random.choice(["Solid","Linear","Radial"])
            st.session_state[f"{name}_c1"]      = random_color()
            st.session_state[f"{name}_c2"]      = random_color()
            st.session_state[f"{name}_pat"]     = random.choice(["None","Stripes","Spots","Diagonal Stripes","Checkerboard","Custom"])
            st.session_state[f"{name}_pc"]      = random_color()
            st.session_state[f"{name}_stripe_w"] = random.randint(5,50)
            st.session_state[f"{name}_dot_r"]    = random.randint(5,30)
            st.session_state[f"{name}_spacing"]  = random.randint(20,100)
            st.session_state[f"{name}_diag_w"]   = random.randint(5,50)
            st.session_state[f"{name}_block"]    = random.randint(20,80)
            st.session_state[f"{name}_alpha"]    = round(random.random(),2)
init_random()

with st.sidebar:
    def part_ui(name, def1, def2):
        st.header(name)
        ftype = st.selectbox("Fill type", ["Solid","Linear","Radial"], key=f"{name}_fill")
        c1 = st.color_picker("Primary color", def1, key=f"{name}_c1")
        c2 = c1 if ftype == "Solid" else st.color_picker("Secondary color", def2, key=f"{name}_c2")
        pat = st.selectbox("Pattern", ["None","Stripes","Spots","Diagonal Stripes","Checkerboard","Custom"], key=f"{name}_pat")
        pc = sw = dr = sp = dw = bl = up = alpha = None
        if pat == "Stripes":
            pc    = st.color_picker("Stripe color", def2, key=f"{name}_pc")
            sw    = st.slider("Stripe width", 1,100, st.session_state.get(f"{name}_stripe_w",20), key=f"{name}_stripe_w")
            alpha = st.slider("Pattern opacity", 0.0,1.0, st.session_state.get(f"{name}_alpha",1.0), key=f"{name}_alpha")
        elif pat == "Spots":
            pc    = st.color_picker("Spot color", def2, key=f"{name}_pc")
            dr    = st.slider("Dot radius", 1,50, st.session_state.get(f"{name}_dot_r",15), key=f"{name}_dot_r")
            sp    = st.slider("Spacing", 5,200, st.session_state.get(f"{name}_spacing",60), key=f"{name}_spacing")
            alpha = st.slider("Pattern opacity", 0.0,1.0, st.session_state.get(f"{name}_alpha",1.0), key=f"{name}_alpha")
        elif pat == "Diagonal Stripes":
            pc    = st.color_picker("Diag color", def2, key=f"{name}_pc")
            dw    = st.slider("Diag width", 1,100, st.session_state.get(f"{name}_diag_w",20), key=f"{name}_diag_w")
            alpha = st.slider("Pattern opacity", 0.0,1.0, st.session_state.get(f"{name}_alpha",1.0), key=f"{name}_alpha")
        elif pat == "Checkerboard":
            pc    = st.color_picker("Checker color", def2, key=f"{name}_pc")
            bl    = st.slider("Block size", 5,200, st.session_state.get(f"{name}_block",50), key=f"{name}_block")
            alpha = st.slider("Pattern opacity", 0.0,1.0, st.session_state.get(f"{name}_alpha",1.0), key=f"{name}_alpha")
        elif pat == "Custom":
            up    = st.file_uploader("Tile PNG", type="png", key=f"{name}_up")
            alpha = st.slider("Pattern opacity", 0.0,1.0, st.session_state.get(f"{name}_alpha",1.0), key=f"{name}_alpha")
        return ftype, c1, c2, pat, pc, sw, dr, sp, dw, bl, up, alpha
    bp_data = part_ui("Backpack", "#A0522D", "#8B4513"); st.markdown("---")
    bd_data = part_ui("Body",     "#FFD39F", "#FFC071"); st.markdown("---")
    hd_data = part_ui("Hands",    "#A0522D", "#8B4513"); st.markdown("---")
    oc = st.color_picker("Outline color", "#000000")
    ow = st.slider("Outline width", 0,50,10)
    by = st.slider("Backpack Y offset", -300,300,-150)
    hx = st.slider("Hands X offset", 0,300,180)
    hy = st.slider("Hands Y offset", 0,300,220)
    bg_file = st.file_uploader("Optional background (PNG)", type="png")

# Build canvas
bg_img = None
if bg_file:
    bg_img = Image.open(bg_file).convert("RGBA").resize((1024,1024), Image.Resampling.LANCZOS)
canvas = Image.new("RGBA", (1024,1024), (0,0,0,0))
for data, center, r in [
    (bp_data, (512,512+by), 240),
    (bd_data, (512,512),     280),
    (hd_data, (512-hx,512+hy),100),
    (hd_data, (512+hx,512+hy),100)
]:
    ftype, c1, c2, pat, pc, sw, dr, sp, dw, bl, up, alpha = data
    fill_img = get_fill_image(ftype, c1, c2, 2*r).convert("RGBA")
    pattern = None
    if pat == "Stripes": pattern = make_stripes(2*r, pc, sw)
    elif pat == "Spots": pattern = make_spots(2*r, pc, dr, sp)
    elif pat == "Diagonal Stripes": pattern = make_diagonal_stripes(2*r, pc, dw)
    elif pat == "Checkerboard": pattern = make_checkerboard(2*r, pc, bl)
    elif pat == "Custom" and up:
        tile = Image.open(up).convert("RGBA")
        ow_t,oh_t = tile.size
        nw = max(1,int(2*r*0.2))
        nh = max(1,int(nw*oh_t/ow_t))
        small = tile.resize((nw,nh), Image.Resampling.LANCZOS)
        pattern = Image.new("RGBA", (2*r,2*r), (0,0,0,0))
        for yy in range(0,2*r,nh):
            for xx in range(0,2*r,nw): pattern.paste(small,(xx,yy),small)
    if pattern:
        mask = pattern.split()[3].point(lambda px: int(px*alpha))
        pattern.putalpha(mask)
        fill_img = Image.alpha_composite(fill_img, pattern)
    m = Image.new("L", (2*r,2*r), 0); md = ImageDraw.Draw(m); md.ellipse((0,0,2*r,2*r), fill=255)
    canvas.paste(fill_img, (center[0]-r,center[1]-r), m)
    ImageDraw.Draw(canvas).ellipse((center[0]-r,center[1]-r,center[0]+r,center[1]+r), outline=oc, width=ow)
if bg_img: canvas = Image.alpha_composite(bg_img, canvas)

# Preview & Export
st.subheader("Preview")
ps = st.selectbox("Preview size", [256,320,512], index=1)
st.image(canvas.resize((ps,ps),Image.Resampling.LANCZOS))
col1,col2 = st.columns(2)
with col1:
    res = st.selectbox("Resolution", [256,512,1024], index=1)
    fmt = st.selectbox("Format", ["PNG","JPEG","SVG"], index=0)
    out = canvas.resize((res,res),Image.Resampling.LANCZOS)
    buf = io.BytesIO(); mime='image/png'
    if fmt=='JPEG': out.convert('RGB').save(buf,'JPEG'); mime='image/jpeg'
    else: out.save(buf,'PNG')
    buf.seek(0)
    st.download_button("Download Skin", data=buf, file_name=f"skin.{fmt.lower()}", mime=mime)
with col2:
    cfg = {name: {'fill':ftype,'c1':c1,'c2':c2,'pattern':pat,'pattern_col':pc,'sw':sw,'dr':dr,'sp':sp,'dw':dw,'bl':bl,'alpha':alpha}
           for name,(ftype,c1,c2,pat,pc,sw,dr,sp,dw,bl,up,alpha) in zip(["Backpack","Body","Hands"],[bp_data,bd_data,hd_data])}
    cfg['outline']={'color':oc,'width':ow}
    cfg['offsets']={'by':by,'hx':hx,'hy':hy}
    st.download_button("Download config (JSON)", data=json.dumps(cfg, indent=2), file_name="skin_config.json", mime="application/json")
