import streamlit as st
from PIL import Image, ImageDraw
import io, random, json, base64

# ─── Page Config & Branding ────────────────────────────────────────────────
st.set_page_config(page_title="Survev.io Skin Editor", layout="wide")

# Favicon + Sidebar logo
try:
    logo_bytes = open(".streamlit/static/logo-surviv.png","rb").read()
    logo_b64   = base64.b64encode(logo_bytes).decode()
    st.markdown(
        f"<link rel='icon' href='data:image/png;base64,{logo_b64}' />",
        unsafe_allow_html=True
    )
    st.sidebar.image(".streamlit/static/logo-surviv.png", use_column_width=True)
except FileNotFoundError:
    pass

# Blurred background (only the backdrop, not the UI controls)
try:
    st.markdown(
        """
        <style>
          .stApp::before {
            content: "";
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: url('/static/main_splash_rivers.png') no-repeat center;
            background-size: cover;
            filter: blur(8px) brightness(0.8);
            z-index: -1;
          }
          .block-container, .sidebar-content {
            background: rgba(255,255,255,0.85) !important;
            border-radius: 10px;
            padding: 1rem;
          }
        </style>
        """,
        unsafe_allow_html=True
    )
except FileNotFoundError:
    pass

st.title("🎨 Survev.io Skin Editor")
st.write("Use tabs below to configure, preview, or export your skin.")

# ─── Utility & Pattern Helpers ─────────────────────────────────────────────
def random_color(): return "#%06x" % random.randint(0,0xFFFFFF)

def make_linear_gradient(sz,c1,c2):
    img=Image.new("RGB",(1,sz));d=ImageDraw.Draw(img)
    for y in range(sz):
        t=y/(sz-1)
        r=int((1-t)*int(c1[1:3],16)+t*int(c2[1:3],16))
        g=int((1-t)*int(c1[3:5],16)+t*int(c2[3:5],16))
        b=int((1-t)*int(c1[5:7],16)+t*int(c2[5:7],16))
        d.point((0,y),(r,g,b))
    return img.resize((sz,sz))

def make_radial_gradient(sz,c1,c2):
    img=Image.new("RGB",(sz,sz));d=ImageDraw.Draw(img)
    cx=cy=sz//2;maxr=(2**0.5)*(sz/2)
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
    p=Image.new("RGBA",(sz,sz),(0,0,0,0));d=ImageDraw.Draw(p)
    for x in range(0,sz,w*2): d.rectangle([x,0,x+w,sz],fill=col)
    return p

def make_spots(sz,col,dr,sp):
    p=Image.new("RGBA",(sz,sz),(0,0,0,0));d=ImageDraw.Draw(p)
    for y in range(0,sz,sp):
      for x in range(0,sz,sp): d.ellipse([x,y,x+dr,y+dr],fill=col)
    return p

def make_diag(sz,col,w):
    p=Image.new("RGBA",(sz,sz),(0,0,0,0));d=ImageDraw.Draw(p)
    for x in range(-sz,sz,w*2): d.line([(x,sz),(x+sz,0)],fill=col,width=w)
    return p

