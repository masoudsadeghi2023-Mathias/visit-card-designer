import os
import io
import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageColor
import arabic_reshaper
from bidi.algorithm import get_display

# ============================
#   ثابت‌ها و مسیرها
# ============================

os.chdir(os.path.dirname(os.path.abspath(__file__)))

DPI = 300
CM_TO_INCH = 1 / 2.54
CARD_WIDTH = int(9 * CM_TO_INCH * DPI)
CARD_HEIGHT = int(5 * CM_TO_INCH * DPI)

PREVIEW_WIDTH = 800
PREVIEW_HEIGHT = int(PREVIEW_WIDTH * (CARD_HEIGHT / CARD_WIDTH))

BACKGROUND_DIR = "backgrounds"
FONTS_DIR = "fonts"

# ============================
#   کمک‌تابع‌ها
# ============================

def load_backgrounds():
    if not os.path.isdir(BACKGROUND_DIR):
        os.makedirs(BACKGROUND_DIR)
    files = [
        f for f in os.listdir(BACKGROUND_DIR)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    ]
    return files

def load_fonts():
    if not os.path.isdir(FONTS_DIR):
        os.makedirs(FONTS_DIR)
    fonts = [f for f in os.listdir(FONTS_DIR) if f.lower().endswith(".ttf")]
    return fonts

def draw_text(draw, text, font_name, size, color, x, y):
    if not text.strip():
        return
    reshaped = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped)
    font_path = os.path.join(FONTS_DIR, font_name)
    try:
        font = ImageFont.truetype(font_path, size)
    except:
        font = ImageFont.load_default()
    draw.multiline_text((x, y), bidi_text, font=font, fill=color, anchor="mm", align="center")

def render_card(bg_path, data, logo_bytes, logo_scale, logo_pos, theme_color, rotate_mode):
    img = Image.open(bg_path).convert("RGBA")
    img = img.resize((CARD_WIDTH, CARD_HEIGHT))

    if rotate_mode == "Flip X":
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    elif rotate_mode == "Flip Y":
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
    elif rotate_mode == "Rotate 180":
        img = img.rotate(180)

    if theme_color:
        r, g, b = ImageColor.getrgb(theme_color)
        overlay = Image.new("RGBA", img.size, (r, g, b, 60))
        img = Image.alpha_composite(img, overlay)

    draw = ImageDraw.Draw(img)

    # چهار متن مستقل
    for key in ["title", "intro", "contact", "email"]:
        block = data[key]
        draw_text(draw, block["text"], block["font"], block["size"], block["color"], block["x"], block["y"])

    # لوگو
    if logo_bytes is not None:
        logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
        scale = logo_scale / 100.0
        w = max(1, int(logo.width * scale))
        h = max(1, int(logo.height * scale))
        logo_resized = logo.resize((w, h), Image.LANCZOS)
        lx = int(logo_pos[0] - logo_resized.width / 2)
        ly = int(logo_pos[1] - logo_resized.height / 2)
        img.alpha_composite(logo_resized, (lx, ly))

    return img

# ============================
#   تنظیمات Streamlit
# ============================

st.set_page_config(page_title="Visit Card Designer", layout="wide")

background_files = load_backgrounds()
fonts = load_fonts() or ["Default.ttf"]

# ============================
#   داده‌های اولیه در Session State
# ============================

if "blocks" not in st.session_state:
    st.session_state.blocks = {
        "title":   {"text": "", "font": fonts[0], "size": 50, "color": "#ffffff", "x": CARD_WIDTH//2, "y": 150},
        "intro":   {"text": "", "font": fonts[0], "size": 40, "color": "#ffffff", "x": CARD_WIDTH//2, "y": 260},
        "contact": {"text": "", "font": fonts[0], "size": 35, "color": "#ffffff", "x": CARD_WIDTH//2, "y": 380},
        "email":   {"text": "", "font": fonts[0], "size": 35, "color": "#ffffff", "x": CARD_WIDTH//2, "y": 480},
    }

if "active" not in st.session_state:
    st.session_state.active = "title"

# ============================
#   سایدبار
# ============================

st.sidebar.title("تنظیمات کارت ویزیت")

bg_name = st.sidebar.selectbox("پس‌زمینه", background_files) if background_files else None

uploaded_logo = st.sidebar.file_uploader("لوگو (PNG)", type=["png"])
logo_bytes = uploaded_logo.read() if uploaded_logo else None

st.sidebar.markdown("---")
theme_color = st.sidebar.color_picker("🎨 رنگ تم", "#ffffff")

st.sidebar.markdown("---")
rotate_mode = st.sidebar.radio("🔁 چرخش", ["None", "Flip X", "Flip Y", "Rotate 180"])

# ============================
#   بدنه اصلی
# ============================

col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.header("بخش فعال")

    # دکمه‌های افقی
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("عنوان"):
        st.session_state.active = "title"
    if c2.button("معرفی"):
        st.session_state.active = "intro"
    if c3.button("آدرس"):
        st.session_state.active = "contact"
    if c4.button("ایمیل"):
        st.session_state.active = "email"

    active = st.session_state.active
    block = st.session_state.blocks[active]

    st.subheader(f"متن بخش: {active}")

    # متن مشترک
    new_text = st.text_area("متن", block["text"])
    block["text"] = new_text

    # کنترل‌های مشترک
    block["font"] = st.selectbox("فونت", fonts, index=fonts.index(block["font"]))
    block["size"] = st.slider("اندازه فونت", 10, 150, block["size"])
    block["color"] = st.color_picker("رنگ متن", block["color"])
    block["x"] = st.slider("X", 0, CARD_WIDTH, block["x"])
    block["y"] = st.slider("Y", 0, CARD_HEIGHT, block["y"])

    st.header("لوگو")
    logo_scale = st.slider("اندازه لوگو (%)", 10, 300, 100)
    logo_x = st.slider("X لوگو", 0, CARD_WIDTH, CARD_WIDTH // 2)
    logo_y = st.slider("Y لوگو", 0, CARD_HEIGHT, CARD_HEIGHT // 2)

with col_right:
    st.header("پیش‌نمایش")

    if bg_name:
        bg_path = os.path.join(BACKGROUND_DIR, bg_name)

        img = render_card(
            bg_path=bg_path,
            data=st.session_state.blocks,
            logo_bytes=logo_bytes,
            logo_scale=logo_scale,
            logo_pos=(logo_x, logo_y),
            theme_color=theme_color,
            rotate_mode=rotate_mode
        )

        preview = img.resize((PREVIEW_WIDTH, PREVIEW_HEIGHT))
        st.image(preview, use_column_width=True)

        buf = io.BytesIO()
        img_rgb = img.convert("RGB")
        img_rgb.save(buf, format="PNG", dpi=(DPI, DPI))
        st.download_button(
            "دانلود کارت نهایی (PNG)",
            data=buf.getvalue(),
            file_name="visit_card.png",
            mime="image/png"
        )
    else:
        st.info("لطفاً از سایدبار یک پس‌زمینه انتخاب کن.")
