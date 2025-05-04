import streamlit as st
from PIL import Image, ImageDraw
import io, random, json, base64

# ─── Page Config & Branding ────────────────────────────────────────────────
st.set_page_config(page_title="Survev.io Skin Editor", layout="wide")
# Favicon and logo
logo_bytes = open('logo-surviv.png','rb').read()
logo_b64 = base64.b64encode(logo_bytes).decode()
st.markdown(
    f"<link rel='icon' href='data:image/png;base64,{logo_b64}' />",
    unsafe_allow_html=True
)
st.sidebar.image('logo-surviv.png', use_column_width=True)
# Blurred background via CSS
st.markdown(
    """
    <style>
      .stApp { background: url('main_splash_rivers.png') no-repeat center; background-size: cover; filter: blur(5px) brightness(0.7); }
      .block-container, .sidebar-content { filter: none; background: rgba(255,255,255,0.8); border-radius: 10px; padding: 1rem; }
    </style>
    """, unsafe_allow_html=True
)

st.title("🎨 Survev.io Skin Editor")
st.write("Use tabs below to configure, preview, or export your skin.")

# Utility: random color
def random_color(): return "#%06x" % random.randint(0,0xFFFFFF)

# ─── Helpers ────────────────────────────────────────────────────────────────
def make_linear_gradient(sz, c1, c2):
    img = Image.new('RGB', (1, sz))
    d = ImageDraw.Draw(img)
    for y in range(sz):
        t = y / (sz - 1)
        r = int((1-t)*int(c1[1:3],16) + t*int(c2[1:3],16))
        g = int((1-t)*int(c1[3:5],16) + t*int(c2[3:5],16))
        b = int((1-t)*int(c1[5:7],16) + t*int(c2[5:7],16))
        d.point((0,y), fill=(r,g,b))
    return img.resize((sz, sz))

def make_radial_gradient(sz, c1, c2):
    img = Image.new('RGB', (sz, sz))
    d = ImageDraw.Draw(img)
    cx, cy = sz//2, sz//2
    maxr = (2**0.5) * (sz/2)
    for y in range(sz):
        for x in range(sz):
            d_norm = ((x-cx)**2 + (y-cy)**2)**0.5 / maxr
            t = min(d_norm, 1.0)
            r = int((1-t)*int(c1[1:3],16) + t*int(c2[1:3],16))
            g = int((1-t)*int(c1[3:5],16) + t*int(c2[3:5],16))
            b = int((1-t)*int(c1[5:7],16) + t*int(c2[5:7],16))
            d.point((x,y), fill=(r,g,b))
    return img

def get_fill_image(ftype, c1, c2, sz):
    if ftype == "Solid":
        return Image.new("RGB", (sz, sz), c1)
    if ftype == "Linear":
        return make_linear_gradient(sz, c1, c2)
    return make_radial_gradient(sz, c1, c2)

# ─── Built-in pattern generators ────────────────────────────────────────────
def make_stripes(sz, color, w):
    pat = Image.new("RGBA", (sz, sz), (0,0,0,0))
    d = ImageDraw.Draw(pat)
    for x in range(0, sz, w*2):
        d.rectangle([x, 0, x+w, sz], fill=color)
    return pat

def make_spots(sz, color, dr, sp):
    pat = Image.new("RGBA", (sz, sz), (0,0,0,0))
    d = ImageDraw.Draw(pat)
    for y in range(0, sz, sp):
        for x in range(0, sz, sp):
            d.ellipse([x, y, x+dr, y+dr], fill=color)
    return pat

def make_diag(sz, color, w):
    pat = Image.new("RGBA", (sz, sz), (0,0,0,0))
    d = ImageDraw.Draw(pat)
    for x in range(-sz, sz, w*2):
        d.line([(x, sz), (x+sz, 0)], fill=color, width=w)
    return pat