def make_check(sz,col,b):
    p=Image.new("RGBA",(sz,sz),(0,0,0,0));d=ImageDraw.Draw(p)
    for y in range(0,sz,b):
      for x in range(0,sz,b):
        if ((x//b+y//b)%2)==0: d.rectangle([x,y,x+b,y+b],fill=col)
    return p

# ─── Sidebar Form for Controls ──────────────────────────────────────────────
with st.sidebar.form("controls"):
    parts=[]

    for name,def1,def2 in [
        ("Backpack","#A0522D","#8B4513"),
        ("Body"    ,"#FFD39F","#FFC071"),
        ("Hands"   ,"#A0522D","#8B4513")
    ]:
        f=st.selectbox(f"{name} fill",["Solid","Linear","Radial"],key=f"{name}_fill")
        c1=st.color_picker(f"{name} primary",def1,key=f"{name}_c1")
        c2=c1 if f=="Solid" else st.color_picker(f"{name} secondary",def2,key=f"{name}_c2")
        p=st.selectbox(f"{name} pattern",["None","Stripes","Spots","Diagonal","Checker","Custom"],key=f"{name}_pat")

        pc=sw=dr=sp=dw=bl=up=None
        if p=="Stripes":
            pc=st.color_picker(f"{name} stripe col",def2,key=f"{name}_pc")
            sw=st.slider(f"{name} stripe w",1,100,20,key=f"{name}_sw")
        if p=="Spots":
            pc=st.color_picker(f"{name} spot col",def2,key=f"{name}_pc")
            dr=st.slider(f"{name} dot r",1,50,15,key=f"{name}_dr")
            sp=st.slider(f"{name} spacing",5,200,60,key=f"{name}_sp")
        if p=="Diagonal":
            pc=st.color_picker(f"{name} diag col",def2,key=f"{name}_pc")
            dw=st.slider(f"{name} diag w",1,100,20,key=f"{name}_dw")
        if p=="Checker":
            pc=st.color_picker(f"{name} check col",def2,key=f"{name}_pc")
            bl=st.slider(f"{name} block"   ,5,200,50,key=f"{name}_bl")
        if p=="Custom":
            up=st.file_uploader(f"{name} tile PNG",type="png",key=f"{name}_up")

        alpha=st.slider(f"{name} opacity",0.0,1.0,1.0,key=f"{name}_alpha")
        parts.append((name,f,c1,c2,p,pc,sw,dr,sp,dw,bl,up,alpha))

    oc = st.color_picker("Outline color","#000000")
    ow = st.slider("Outline width",0,50,10)
    by = st.slider("Backpack Y offset",-300,300,-150)
    hx = st.slider("Hands X offset",0,300,180)
    hy = st.slider("Hands Y offset",0,300,220)

    bg_file = st.file_uploader("Background (PNG)",type="png")
    submitted = st.form_submit_button("Apply")

# ─── Build Canvas Upfront ───────────────────────────────────────────────────
# Load BG if any
bg_img=None
if bg_file:
    bg_img=Image.open(bg_file).convert("RGBA").resize((1024,1024),Image.Resampling.LANCZOS)

# Compose all parts
canvas=Image.new("RGBA",(1024,1024),(0,0,0,0))
for name,f,c1,c2,p,pc,sw,dr,sp,dw,bl,up,alpha in parts:
    # choose radius & center
    r = 240 if name=="Backpack" else (280 if name=="Body" else 100)
    cx,cy = (512,512+by) if name=="Backpack" else ((512,512) if name=="Body" else (512-hx,512+hy))
    # base fill
    fill_img=get_fill_image(f,c1,c2,2*r).convert("RGBA")
    # build pattern
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
    # overlay with opacity
    if pattern:
        a_mask=pattern.split()[3].point(lambda px:int(px*alpha))
        pattern.putalpha(a_mask)
        fill_img=Image.alpha_composite(fill_img,pattern)
    # mask & paste circle
    mask=Image.new("L",(2*r,2*r),0)
    ImageDraw.Draw(mask).ellipse((0,0,2*r,2*r),fill=255)
    canvas.paste(fill_img,(cx-r,cy-r),mask)
    # outline
    ImageDraw.Draw(canvas).ellipse(
        (cx-r,cy-r,cx+r,cy+r),outline=oc,width=ow
    )

# composite background under
if bg_img:
    canvas=Image.alpha_composite(bg_img,canvas)

# ─── Tabs: Editor / Preview / Export ────────────────────────────────────────
tabs = st.tabs(["Editor","Preview","Export"])

with tabs[1]:
    st.subheader("Live Preview")
    st.image(canvas.resize((256,256),Image.Resampling.LANCZOS), use_container_width=True)

with tabs[2]:
    col1,col2 = st.columns(2)
    with col1:
        st.write("**Download Skin**")
        res = st.selectbox("Resolution",[256,512,1024],index=1)
        fmt = st.selectbox("Format",["PNG","JPEG","SVG"])
        buf = io.BytesIO()
        out = canvas.resize((res,res),Image.Resampling.LANCZOS)
        if fmt=="JPEG":
            out.convert("RGB").save(buf,"JPEG"); mime="image/jpeg"
        else:
            out.save(buf,"PNG");    mime="image/png"
        buf.seek(0)
        st.download_button("Download",data=buf,file_name=f"skin.{fmt.lower()}",mime=mime)
    with col2:
        st.write("**Download Config (JSON)**")
        cfg = {
            name:{
                "fill":f,"c1":c1,"c2":c2,
                "pattern":p,"pattern_col":pc,
                "stripe":sw,"dot":dr,"spacing":sp,
                "diag":dw,"block":bl,"opacity":alpha
            } for name,f,c1,c2,p,pc,sw,dr,sp,dw,bl,up,alpha in parts
        }
        cfg["outline"] = {"color":oc,"width":ow}
        cfg["offsets"] = {"by":by,"hx":hx,"hy":hy}
        json_str = json.dumps(cfg,indent=2)
        st.download_button("Download JSON",data=json_str,file_name="config.json",mime="application/json")
