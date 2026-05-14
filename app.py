import os
import io
import streamlit as st

from PIL import Image, ImageDraw, ImageFont, ImageColor
import arabic_reshaper

from bidi.algorithm import get_display
from streamlit_image_coordinates import streamlit_image_coordinates

# =========================================================
# تنظیمات اولیه
# =========================================================

st.set_page_config(
    page_title="Visit Card Designer",
    layout="wide"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BACKGROUND_DIR = os.path.join(BASE_DIR, "backgrounds")
FONTS_DIR = os.path.join(BASE_DIR, "fonts")

os.makedirs(BACKGROUND_DIR, exist_ok=True)
os.makedirs(FONTS_DIR, exist_ok=True)

# =========================================================
# تنظیمات کارت
# =========================================================

DPI = 300
CM_TO_INCH = 1 / 2.54

CARD_WIDTH = int(9 * CM_TO_INCH * DPI)
CARD_HEIGHT = int(5 * CM_TO_INCH * DPI)

PREVIEW_WIDTH = 800
PREVIEW_HEIGHT = int(PREVIEW_WIDTH * (CARD_HEIGHT / CARD_WIDTH))

# =========================================================
# کش‌ها
# =========================================================

@st.cache_data
def load_backgrounds():
    return [
        f for f in os.listdir(BACKGROUND_DIR)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    ]


@st.cache_data
def load_fonts():
    return [
        f for f in os.listdir(FONTS_DIR)
        if f.lower().endswith(".ttf")
    ]


@st.cache_resource
def get_font(font_path, size):
    return ImageFont.truetype(font_path, size)


@st.cache_data
def open_background(path):
    return Image.open(path).convert("RGBA")


# =========================================================
# داده‌های اولیه
# =========================================================

background_files = load_backgrounds()
fonts = load_fonts()

if not fonts:
    st.error("هیچ فونتی داخل پوشه fonts پیدا نشد.")
    st.stop()

TEXT_TYPES = {
    "title": "عنوان",
    "intro": "معرفی",
    "contact": "اطلاعات تماس",
    "email": "ایمیل"
}

# =========================================================
# Session State
# =========================================================

if "blocks" not in st.session_state:

    st.session_state.blocks = {}

    default_y = 180

    for key in TEXT_TYPES:

        st.session_state.blocks[key] = {
            "text": "",
            "font": fonts[0],
            "size": 60,
            "color": "#000000",
            "x": CARD_WIDTH // 2,
            "y": default_y
        }

        default_y += 160

if "active_block" not in st.session_state:
    st.session_state.active_block = "title"

if "logo_bytes" not in st.session_state:
    st.session_state.logo_bytes = None

if "logo_x" not in st.session_state:
    st.session_state.logo_x = CARD_WIDTH // 2

if "logo_y" not in st.session_state:
    st.session_state.logo_y = CARD_HEIGHT // 2

if "logo_scale" not in st.session_state:
    st.session_state.logo_scale = 100

# =========================================================
# توابع
# =========================================================

def rtl_text(text):
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def draw_text(draw, block):

    if not block["text"].strip():
        return

    font_path = os.path.join(FONTS_DIR, block["font"])

    try:
        font = get_font(font_path, block["size"])
    except:
        font = ImageFont.load_default()

    text = rtl_text(block["text"])

    draw.multiline_text(
        (block["x"], block["y"]),
        text,
        font=font,
        fill=block["color"],
        anchor="mm",
        align="center"
    )


def render_card(
        bg_path,
        blocks,
        logo_bytes,
        logo_scale,
        logo_pos,
        theme_color,
        rotate_mode
):

    img = open_background(bg_path).copy()

    img = img.resize((CARD_WIDTH, CARD_HEIGHT))

    # ====================
    # Rotate
    # ====================

    if rotate_mode == "Flip X":
        img = img.transpose(Image.FLIP_LEFT_RIGHT)

    elif rotate_mode == "Flip Y":
        img = img.transpose(Image.FLIP_TOP_BOTTOM)

    elif rotate_mode == "Rotate 180":
        img = img.rotate(180)

    # ====================
    # Theme Color
    # ====================

    if theme_color != "#ffffff":

        r, g, b = ImageColor.getrgb(theme_color)

        overlay = Image.new(
            "RGBA",
            img.size,
            (r, g, b, 60)
        )

        img = Image.alpha_composite(img, overlay)

    # ====================
    # Draw Texts
    # ====================

    draw = ImageDraw.Draw(img)

    for key in blocks:
        draw_text(draw, blocks[key])

    # ====================
    # Draw Logo
    # ====================

    if logo_bytes:

        logo = Image.open(
            io.BytesIO(logo_bytes)
        ).convert("RGBA")

        scale = logo_scale / 100.0

        w = max(1, int(logo.width * scale))
        h = max(1, int(logo.height * scale))

        logo = logo.resize((w, h), Image.LANCZOS)

        lx = int(logo_pos[0] - w / 2)
        ly = int(logo_pos[1] - h / 2)

        img.alpha_composite(logo, (lx, ly))

    return img


# =========================================================
# Sidebar
# =========================================================

st.sidebar.title("تنظیمات")

# ====================
# Background
# ====================

if background_files:

    selected_bg = st.sidebar.selectbox(
        "پس‌زمینه",
        background_files
    )

    bg_path = os.path.join(
        BACKGROUND_DIR,
        selected_bg
    )

else:

    st.warning("هیچ بکگراندی داخل پوشه backgrounds وجود ندارد.")
    st.stop()

# ====================
# Logo
# ====================

st.sidebar.markdown("---")

uploaded_logo = st.sidebar.file_uploader(
    "آپلود لوگو PNG",
    type=["png"]
)

if uploaded_logo:
    st.session_state.logo_bytes = uploaded_logo.read()

# ====================
# Theme
# ====================

st.sidebar.markdown("---")

theme_color = st.sidebar.color_picker(
    "رنگ تم",
    "#ffffff"
)

# ====================
# Rotation
# ====================

rotate_mode = st.sidebar.radio(
    "چرخش بکگراند",
    [
        "None",
        "Flip X",
        "Flip Y",
        "Rotate 180"
    ]
)

# =========================================================
# Layout
# =========================================================

left_col, right_col = st.columns([1, 1.4])

# =========================================================
# LEFT PANEL
# =========================================================

with left_col:

    st.header("ویرایش متن")

    cols = st.columns(len(TEXT_TYPES))

    for i, key in enumerate(TEXT_TYPES):

        if cols[i].button(TEXT_TYPES[key]):

            st.session_state.active_block = key

            st.rerun()

    active_key = st.session_state.active_block

    block = st.session_state.blocks[active_key]

    st.markdown("---")

    st.subheader(f"بخش فعال: {TEXT_TYPES[active_key]}")

    # ====================
    # Text
    # ====================

    block["text"] = st.text_area(
        "متن",
        block["text"],
        height=120
    )

    # ====================
    # Font
    # ====================

    current_font_index = fonts.index(block["font"])

    block["font"] = st.selectbox(
        "فونت",
        fonts,
        index=current_font_index
    )

    # ====================
    # Font Size
    # ====================

    block["size"] = st.slider(
        "اندازه فونت",
        10,
        180,
        block["size"]
    )

    # ====================
    # Color
    # ====================

    block["color"] = st.color_picker(
        "رنگ متن",
        block["color"]
    )

    # ====================
    # Position
    # ====================

    st.markdown("### موقعیت متن")

    block["x"] = st.slider(
        "X",
        0,
        CARD_WIDTH,
        block["x"]
    )

    block["y"] = st.slider(
        "Y",
        0,
        CARD_HEIGHT,
        block["y"]
    )

    # =====================================================
    # LOGO
    # =====================================================

    st.markdown("---")

    st.header("تنظیمات لوگو")

    st.session_state.logo_scale = st.slider(
        "اندازه لوگو (%)",
        10,
        300,
        st.session_state.logo_scale
    )

    st.session_state.logo_x = st.slider(
        "X لوگو",
        0,
        CARD_WIDTH,
        st.session_state.logo_x
    )

    st.session_state.logo_y = st.slider(
        "Y لوگو",
        0,
        CARD_HEIGHT,
        st.session_state.logo_y
    )

# =========================================================
# RIGHT PANEL
# =========================================================

with right_col:

    st.header("پیش‌نمایش")

    final_image = render_card(
        bg_path=bg_path,
        blocks=st.session_state.blocks,
        logo_bytes=st.session_state.logo_bytes,
        logo_scale=st.session_state.logo_scale,
        logo_pos=(
            st.session_state.logo_x,
            st.session_state.logo_y
        ),
        theme_color=theme_color,
        rotate_mode=rotate_mode
    )

    preview = final_image.resize(
        (PREVIEW_WIDTH, PREVIEW_HEIGHT)
    )

    # =====================================================
    # Interactive Preview
    # =====================================================

    clicked = streamlit_image_coordinates(
        preview,
        key="card_preview"
    )

    if clicked is not None:

        px = int(
            clicked["x"] / PREVIEW_WIDTH * CARD_WIDTH
        )

        py = int(
            clicked["y"] / PREVIEW_HEIGHT * CARD_HEIGHT
        )

        st.session_state.blocks[
            st.session_state.active_block
        ]["x"] = px

        st.session_state.blocks[
            st.session_state.active_block
        ]["y"] = py

        st.rerun()

    # =====================================================
    # Download
    # =====================================================

    st.markdown("---")

    buffer = io.BytesIO()

    final_image.convert("RGB").save(
        buffer,
        format="PNG",
        dpi=(DPI, DPI)
    )

    st.download_button(
        "دانلود کارت نهایی",
        data=buffer.getvalue(),
        file_name="visit_card.png",
        mime="image/png",
        use_container_width=True
    )

# =========================================================
# Footer
# =========================================================

st.markdown("---")

st.caption("Visit Card Designer • Streamlit Edition")