def make_check(sz, color, b):
    pat = Image.new("RGBA", (sz, sz), (0,0,0,0))
    d = ImageDraw.Draw(pat)
    for y in range(0, sz, b):
        for x in range(0, sz, b):
            if ((x//b + y//b) % 2) == 0:
                d.rectangle([x, y, x+b, y+b], fill=color)
    return pat

# ─── Pattern Config UI ─────────────────────────────────────────────────────
with st.sidebar.form('controls'):
  st.header('Skin Parts')
  parts=[]
  for name,def1,def2 in [('Backpack','#A0522D','#8B4513'),('Body','#FFD39F','#FFC071'),('Hands','#A0522D','#8B4513')]:
    f=st.selectbox(f'{name} fill',['Solid','Linear','Radial'],key=f'{name}_fill');c1=st.color_picker(f'{name} primary',def1,key=f'{name}_c1');c2=c1 if f=='Solid' else st.color_picker(f'{name} secondary',def2,key=f'{name}_c2')
    p=st.selectbox(f'{name} pattern',['None','Stripes','Spots','Diagonal','Checker','Custom'],key=f'{name}_pat')
    pc=sw=dr=sp=dw=bl=up=None
    if p=='Stripes': pc=st.color_picker(f'{name} stripe col',def2,key=f'{name}_pc');sw=st.slider(f'{name} stripe w',1,100,20,key=f'{name}_sw')
    elif p=='Spots': pc=st.color_picker(f'{name} spot col',def2,key=f'{name}_pc');dr=st.slider(f'{name} dot r',1,50,15,key=f'{name}_dr');sp=st.slider(f'{name} spacing',5,200,60,key=f'{name}_sp')
    elif p=='Diagonal': pc=st.color_picker(f'{name} diag col',def2,key=f'{name}_pc');dw=st.slider(f'{name} diag w',1,100,20,key=f'{name}_dw')
    elif p=='Checker': pc=st.color_picker(f'{name} check col',def2,key=f'{name}_pc');bl=st.slider(f'{name} block',5,200,50,key=f'{name}_bl')
    elif p=='Custom': up=st.file_uploader(f'{name} tile PNG',type='png',key=f'{name}_up')
    alpha=st.slider(f'{name} op',0.0,1.0,1.0,key=f'{name}_alpha')
    parts.append((name,f,c1,c2,p,pc,sw,dr,sp,dw,bl,up,alpha))
  oc=st.color_picker('Outline col','#000000');ow=st.slider('Outline w',0,50,10)
  by=st.slider('Backpack Y',-300,300,-150);hx=st.slider('Hands X',0,300,180);hy=st.slider('Hands Y',0,300,220)
  submitted=st.form_submit_button('Apply Changes')

# ─── Main UI ───────────────────────────────────────────────────────────────
tabs = st.tabs(['Editor','Preview','Export'])

with tabs[1]:
  st.subheader('Live Preview')
  placeholder = st.empty()
  placeholder.image(canvas.resize((256,256),Image.Resampling.LANCZOS))

with tabs[2]:
  col1,col2=st.columns(2)
  with col1:
    res=st.selectbox('Res',[256,512,1024],index=1)
    fmt=st.selectbox('Fmt',['PNG','JPEG','SVG'])
    if st.button('Download'):
      buf=io.BytesIO();out=canvas.resize((res,res),Image.Resampling.LANCZOS)
      if fmt=='JPEG': out.convert('RGB').save(buf,'JPEG');mime='image/jpeg'
      else: out.save(buf,'PNG');mime='image/png'
      st.download_button('dl',buf,file_name=f'skin.{fmt.lower()}',mime=mime)
  with col2:
    cfg=json.dumps({pn:dict(fill,f=ftype) for pn,(*_,ftype,pc,sw,dr,sp,dw,bl,up,alpha) in zip(['bp','bd','hd'],parts)},indent=2)
    st.download_button('Download JSON',cfg,'config.json','application/json')

# ─── Draw Canvas ───────────────────────────────────────────────────────────
canvas = Image.new('RGBA', (1024,1024), (0,0,0,0))
for name,f,c1,c2,p,pc,sw,dr,sp,dw,bl,up,alpha in parts:
    # Base fill
    fill_img = get_fill_image(f, c1, c2, 2*240 if name=='Backpack' else (2*280 if name=='Body' else 2*100)).convert('RGBA')
    # Pattern
    pattern = None
    r = 240 if name=='Backpack' else (280 if name=='Body' else 100)
    size = 2*r
    if p == 'Stripes':
        pattern = make_stripes(size, pc, sw)
    elif p == 'Spots':
        pattern = make_spots(size, pc, dr, sp)
    elif p == 'Diagonal':
        pattern = make_diag(size, pc, dw)
    elif p == 'Checker':
        pattern = make_check(size, pc, bl)
    elif p == 'Custom' and up:
        tile = Image.open(up).convert('RGBA')
        ow_t, oh_t = tile.size
        nw = max(1, int(size*0.2))
        nh = max(1, int(nw * oh_t / ow_t))
        small = tile.resize((nw, nh), Image.Resampling.LANCZOS)
        pattern = Image.new('RGBA', (size,size), (0,0,0,0))
        for y in range(0, size, nh):
            for x in range(0, size, nw):
                pattern.paste(small, (x,y), small)
    # Overlay pattern
    if pattern:
        alpha_mask = pattern.split()[3].point(lambda px: int(px * alpha))
        pattern.putalpha(alpha_mask)
        fill_img = Image.alpha_composite(fill_img, pattern)
    # Paste onto canvas
    # Determine center
    cx, cy = (512,512+by) if name=='Backpack' else ((512,512) if name=='Body' else ((512-hx,512+hy) if name=='Hands' else (512+hx,512+hy)))
    mask = Image.new('L', (size,size), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse((0,0,size,size), fill=255)
    canvas.paste(fill_img, (cx-r, cy-r), mask)
    # Outline
    ImageDraw.Draw(canvas).ellipse(
        (cx-r, cy-r, cx+r, cy+r), outline=oc, width=ow
    )
# Composite background
if bg_img:
    canvas = Image.alpha_composite(bg_img, canvas)
# Update Preview
placeholder.image(canvas.resize((256,256), Image.Resampling.LANCZOS))

# Export tab actions handled above
