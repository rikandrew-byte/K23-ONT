#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ứng dụng tạo tập luyện viết chữ Hán
=====================================
Thư viện: pip install reportlab requests pillow matplotlib
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os, sys, json, re, math, warnings
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path as MplPath
import matplotlib.font_manager as fm

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.utils import ImageReader


# ─────────────────────────────────────────────────────────────────────────────
#  FONT SETUP  (phải chạy trước khi dùng pyplot)
# ─────────────────────────────────────────────────────────────────────────────

_CJK_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simsun.ttc",
    r"C:\Windows\Fonts\STKAITI.TTF",
    r"C:\Windows\Fonts\mingliu.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
]

_VI_CANDIDATES = [          # font hỗ trợ ký tự tiếng Việt có dấu
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\tahoma.ttf",
    r"C:\Windows\Fonts\calibri.ttf",
    r"C:\Windows\Fonts\msyh.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

_CJK_FONT_PATH: str | None = None
_VI_FONT_PATH:  str | None = None


def _supports_glyphs(path: str, test_chars: str) -> bool:
    """Kiểm tra font có render được test_chars không (dùng PIL)."""
    try:
        font = ImageFont.truetype(path, 16)
        img  = Image.new("RGB", (len(test_chars) * 20, 24), "white")
        ImageDraw.Draw(img).text((2, 2), test_chars, font=font, fill="black")
        return any(p != (255, 255, 255) for p in img.getdata())
    except Exception:
        return False


def _setup_fonts():
    global _CJK_FONT_PATH, _VI_FONT_PATH

    # Tìm font CJK
    for path in _CJK_CANDIDATES:
        if os.path.isfile(path) and _supports_glyphs(path, "赢你好"):
            _CJK_FONT_PATH = path
            # Đăng ký vào matplotlib
            fm.fontManager.addfont(path)
            name = fm.FontProperties(fname=path).get_name()
            matplotlib.rcParams["font.family"] = name
            matplotlib.rcParams["axes.unicode_minus"] = False
            break

    # Tìm font tiếng Việt
    for path in _VI_CANDIDATES:
        if os.path.isfile(path) and _supports_glyphs(path, "Thứ tự nét viết"):
            _VI_FONT_PATH = path
            break


_setup_fonts()


def pil_font(path: str | None, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Trả về PIL font, fallback về default nếu lỗi."""
    if path:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


# ─────────────────────────────────────────────────────────────────────────────
#  HẰNG SỐ LAYOUT
# ─────────────────────────────────────────────────────────────────────────────

HW_SIZE = 1024.0

CDN_URL        = "https://cdn.jsdelivr.net/npm/hanzi-writer-data@2.0/{char}.json"
CDN_URL_LATEST = "https://cdn.jsdelivr.net/npm/hanzi-writer-data@latest/{char}.json"

PAGE_W, PAGE_H = A4          # 595 × 842 pt
MARGIN_X = 36                # pt
MARGIN_Y = 36

PRACTICE_ROWS     = 3        # mặc định, override được qua LayoutConfig
PRACTICE_COLS     = 15       # cố định 15 ô/dòng
TRACE_SQUARES     = 3        # luôn 3 ô đầu có chữ mẫu
MAX_STEPS_PER_ROW = 16

# ── Kích thước cố định ────────────────────────────────────────────────────────
FIXED_SQ = 34.0              # 12mm = 34pt, không thay đổi

# Màu (R,G,B 0–1)
C_STROKE  = (0.10, 0.10, 0.18)
C_RED     = (0.90, 0.22, 0.27)
C_BORDER  = (0.27, 0.27, 0.27)
C_DASH    = (0.73, 0.73, 0.73)
C_BG_HDR  = (0.97, 0.97, 0.97)

# Render DPI cho ảnh nét và header
RENDER_DPI = 150

# ── Không còn tùy chọn cỡ — cố định 34pt (12mm) ─────────────────────────────

class LayoutConfig:
    """
    Layout cố định sq=34pt (12mm), 15 ô/dòng.
    Tham số duy nhất người dùng chọn: rows (số dòng luyện tập).
    """
    def __init__(self, rows: int = 3):
        self.sq     = FIXED_SQ
        self.rows   = max(1, rows)
        self.sq_gap = 2.0           # khoảng cách giữa các ô (pt)

        cw              = PAGE_W - 2 * MARGIN_X
        self.content_w  = cw
        self.cols       = PRACTICE_COLS   # luôn 15

        # Header: bằng đúng kích thước ô để tỉ lệ đồng đều
        # Tăng thêm 10pt để chứa nhãn cụm nếu cần (không ảnh hưởng khi không có nhãn)
        self.hdr_h      = 48.0
        # Stroke-order box: ô VUÔNG bằng box_h × box_h
        # Giới hạn tối đa = box_h để không giãn ngang khi ít nét
        self.box_h      = 30.0      # chiều cao (= chiều rộng tối đa) của mỗi ô thứ tự nét
        self.box_gap    = 2.5
        self.lbl_h      = 14.0      # nhãn section - TĂNG để rõ ràng hơn

        self.row_h      = self.sq + self.sq_gap
        self.blk_gap    = 6.0       # khoảng cách giữa các block (giảm để tiết kiệm giấy)

    def stroke_section_h(self, n_strokes: int) -> float:
        """Chiều cao phần thứ tự nét (1 hoặc 2 hàng nếu > 16 nét)."""
        n_rows = math.ceil(n_strokes / MAX_STEPS_PER_ROW)
        return self.lbl_h + 6 + n_rows * (self.box_h + self.box_gap + 6) + 2

    def block_total_h(self, n_strokes: int) -> float:
        practice_h = self.rows * self.row_h + self.lbl_h + 6  # thêm khoảng cách
        return self.hdr_h + 2 + self.stroke_section_h(n_strokes) + practice_h + self.blk_gap


# ─────────────────────────────────────────────────────────────────────────────
#  BỘ NHỚ ĐỆM CỤ CỤC BỘ (LOCAL CACHE) & LẤY DỮ LIỆU NÉT / TỪ ĐIỂN
# ─────────────────────────────────────────────────────────────────────────────

CACHE_DIR = Path("cache")
STROKES_CACHE_DIR = CACHE_DIR / "strokes"
DICT_CACHE_DIR = CACHE_DIR / "dict"

# Đảm bảo các thư mục cache tồn tại
STROKES_CACHE_DIR.mkdir(parents=True, exist_ok=True)
DICT_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def fetch_character_data(char: str) -> dict:
    """
    Lấy dữ liệu nét của chữ Hán. Ưu tiên đọc từ cache cục bộ.
    Nếu không có, tải từ CDN và lưu vào cache.
    """
    cache_file = STROKES_CACHE_DIR / f"{char}.json"
    if cache_file.is_file():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                d = json.load(f)
                if "strokes" in d and "medians" in d:
                    return d
        except Exception:
            pass

    encoded  = char.encode("utf-8")
    url_char = "".join(f"%{b:02X}" for b in encoded)
    for url in [CDN_URL.format(char=url_char), CDN_URL_LATEST.format(char=url_char)]:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                d = r.json()
                if "strokes" in d and "medians" in d:
                    # Lưu vào cache
                    try:
                        with open(cache_file, "w", encoding="utf-8") as f:
                            json.dump(d, f, ensure_ascii=False, indent=2)
                    except Exception:
                        pass
                    return d
        except requests.exceptions.ConnectionError:
            raise RuntimeError("Không có kết nối internet.")
        except requests.exceptions.Timeout:
            raise RuntimeError("Hết thời gian chờ khi tải dữ liệu.")
        except (json.JSONDecodeError, ValueError):
            continue
    raise RuntimeError(f"Không tìm thấy dữ liệu cho '{char}'.")


def fetch_dictionary_data_bulk(chars: list[str]) -> dict[str, dict[str, str]]:
    """
    Tra cứu hàng loạt Pinyin và nghĩa Hán-Việt cho danh sách ký tự.
    Ưu tiên đọc từ cache cục bộ. Đối với những chữ chưa có cache,
    gửi yêu cầu mạng đến thivien.net để tra cứu hàng loạt, sau đó lưu cache.
    
    Trả về dict dạng: {char: {"pinyin": str, "nghia": str}}
    """
    results = {}
    missing_chars = []
    
    # 1. Đọc từ cache trước
    for ch in chars:
        cache_file = DICT_CACHE_DIR / f"{ch}.json"
        if cache_file.is_file():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    results[ch] = json.load(f)
                    continue
            except Exception:
                pass
        missing_chars.append(ch)
        
    if not missing_chars:
        return results
        
    # 2. Gửi yêu cầu lấy từ điển trực tuyến từ Thi Viện
    url = "https://hvdic.thivien.net/transcript-query.json.php"
    headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
    
    # Gom các chữ thiếu thành 1 chuỗi để tra cứu trong 1 request
    query_str = "".join(missing_chars)
    dict_temp = {ch: {"pinyin": "", "nghia": ""} for ch in missing_chars}
    
    # Tra cứu Hán-Việt (lang=1)
    try:
        r = requests.post(url, data={"mode": "trans", "lang": "1", "input": query_str}, headers=headers, timeout=8)
        if r.status_code == 200:
            res_data = r.json()
            if isinstance(res_data, dict) and "result" in res_data:
                for item in res_data["result"]:
                    char_i = item.get("i")
                    readings = item.get("o")
                    if char_i in dict_temp and isinstance(readings, list) and readings:
                        # Lấy nghĩa đầu tiên và viết hoa
                        dict_temp[char_i]["nghia"] = readings[0].upper()
    except Exception as e:
        print(f"Lỗi tra nghĩa Hán-Việt trực tuyến: {e}", file=sys.stderr)

    # Tra cứu Pinyin (lang=2)
    try:
        r = requests.post(url, data={"mode": "trans", "lang": "2", "input": query_str}, headers=headers, timeout=8)
        if r.status_code == 200:
            res_data = r.json()
            if isinstance(res_data, dict) and "result" in res_data:
                for item in res_data["result"]:
                    char_i = item.get("i")
                    readings = item.get("o")
                    if char_i in dict_temp and isinstance(readings, list) and readings:
                        dict_temp[char_i]["pinyin"] = readings[0]
    except Exception as e:
        print(f"Lỗi tra Pinyin trực tuyến: {e}", file=sys.stderr)

    # Lưu cache và gộp vào kết quả
    for ch, data in dict_temp.items():
        cache_file = DICT_CACHE_DIR / f"{ch}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        results[ch] = data
        
    return results


# ─────────────────────────────────────────────────────────────────────────────
#  SVG PATH → matplotlib Path  (đúng, dùng lại từ generate_sheet.py)
# ─────────────────────────────────────────────────────────────────────────────

def _tokenise(d: str):
    re_tok = re.compile(
        r"([MmZzLlHhVvCcSsQqTtAa])|"
        r"([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)"
    )
    cmd, args = None, []
    for ct, nt in re_tok.findall(d):
        if ct:
            if cmd is not None: yield cmd, args
            cmd, args = ct, []
        elif nt:
            args.append(float(nt))
    if cmd is not None: yield cmd, args


def svg_to_mpl(d: str, tfn=None):
    """Chuyển SVG path string → matplotlib Path. tfn(x,y) → (x',y')."""
    verts, codes = [], []
    cx = cy = 0.0

    def T(x, y): return tfn(x, y) if tfn else (x, y)

    for cmd, args in _tokenise(d):
        if cmd in "Mm":
            rel = cmd.islower()
            for i in range(0, len(args), 2):
                x = (cx + args[i]   if rel else args[i])
                y = (cy + args[i+1] if rel else args[i+1])
                verts.append(T(x, y)); codes.append(MplPath.MOVETO)
                cx, cy = x, y
        elif cmd in "Ll":
            rel = cmd.islower()
            for i in range(0, len(args), 2):
                x = (cx + args[i]   if rel else args[i])
                y = (cy + args[i+1] if rel else args[i+1])
                verts.append(T(x, y)); codes.append(MplPath.LINETO)
                cx, cy = x, y
        elif cmd in "Cc":
            rel = cmd.islower()
            for i in range(0, len(args), 6):
                pts = args[i:i+6]
                if len(pts) < 6: break
                if rel:
                    pts = [pts[0]+cx,pts[1]+cy, pts[2]+cx,pts[3]+cy,
                           pts[4]+cx,pts[5]+cy]
                for k in range(0,6,2): verts.append(T(pts[k], pts[k+1]))
                codes += [MplPath.CURVE4]*3
                cx, cy = pts[4], pts[5]
        elif cmd in "Qq":
            rel = cmd.islower()
            for i in range(0, len(args), 4):
                pts = args[i:i+4]
                if len(pts) < 4: break
                if rel:
                    pts = [pts[0]+cx,pts[1]+cy, pts[2]+cx,pts[3]+cy]
                verts.append(T(pts[0],pts[1])); verts.append(T(pts[2],pts[3]))
                codes += [MplPath.CURVE3]*2
                cx, cy = pts[2], pts[3]
        elif cmd in "Zz":
            if verts: verts.append(verts[-1]); codes.append(MplPath.CLOSEPOLY)

    return MplPath(verts, codes) if verts else None


# ─────────────────────────────────────────────────────────────────────────────
#  RENDER NÉT CHỮ → PIL Image  (dùng matplotlib, chính xác)
# ─────────────────────────────────────────────────────────────────────────────

def render_strokes_pil(strokes: list, num: int, px: int = 200,
                       highlight_last: bool = False,
                       alpha: float = 1.0) -> Image.Image:
    """
    Vẽ `num` nét đầu tiên vào ảnh PIL px×px.
    Dùng matplotlib backend Agg (chính xác Bezier).
    """
    PAD   = 0.12  # Tăng padding để nét chữ không bị sát mép hoặc mất chân
    SCALE = (1.0 - 2*PAD) / HW_SIZE

    def hw2u(x, y): return x*SCALE + PAD, y*SCALE + PAD

    inch = px / RENDER_DPI
    fig = plt.figure(figsize=(inch, inch), dpi=RENDER_DPI)
    ax  = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(-0.08, 1.08); ax.set_ylim(-0.08, 1.08)
    ax.set_aspect("equal"); ax.axis("off")
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    for i, sd in enumerate(strokes[:num]):
        is_last   = (i == num - 1)
        color     = C_RED if (highlight_last and is_last) else C_STROKE
        mpath     = svg_to_mpl(sd, tfn=hw2u)
        if mpath is None: continue
        ax.add_patch(patches.PathPatch(
            mpath, facecolor=color, edgecolor=color,
            lw=0.5, alpha=alpha, zorder=2+i
        ))

    buf = BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fig.savefig(buf, format="png", dpi=RENDER_DPI,
                    bbox_inches=None, transparent=True)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGBA").copy()


# ─────────────────────────────────────────────────────────────────────────────
#  RENDER HEADER BLOCK → PIL Image
#  Dùng PIL text để tránh hoàn toàn ReportLab font encoding issues
# ─────────────────────────────────────────────────────────────────────────────

def render_header_pil(char: str, pinyin: str, nghia: str,
                      num_strokes: int, width_pt: float, height_pt: float,
                      group_label: str = "",
                      dpi: int = RENDER_DPI) -> Image.Image:
    """
    Vẽ header block thành PIL Image với font CJK + Unicode Việt.
    group_label: nếu không rỗng, vẽ thêm nhãn cụm nhỏ phía trên (ví dụ '人事').
    """
    W = int(width_pt  * dpi / 72)
    H = int(height_pt * dpi / 72)
    img = Image.new("RGB", (W, H), (247, 247, 247))
    draw = ImageDraw.Draw(img)

    # Thanh đỏ bên trái
    bar_w = max(4, int(W * 0.006))
    draw.rectangle([0, 0, bar_w, H], fill=(230, 57, 70))

    char_x = bar_w + max(4, int(W * 0.010))

    # ── Nhãn cụm nhỏ phía trên (nếu có) ────────────────────────────────
    # Chiếm không gian nhỏ góc trên bên trái, không ảnh hưởng đến size chữ Hán
    if group_label:
        f_lbl   = pil_font(_CJK_FONT_PATH, max(8, int(H * 0.16))) # nhỏ hơn một chút
        label_h = int(H * 0.22)
        # Nền nhãn nhạt hơn
        draw.rectangle([bar_w, 0, W, label_h], fill=(238, 238, 242))
        draw.line([(bar_w, label_h), (W, label_h)], fill=(210, 210, 210), width=1)
        draw.text((char_x, 2), group_label, font=f_lbl, fill=(100, 100, 130))

    # ── Chữ Hán lớn – căn giữa dọc phần không gian bên dưới nhãn ──────────
    # Size cố định cho MỌI chữ Hán để tránh "chữ to, chữ bé"
    char_sz = int(H * 0.55)
    f_cjk   = pil_font(_CJK_FONT_PATH, char_sz)
    
    # Tính khoảng trống thực tế: Nếu có nhãn thì chừa 22% ở trên, nếu không thì dùng toàn bộ 100%
    effective_label_h = int(H * 0.22) if group_label else 0
    available_h = H - effective_label_h
    
    # Căn giữa theo font bounding box để chính xác nhất
    bbox_char = draw.textbbox((0, 0), char, font=f_cjk)
    char_h_actual = bbox_char[3] - bbox_char[1]
    
    # Căn giữa trong không gian `available_h`
    char_y = effective_label_h + (available_h - char_h_actual) // 2 - bbox_char[1]
    
    draw.text((char_x, char_y), char, font=f_cjk, fill=(26, 26, 46))
    
    # Tính toán để căn lề cột phải
    char_actual_w = bbox_char[2] - bbox_char[0]

    # Đường dọc phân cách
    sep_x = char_x + char_actual_w + max(12, int(W * 0.02))
    draw.line([(sep_x, int(H * 0.1)),
               (sep_x, int(H * 0.9))],
              fill=(221, 221, 221), width=1)

    # ── Cột phải: Pinyin + Nghĩa + "N nét" – căn giữa dọc toàn bộ block H ────
    info_x = sep_x + max(12, int(W * 0.02))
    
    # Kích thước chữ cố định
    py_sz  = max(10, int(H * 0.26))
    ng_sz  = max(8,  int(H * 0.20))
    sm_sz  = max(7,  int(H * 0.15))

    f_py = pil_font(_VI_FONT_PATH, py_sz)
    f_ng = pil_font(_VI_FONT_PATH, ng_sz)
    f_sm = pil_font(_VI_FONT_PATH, sm_sz)

    GAP12 = max(2, int(H * 0.03))   # khoảng cách pinyin → nghĩa
    GAP23 = max(2, int(H * 0.03))   # khoảng cách nghĩa → số nét
    sm_label = f"{num_strokes} nét"

    # Tính toán chiều cao khối thông tin và vẽ (căn giữa trong available_h)
    if pinyin and nghia:
        block_h = py_sz + GAP12 + ng_sz + GAP23 + sm_sz
        block_y = effective_label_h + (available_h - block_h) // 2
        draw.text((info_x, block_y),                          pinyin,   font=f_py, fill=(51,  51,  51))
        draw.text((info_x, block_y + py_sz + GAP12),          nghia,    font=f_ng, fill=(100, 100, 100))
        draw.text((info_x, block_y + py_sz + GAP12 + ng_sz + GAP23), sm_label, font=f_sm, fill=(160, 160, 160))
    elif pinyin:
        block_h = py_sz + GAP23 + sm_sz
        block_y = effective_label_h + (available_h - block_h) // 2
        draw.text((info_x, block_y),                 pinyin,   font=f_py, fill=(51,  51,  51))
        draw.text((info_x, block_y + py_sz + GAP23), sm_label, font=f_sm, fill=(160, 160, 160))
    elif nghia:
        block_h = ng_sz + GAP23 + sm_sz
        block_y = effective_label_h + (available_h - block_h) // 2
        draw.text((info_x, block_y),                 nghia,    font=f_ng, fill=(100, 100, 100))
        draw.text((info_x, block_y + ng_sz + GAP23), sm_label, font=f_sm, fill=(160, 160, 160))
    else:
        # Không có pinyin lẫn nghĩa – chỉ số nét
        block_y = effective_label_h + (available_h - sm_sz) // 2
        draw.text((info_x, block_y), sm_label, font=f_sm, fill=(160, 160, 160))

    return img


def render_label_pil(text: str, width_pt: float, height_pt: float,
                     dpi: int = RENDER_DPI) -> Image.Image:
    """Vẽ nhãn section (text tiếng Việt) thành ảnh PIL với nền nhẹ."""
    W = int(width_pt  * dpi / 72)
    H = int(height_pt * dpi / 72)
    
    # Tạo ảnh với nền xám rất nhạt
    img  = Image.new("RGB", (W, H), (250, 250, 252))
    draw = ImageDraw.Draw(img)
    
    # Vẽ text với font và size phù hợp
    f = pil_font(_VI_FONT_PATH, int(H * 0.50))  # giảm tỷ lệ để text không bị cắt
    
    # Căn giữa theo chiều dọc
    draw.text((6, int(H * 0.25)), text, font=f, fill=(70, 70, 90))
    
    # Vẽ đường viền nhẹ phía dưới
    draw.line([(0, H-1), (W, H-1)], fill=(220, 220, 225), width=1)
    
    return img


# ─────────────────────────────────────────────────────────────────────────────
#  HELPER: PIL Image → ReportLab ImageReader (in-memory)
# ─────────────────────────────────────────────────────────────────────────────

def pil_to_rl(img: Image.Image) -> ImageReader:
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


# ─────────────────────────────────────────────────────────────────────────────
#  VẼ Ô 米字格 TRỰC TIẾP TRÊN CANVAS REPORTLAB
# ─────────────────────────────────────────────────────────────────────────────

def draw_mizige(c, x: float, y: float, size: float):
    """Vẽ một ô 米字格 vào ReportLab canvas. y = góc dưới trái."""
    c.saveState()
    # Nền trắng + viền ngoài
    c.setFillColorRGB(1, 1, 1)
    c.setStrokeColorRGB(*C_BORDER)
    c.setLineWidth(0.9)
    c.rect(x, y, size, size, fill=1, stroke=1)

    # Đường kẻ phụ (đứt nét)
    c.setStrokeColorRGB(*C_DASH)
    c.setLineWidth(0.5)
    c.setDash([2.5, 2.5])
    cx, cy = x + size/2, y + size/2
    c.line(x,  cy, x+size, cy)          # ngang
    c.line(cx,  y, cx, y+size)          # dọc
    c.line(x,   y, x+size, y+size)      # chéo ↗
    c.line(x, y+size, x+size, y)        # chéo ↘
    c.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
#  VẼ MỘT BLOCK CHỮ HÁN VÀO PDF
# ─────────────────────────────────────────────────────────────────────────────

def draw_char_block(c, char: str, strokes: list,
                    x: float, y: float,
                    pinyin: str = "", nghia: str = "",
                    cfg: LayoutConfig | None = None,
                    group_label: str = ""):
    """Vẽ block hoàn chỉnh: header + stroke-order + practice grid.
    y = góc DƯỚI TRÁI của block (PDF coordinates).
    group_label: tên cụm hiển thị nhỏ trong header (chỉ chữ đầu cụm).
    """
    if cfg is None:
        cfg = LayoutConfig()

    n   = len(strokes)
    cw  = cfg.content_w
    blk = cfg.block_total_h(n)
    top = y + blk

    # ── HEADER ────────────────────────────────────────────────────────
    hdr_y   = top - cfg.hdr_h
    hdr_img = render_header_pil(char, pinyin, nghia, n, cw, cfg.hdr_h,
                                group_label=group_label)
    c.drawImage(pil_to_rl(hdr_img), x, hdr_y, width=cw, height=cfg.hdr_h)
    c.setStrokeColorRGB(*C_DASH); c.setLineWidth(0.4)
    c.line(x, hdr_y, x + cw, hdr_y)

    # ── NHÃN THỨ TỰ NÉT ───────────────────────────────────────────────
    lbl_h      = cfg.lbl_h
    stroke_top = hdr_y - lbl_h - 2  # thêm 2pt khoảng cách
    lbl1       = render_label_pil("◆  Thứ tự nét viết", cw, lbl_h)
    c.drawImage(pil_to_rl(lbl1), x, stroke_top, width=cw, height=lbl_h)

    # ── BẢNG THỨ TỰ NÉT ──────────────────────────────────────────────
    # Mỗi ô thứ tự nét là hình VUÔNG kích thước box_h × box_h.
    # Các ô được căn trái; không giãn ra để lấp đầy chiều rộng trang.
    n_step_rows     = math.ceil(n / MAX_STEPS_PER_ROW)
    box_h           = cfg.box_h
    box_gap         = cfg.box_gap
    stroke_grid_top = stroke_top - 4  # thêm khoảng cách từ nhãn xuống lưới

    for row_i in range(n_step_rows):
        s0   = row_i * MAX_STEPS_PER_ROW
        s1   = min(s0 + MAX_STEPS_PER_ROW, n)
        n_in = s1 - s0
        # ô vuông – không giãn
        box_w = box_h
        row_y = stroke_grid_top - (row_i + 1) * (box_h + box_gap + 6)

        for col_i in range(n_in):
            sn = s0 + col_i + 1
            bx = x + col_i * (box_w + box_gap)
            by = row_y + 2

            # Nền ô (hình vuông hoàn hảo)
            c.saveState()
            c.setFillColorRGB(0.98, 0.98, 0.98)
            c.setStrokeColorRGB(*C_DASH); c.setLineWidth(0.4)
            c.rect(bx, by, box_w, box_h, fill=1, stroke=1)
            c.restoreState()

            # Render nét trong ô – dịch ảnh lên cao hơn trong ô cho cân đối
            px_size = max(48, int(box_h * RENDER_DPI / 72 * 1.8))
            stroke_img = render_strokes_pil(strokes, sn, px=px_size, highlight_last=True)
            img_sz  = box_h - 3       # kích thước ảnh vuông nhỏ hơn ô một chút
            x_off   = (box_w - img_sz) / 2   # căn giữa ngang
            y_off   = 2.5                      # đẩy ảnh lên khỏi đáy ô (tung độ ReportLab tăng lên)
            c.drawImage(pil_to_rl(stroke_img),
                        bx + x_off, by + y_off,
                        width=img_sz, height=img_sz,
                        mask="auto")

            # Số thứ tự nhỏ dưới ô
            c.setFillColorRGB(0.60, 0.60, 0.60)
            c.setFont("Helvetica", 5.0)
            c.drawCentredString(bx + box_w/2, by - 5.5, str(sn))

    # ── NHÃN LUYỆN TẬP ────────────────────────────────────────────────
    practice_top = stroke_grid_top - n_step_rows * (box_h + box_gap + 6) - 6  # thêm khoảng cách
    lbl2 = render_label_pil("◆  Luyện tập  (3 ô đầu: đồ theo chữ mẫu)", cw, lbl_h)
    c.drawImage(pil_to_rl(lbl2), x, practice_top, width=cw, height=lbl_h)

    # ── 米字格 PRACTICE GRID ──────────────────────────────────────────
    grid_top = practice_top - 4  # thêm khoảng cách từ nhãn xuống lưới
    sq       = cfg.sq
    sq_gap   = cfg.sq_gap
    row_h    = cfg.row_h
    cols     = cfg.cols
    rows     = cfg.rows

    for row_i in range(rows):
        ry = grid_top - (row_i + 1) * row_h + (row_h - sq) / 2
        for col_i in range(cols):
            sx = x + col_i * (sq + sq_gap)
            draw_mizige(c, sx, ry, sq)

            flat = row_i * cols + col_i
            if flat < TRACE_SQUARES:
                guide_px = max(48, int(sq * RENDER_DPI / 72))
                guide    = render_strokes_pil(strokes, n, px=guide_px,
                                              highlight_last=False, alpha=0.15)
                pad = sq * 0.07
                c.drawImage(pil_to_rl(guide),
                            sx+pad, ry+pad,
                            width=sq-2*pad, height=sq-2*pad, mask="auto")


# ─────────────────────────────────────────────────────────────────────────────
#  TẠO FILE PDF ĐA TRANG
# ─────────────────────────────────────────────────────────────────────────────

def generate_workbook_pdf(groups: list, output_path: str,
                          cfg: "LayoutConfig | None" = None,
                          progress_callback=None):
    """
    Tạo PDF luyện viết.
    groups: list of (group_text, list_of_(char, pinyin, nghia, strokes))

    Layout:
    - Không có banner riêng. Tên cụm hiển thị nhỏ trong header của chữ ĐẦU TIÊN.
    - Vẽ liên tục, sang trang chỉ khi block tiếp theo không vừa.
    - Không đẩy sớm → tận dụng tối đa diện tích trang.
    """
    if cfg is None:
        cfg = LayoutConfig()

    total_chars = sum(len(chars) for _, chars in groups)
    done        = 0

    c     = rl_canvas.Canvas(output_path, pagesize=A4)
    cur_y = PAGE_H - MARGIN_Y
    
    # Vẽ header trang đầu tiên
    _draw_header(c)

    def new_page():
        nonlocal cur_y
        _draw_footer(c)
        c.showPage()
        _draw_header(c)  # Vẽ header cho trang mới
        cur_y = PAGE_H - MARGIN_Y

    for group_text, char_list in groups:
        is_multi = len(group_text) > 1

        for char_idx, (char, pinyin, nghia, strokes) in enumerate(char_list):
            done += 1
            if progress_callback:
                progress_callback(done, total_chars, f"Đang xử lý: {char}")

            blk_h = cfg.block_total_h(len(strokes))

            # Sang trang nếu block không vừa
            if cur_y - blk_h < MARGIN_Y:
                new_page()

            # Nhãn cụm: chỉ gắn vào chữ đầu tiên của cụm đa chữ
            lbl = group_text if (is_multi and char_idx == 0) else ""

            block_bottom = cur_y - blk_h
            try:
                draw_char_block(c, char, strokes,
                                MARGIN_X, block_bottom,
                                pinyin, nghia, cfg=cfg,
                                group_label=lbl)
            except Exception as e:
                print(f"Lỗi vẽ block '{char}': {e}", file=sys.stderr)

            cur_y = block_bottom - cfg.blk_gap

    _draw_footer(c)
    c.save()

    if progress_callback:
        progress_callback(total_chars, total_chars, "Hoàn thành!")


def _draw_header(c):
    """Vẽ thông tin khóa học ở góc trên bên trái (dùng PIL để hỗ trợ tiếng Việt)."""
    text = "Khóa 23 ngành Ngôn Ngữ Trung"
    
    # Tạo ảnh PIL với text tiếng Việt
    font_size = 32  # tăng kích thước để render rõ hơn
    font = pil_font(_VI_FONT_PATH, font_size)
    
    # Ước tính kích thước text với padding lớn hơn
    dummy_img = Image.new("RGB", (1, 1), "white")
    draw = ImageDraw.Draw(dummy_img)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    # Tạo ảnh với padding nhiều hơn (đặc biệt ở trên và dưới)
    pad_x = 8
    pad_y = 12  # padding dọc lớn hơn để không bị cắt chân chữ
    img_w = text_w + pad_x * 2
    img_h = int(font_size * 1.5)  # chiều cao = 1.5 lần font size để chắc chắn
    
    # Tạo ảnh trong suốt với text
    img = Image.new("RGBA", (img_w, img_h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    # Vẽ text với offset y để căn giữa
    draw.text((pad_x, pad_y), text, font=font, fill=(77, 77, 102))
    
    # Vẽ lên canvas với tỷ lệ đúng
    img_h_pt = 11  # chiều cao hiển thị trên PDF (points)
    img_w_pt = img_w * img_h_pt / img_h
    
    c.drawImage(pil_to_rl(img), MARGIN_X, PAGE_H - MARGIN_Y + 10, 
                width=img_w_pt, height=img_h_pt, mask="auto")


def _draw_footer(c):
    # Thông tin nguồn dữ liệu (giữa trang)
    c.setFont("Helvetica", 6.5)
    c.setFillColorRGB(0.70, 0.70, 0.70)
    c.drawCentredString(
        PAGE_W / 2, 18,
        "Du lieu net: Make Me A Hanzi / hanzi-writer-data (CC BY 4.0)"
    )
    
    # Tên tác giả (góc dưới phải - gọn gàng)
    c.setFont("Helvetica-Oblique", 7)
    c.setFillColorRGB(0.60, 0.60, 0.60)
    c.drawRightString(PAGE_W - MARGIN_X, 18, "Created by Andrew Tseng")


# ─────────────────────────────────────────────────────────────────────────────
#  GUI APPLICATION
# ─────────────────────────────────────────────────────────────────────────────

class HanziWorkbookApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Tạo Tập Luyện Viết Chữ Hán - EHOU - ONT K23")
        self.root.geometry("720x640")
        self.root.resizable(True, True)

        self.output_var = tk.StringVar(value="tap_luyen_chu_han.pdf")
        self.status_var = tk.StringVar(value="Sẵn sàng.")

        self._build_ui()

        if not _CJK_FONT_PATH:
            messagebox.showwarning(
                "Cảnh báo font",
                "Không tìm thấy font CJK.\n"
                "Chữ Hán có thể không hiển thị đúng trong PDF."
            )

    # ── Build UI ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Title
        tk.Label(self.root,
                 text="📝  TẠO TẬP LUYỆN VIẾT CHỮ HÁN",
                 font=("Segoe UI", 15, "bold"), fg="#1a1a2e"
                 ).pack(pady=10)

        # Input frame
        frm_in = ttk.LabelFrame(self.root,
                                 text="Nhập danh sách chữ Hán", padding=10)
        frm_in.pack(fill="both", expand=True, padx=18, pady=5)

        tk.Label(frm_in,
                 text="Nhập hoặc dán chữ Hán (cách nhau bằng dấu cách / xuống dòng):",
                 font=("Segoe UI", 9), fg="#555"
                 ).pack(anchor="w")

        tf = tk.Frame(frm_in)
        tf.pack(fill="both", expand=True, pady=4)
        sb = ttk.Scrollbar(tf); sb.pack(side="right", fill="y")

        try:
            input_font = ("Microsoft YaHei", 13)
            tk.Label(frm_in, text="", font=input_font)
        except Exception:
            input_font = ("TkDefaultFont", 13)

        self.txt = tk.Text(tf, font=input_font, height=6,
                           yscrollcommand=sb.set, wrap="word")
        self.txt.pack(side="left", fill="both", expand=True)
        sb.config(command=self.txt.yview)
        self.txt.insert("1.0", "你 好 学 中 水 龙 爱")

        # Settings frame (output + size chung 1 dòng)
        frm_cfg = ttk.LabelFrame(self.root, text="Cài đặt xuất file", padding=10)
        frm_cfg.pack(fill="x", padx=18, pady=5)

        # Hàng 1: đường dẫn file
        row1 = tk.Frame(frm_cfg); row1.pack(fill="x", pady=2)
        tk.Label(row1, text="Tên file:", font=("Segoe UI", 9), width=9
                 ).pack(side="left")
        ttk.Entry(row1, textvariable=self.output_var, width=38
                  ).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(row1, text="Chọn…", command=self._browse
                   ).pack(side="left")

        # Hàng 2: chỉ còn số dòng luyện tập
        row2 = tk.Frame(frm_cfg); row2.pack(fill="x", pady=2)

        tk.Label(row2, text="Số dòng:", font=("Segoe UI", 9), width=9
                 ).pack(side="left")
        self.rows_var = tk.IntVar(value=3)
        rows_sb = ttk.Spinbox(
            row2, from_=1, to=10,
            textvariable=self.rows_var,
            width=4, state="readonly",
            command=self._update_estimate,
        )
        rows_sb.pack(side="left", padx=4)
        tk.Label(row2, text="dòng  (ô 12mm, 15 ô/dòng)",
                 font=("Segoe UI", 9), fg="#555"
                 ).pack(side="left", padx=(4, 16))

        self.est_var = tk.StringVar()
        tk.Label(row2, textvariable=self.est_var,
                 font=("Segoe UI", 8), fg="#777"
                 ).pack(side="left")

        self._update_estimate()

        # Hàng 3: Tùy chọn lọc thông minh
        row3 = tk.Frame(frm_cfg)
        row3.pack(fill="x", pady=2)
        
        self.dedup_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(row3, text="Lọc bỏ các chữ trùng lặp", variable=self.dedup_var).pack(side="left", padx=(0, 16))
        
        self.skip_basic_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(row3, text="Bỏ qua các chữ quá cơ bản (< 4 nét)", variable=self.skip_basic_var).pack(side="left")

        # Action button
        self.btn = tk.Button(
            self.root,
            text="🚀  BẮT ĐẦU XUẤT FILE PDF",
            font=("Segoe UI", 12, "bold"),
            bg="#e63946", fg="white",
            activebackground="#d62839", activeforeground="white",
            padx=28, pady=10, cursor="hand2",
            command=self._start
        )
        self.btn.pack(pady=10)

        # Progress
        frm_pg = ttk.LabelFrame(self.root, text="Tiến trình", padding=8)
        frm_pg.pack(fill="x", padx=18, pady=4)
        self.pb = ttk.Progressbar(frm_pg, mode="determinate", length=640)
        self.pb.pack(fill="x", pady=4)
        
        lbl_status = tk.Label(frm_pg, textvariable=self.status_var,
                              font=("Segoe UI", 9), fg="#555")
        lbl_status.pack(side="left", anchor="w")
        
        lbl_author = tk.Label(frm_pg, text="© Andrew Tseng",
                              font=("Segoe UI", 8, "italic"), fg="#888")
        lbl_author.pack(side="right", anchor="e")

    def _update_estimate(self):
        """Ước tính số chữ/trang theo số dòng đã chọn."""
        rows = max(1, self.rows_var.get())
        cfg  = LayoutConfig(rows)
        blk  = cfg.block_total_h(8)
        per_page = max(1, int((PAGE_H - 2 * MARGIN_Y) / (blk + cfg.blk_gap)))
        self.est_var.set(f"≈ {per_page} chữ/trang  ·  {rows * cfg.cols} ô/chữ")

    # ── Callbacks ────────────────────────────────────────────────────────────
    def _browse(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf"), ("Tất cả", "*.*")],
            initialfile=self.output_var.get()
        )
        if path:
            self.output_var.set(path)

    def _parse_groups(self, text: str) -> list[list[str]]:
        """
        Tách input thành danh sách CỤM từ, giữ nguyên thứ tự.

        Logic:
        - Dấu phân cách cụm: dấu phẩy ',', dấu chấm phẩy ';', xuống dòng
        - Trong mỗi cụm: lấy tất cả chữ Hán liên tiếp
        - Khoảng trắng giữa các chữ TRONG cùng một cụm được bỏ qua
        - Chữ đơn lẻ (1 chữ) vẫn là 1 cụm riêng
        - Loại bỏ trùng lặp toàn cục (cùng tổ hợp cụm)

        Ví dụ: "各种各样, 打交道, 学 习, 水"
        → [['各','种','各','样'], ['打','交','道'], ['学','习'], ['水']]
        """
        # Tách theo dấu phân cách cụm
        separators = re.compile(r'[,，;；\n]+')
        raw_groups = separators.split(text)

        seen_groups = set()
        result = []

        for raw in raw_groups:
            # Lấy tất cả chữ Hán trong đoạn này (bỏ qua khoảng trắng)
            chars = re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', raw)
            if not chars:
                continue
            key = "".join(chars)
            if key in seen_groups:
                continue
            seen_groups.add(key)
            result.append(chars)

        return result

    # Giữ lại _parse_chars cho ước tính (đếm tổng chữ)
    def _parse_chars(self, text: str) -> list[str]:
        """Đếm tổng số chữ Hán duy nhất (dùng cho ước tính)."""
        seen, result = set(), []
        for ch in re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', text):
            if ch not in seen:
                seen.add(ch); result.append(ch)
        return result

    def _update_progress(self, cur: int, total: int, msg: str):
        self.pb["value"] = cur / total * 100
        self.status_var.set(f"{msg}  ({cur}/{total})")
        self.root.update_idletasks()

    def _start(self):
        text   = self.txt.get("1.0", "end-1c")
        groups = self._parse_groups(text)

        if not groups:
            messagebox.showerror("Lỗi", "Vui lòng nhập ít nhất một chữ Hán!")
            return

        total = sum(len(g) for g in groups)
        out   = self.output_var.get()
        if not out.endswith(".pdf"):
            out += ".pdf"

        rows = max(1, self.rows_var.get())
        cfg  = LayoutConfig(rows)

        self.btn.config(state="disabled")
        self.pb["value"] = 0
        self.status_var.set(f"Chuẩn bị {total} chữ trong {len(groups)} cụm…")

        dedup = self.dedup_var.get()
        skip_basic = self.skip_basic_var.get()

        threading.Thread(target=self._worker,
                         args=(groups, out, cfg, dedup, skip_basic), daemon=True).start()

    def _worker(self, groups: list, out: str, cfg: LayoutConfig, dedup: bool, skip_basic: bool):
        try:
            # Thu thập tất cả chữ cần tải (duy nhất theo cụm, giữ thứ tự)
            all_chars_flat: list[str] = []
            seen_chars: set[str] = set()
            for group in groups:
                for ch in group:
                    if ch not in seen_chars:
                        seen_chars.add(ch)
                        all_chars_flat.append(ch)

            total = len(all_chars_flat)

            # Tải dữ liệu nét & tra từ điển
            stroke_cache: dict[str, list] = {}
            dict_cache: dict[str, dict] = {}
            
            # 1. Tra cứu từ điển hàng loạt trước
            self.root.after(0, lambda: self.status_var.set("Đang tra cứu từ điển..."))
            try:
                dict_cache = fetch_dictionary_data_bulk(all_chars_flat)
            except Exception as e:
                print(f"Lỗi tra từ điển hàng loạt: {e}", file=sys.stderr)
            
            # 2. Tải dữ liệu nét
            for i, ch in enumerate(all_chars_flat, 1):
                self.root.after(0, lambda c=i, t=total, h=ch:
                                self._update_progress(c, t, f"Tải dữ liệu nét: {h}"))
                try:
                    d = fetch_character_data(ch)
                    stroke_cache[ch] = d["strokes"]
                except Exception as e:
                    self.root.after(0, lambda h=ch, err=str(e):
                                    messagebox.showwarning(
                                        "Bỏ qua",
                                        f"Không tải được '{h}': {err}\n"
                                        "Chữ này sẽ bị bỏ qua."))

            # Xây dựng groups data cho PDF (tự động lấy Pinyin và Nghĩa Hán-Việt)
            pdf_groups = []
            practiced_chars = set()
            for group in groups:
                group_text = "".join(group)
                char_list  = []
                for ch in group:
                    if ch in stroke_cache:
                        strokes_data = stroke_cache[ch]
                        
                        # Logic lọc chữ
                        if dedup and ch in practiced_chars:
                            continue
                        if skip_basic and len(strokes_data) < 4:
                            practiced_chars.add(ch) # Đánh dấu đã xét
                            continue
                            
                        practiced_chars.add(ch)
                        
                        ch_info = dict_cache.get(ch, {"pinyin": "", "nghia": ""})
                        py = ch_info.get("pinyin", "")
                        ng = ch_info.get("nghia", "")
                        char_list.append((ch, py, ng, strokes_data))
                if char_list:
                    pdf_groups.append((group_text, char_list))

            if not pdf_groups:
                raise RuntimeError("Không có ký tự hợp lệ nào.")

            self.root.after(0, lambda: self.status_var.set("Đang tạo PDF…"))
            generate_workbook_pdf(
                pdf_groups, out,
                cfg=cfg,
                progress_callback=lambda c, t, m: self.root.after(
                    0, lambda: self._update_progress(c, t, m))
            )
            self.root.after(0, lambda: self._done(out))

        except Exception as e:
            self.root.after(0, lambda: self._error(str(e)))

    def _done(self, filepath: str):
        self.btn.config(state="normal")
        self.pb["value"] = 100
        self.status_var.set("✓ Hoàn thành!")
        if messagebox.askyesno(
            "Thành công",
            f"Đã tạo file PDF:\n\n{filepath}\n\nMở file ngay?"
        ):
            try:
                os.startfile(filepath)
            except AttributeError:
                import subprocess
                for cmd in [["open", filepath], ["xdg-open", filepath]]:
                    try: subprocess.Popen(cmd); break
                    except Exception: pass

    def _error(self, msg: str):
        self.btn.config(state="normal")
        self.status_var.set("Lỗi!")
        messagebox.showerror("Lỗi", f"Không thể tạo PDF:\n\n{msg}")


# ─────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    if sys.version_info < (3, 10):
        print(f"Cần Python 3.10+, hiện tại: {sys.version}", file=sys.stderr)
        sys.exit(1)
    try:
        root = tk.Tk()
        HanziWorkbookApp(root)
        root.mainloop()
    except Exception as e:
        import traceback
        try:
            messagebox.showerror("Lỗi khởi động",
                                 f"{e}\n\n{traceback.format_exc()}")
        except Exception:
            print(f"LỖI: {e}", file=sys.stderr)
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
