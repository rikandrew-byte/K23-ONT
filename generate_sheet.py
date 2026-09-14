#!/usr/bin/env python3
"""
Bảng luyện viết chữ Hán (Hanzi Practice Sheet Generator)
==========================================================
Tạo file PNG luyện viết cho một chữ Hán bất kỳ.

Cách dùng:
    python generate_sheet.py --char 你
    python generate_sheet.py --char 好 --pinyin hǎo --nghia "tốt; giỏi"
    python generate_sheet.py --char 水 --output bang_luyen.png

Thư viện cần cài:
    pip install matplotlib pillow requests

Nguồn dữ liệu nét:
    hanzi-writer-data (CC BY 4.0) qua jsDelivr CDN
    https://github.com/chanind/hanzi-writer-data
"""

import argparse
import sys
import json
import re
import math
import warnings
import os
import requests
from pathlib import Path

# ── Thiết lập font CJK TRƯỚC KHI import pyplot ──────────────────────────────
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm


# ─────────────────────────────────────────────────────────────────────────────
#  ĐĂNG KÝ FONT CJK – phải chạy trước khi dùng pyplot
# ─────────────────────────────────────────────────────────────────────────────

# Danh sách font ưu tiên (tên file, không phân biệt hoa thường)
_CJK_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",          # Microsoft YaHei  (Windows)
    r"C:\Windows\Fonts\simsun.ttc",        # SimSun           (Windows)
    r"C:\Windows\Fonts\STKAITI.TTF",       # STKaiti          (Windows/macOS)
    r"C:\Windows\Fonts\mingliu.ttc",       # MingLiU          (Windows)
    "/System/Library/Fonts/PingFang.ttc",  # PingFang         (macOS)
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",   # Noto CJK (Linux)
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",             # WQY (Linux)
]

# Tìm kiếm mở rộng qua font_manager nếu danh sách cứng thất bại
_CJK_SEARCH_KEYWORDS = ["msyh", "simsun", "kaiti", "mingliu", "noto", "wqy", "pingfang"]


def _setup_cjk_font() -> str | None:
    """
    Đăng ký một font CJK vào matplotlib và trả về tên font đã đăng ký.
    Trả về None nếu không tìm thấy font nào phù hợp.
    """
    from matplotlib.ft2font import FT2Font

    def supports_cjk(path: str) -> bool:
        """Kiểm tra font có hỗ trợ chữ Hán cơ bản không (thử ký tự 中 và 赢)."""
        try:
            f = FT2Font(path)
            return f.get_char_index(ord("中")) > 0 and f.get_char_index(ord("赢")) > 0
        except Exception:
            return False

    # 1. Thử danh sách cứng trước
    for path in _CJK_FONT_CANDIDATES:
        if os.path.isfile(path) and supports_cjk(path):
            fm.fontManager.addfont(path)
            name = fm.FontProperties(fname=path).get_name()
            matplotlib.rcParams["font.family"] = name
            matplotlib.rcParams["axes.unicode_minus"] = False
            return path

    # 2. Quét toàn bộ font hệ thống
    for path in fm.findSystemFonts():
        low = path.lower()
        if any(k in low for k in _CJK_SEARCH_KEYWORDS):
            if supports_cjk(path):
                fm.fontManager.addfont(path)
                name = fm.FontProperties(fname=path).get_name()
                matplotlib.rcParams["font.family"] = name
                matplotlib.rcParams["axes.unicode_minus"] = False
                return path

    return None


# Chạy ngay khi import module
_CJK_FONT_PATH = _setup_cjk_font()
_CJK_FONT_PROP_CACHE: dict[float, fm.FontProperties] = {}


def get_cjk_prop(size: float) -> fm.FontProperties:
    """Trả về FontProperties CJK cho kích thước cho trước (có cache)."""
    if size not in _CJK_FONT_PROP_CACHE:
        if _CJK_FONT_PATH:
            _CJK_FONT_PROP_CACHE[size] = fm.FontProperties(fname=_CJK_FONT_PATH, size=size)
        else:
            _CJK_FONT_PROP_CACHE[size] = fm.FontProperties(size=size)
    return _CJK_FONT_PROP_CACHE[size]


import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path as MplPath
import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
#  HẰNG SỐ & BỐ CỤC TRANG
# ─────────────────────────────────────────────────────────────────────────────

# Không gian tọa độ Hanzi Writer: 1024 × 1024, trục y hướng lên
HW_SIZE = 1024.0

# URL dữ liệu nét từ CDN jsDelivr
CDN_URL        = "https://cdn.jsdelivr.net/npm/hanzi-writer-data@2.0/{char}.json"
CDN_URL_LATEST = "https://cdn.jsdelivr.net/npm/hanzi-writer-data@latest/{char}.json"

# Màu sắc
COL_STROKE        = "#1a1a2e"   # Nét đã hoàn thành – xanh đậm
COL_CURRENT       = "#e63946"   # Nét mới thêm vào – đỏ
COL_GRID_OUTER    = "#444444"   # Viền ô luyện
COL_GRID_DASH     = "#bbbbbb"   # Đường kẻ phụ bên trong ô
COL_HEADER_BG     = "#f7f7f7"   # Nền tiêu đề
COL_SECTION_TITLE = "#555555"   # Màu nhãn section
COL_ACCENT_BAR    = "#e63946"   # Thanh trang trí bên trái header

# Kích thước trang (inches)
PAGE_WIDTH   = 8.5
PAGE_DPI     = 150

# Chiều cao các section (inches)
H_HEADER      = 1.40
H_SECTION_LBL = 0.28
H_STEP_ROW    = 1.00   # chiều cao 1 hàng bảng thứ tự nét
H_PRACTICE    = 1.05   # chiều cao 1 hàng luyện tập
PRACTICE_ROWS = 3
PRACTICE_COLS = 10
TRACE_SQUARES = 3      # 3 ô đầu có chữ mẫu mờ

MARGIN_X = 0.30   # inch lề trái/phải
MARGIN_Y = 0.20   # inch lề trên/dưới

# Số nét tối đa hiển thị trên 1 hàng bảng thứ tự nét
MAX_STEPS_PER_ROW = 16


# ─────────────────────────────────────────────────────────────────────────────
#  CACHE & LẤY DỮ LIỆU
# ─────────────────────────────────────────────────────────────────────────────

CACHE_DIR = Path("cache")
STROKES_CACHE_DIR = CACHE_DIR / "strokes"
DICT_CACHE_DIR = CACHE_DIR / "dict"

STROKES_CACHE_DIR.mkdir(parents=True, exist_ok=True)
DICT_CACHE_DIR.mkdir(parents=True, exist_ok=True)

def fetch_character_data(char: str) -> dict:
    """
    Tải dữ liệu nét từ hanzi-writer-data CDN hoặc từ cache cục bộ.
    Trả về dict với 'strokes' và 'medians'.
    Ném RuntimeError nếu thất bại.
    """
    cache_file = STROKES_CACHE_DIR / f"{char}.json"
    if cache_file.is_file():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "strokes" in data and "medians" in data:
                    return data
        except Exception:
            pass

    encoded   = char.encode("utf-8")
    url_char  = "".join(f"%{b:02X}" for b in encoded)
    urls      = [CDN_URL.format(char=url_char), CDN_URL_LATEST.format(char=url_char)]

    for url in urls:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if "strokes" in data and "medians" in data:
                    try:
                        with open(cache_file, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                    except Exception:
                        pass
                    return data
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Không có kết nối internet. Vui lòng kiểm tra mạng và thử lại."
            )
        except requests.exceptions.Timeout:
            raise RuntimeError(
                "Hết thời gian chờ khi tải dữ liệu. Vui lòng thử lại."
            )
        except (json.JSONDecodeError, ValueError):
            continue

    raise RuntimeError(
        f"Không tìm thấy dữ liệu cho ký tự '{char}'. "
        "Có thể đây là ký tự hiếm, dấu câu, hoặc không phải chữ Hán."
    )

def fetch_dict_data(char: str) -> dict:
    """Tra cứu Pinyin và Hán-Việt tự động từ Thi Viện nếu chưa có trong cache."""
    cache_file = DICT_CACHE_DIR / f"{char}.json"
    if cache_file.is_file():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    res = {"pinyin": "", "nghia": ""}
    url = "https://hvdic.thivien.net/transcript-query.json.php"
    headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

    try:
        r = requests.post(url, data={"mode": "trans", "lang": "1", "input": char}, headers=headers, timeout=5)
        if r.status_code == 200:
            d = r.json()
            if "result" in d and d["result"]:
                readings = d["result"][0].get("o")
                if readings: res["nghia"] = readings[0].upper()
    except Exception:
        pass

    try:
        r = requests.post(url, data={"mode": "trans", "lang": "2", "input": char}, headers=headers, timeout=5)
        if r.status_code == 200:
            d = r.json()
            if "result" in d and d["result"]:
                readings = d["result"][0].get("o")
                if readings: res["pinyin"] = readings[0]
    except Exception:
        pass

    if res["pinyin"] or res["nghia"]:
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(res, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    return res


# ─────────────────────────────────────────────────────────────────────────────
#  PHÂN TÍCH SVG PATH
# ─────────────────────────────────────────────────────────────────────────────

def _tokenise_path(d: str):
    """Phân tách chuỗi SVG path thành các token (lệnh, danh sách số)."""
    token_re = re.compile(
        r"([MmZzLlHhVvCcSsQqTtAa])|"
        r"([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)"
    )
    cmd, args = None, []
    for cmd_tok, num_tok in token_re.findall(d):
        if cmd_tok:
            if cmd is not None:
                yield cmd, args
            cmd, args = cmd_tok, []
        elif num_tok:
            args.append(float(num_tok))
    if cmd is not None:
        yield cmd, args


def svg_path_to_mpl(d: str, transform_fn=None):
    """
    Chuyển chuỗi SVG path thành matplotlib Path.
    transform_fn(x, y) -> (x', y') áp dụng cho mọi điểm.
    """
    verts, codes = [], []
    cx, cy = 0.0, 0.0

    def T(x, y):
        return transform_fn(x, y) if transform_fn else (x, y)

    for cmd, args in _tokenise_path(d):
        if cmd in ("M", "m"):
            rel = cmd == "m"
            for i in range(0, len(args), 2):
                x = (cx + args[i]   if rel else args[i])
                y = (cy + args[i+1] if rel else args[i+1])
                verts.append(T(x, y)); codes.append(MplPath.MOVETO)
                cx, cy = x, y
        elif cmd in ("L", "l"):
            rel = cmd == "l"
            for i in range(0, len(args), 2):
                x = (cx + args[i]   if rel else args[i])
                y = (cy + args[i+1] if rel else args[i+1])
                verts.append(T(x, y)); codes.append(MplPath.LINETO)
                cx, cy = x, y
        elif cmd in ("C", "c"):
            rel = cmd == "c"
            for i in range(0, len(args), 6):
                pts = args[i:i+6]
                if len(pts) < 6: break
                if rel:
                    pts = [pts[0]+cx, pts[1]+cy, pts[2]+cx, pts[3]+cy,
                           pts[4]+cx, pts[5]+cy]
                for k in range(0, 6, 2):
                    verts.append(T(pts[k], pts[k+1]))
                codes += [MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4]
                cx, cy = pts[4], pts[5]
        elif cmd in ("Q", "q"):
            rel = cmd == "q"
            for i in range(0, len(args), 4):
                pts = args[i:i+4]
                if len(pts) < 4: break
                if rel:
                    pts = [pts[0]+cx, pts[1]+cy, pts[2]+cx, pts[3]+cy]
                verts.append(T(pts[0], pts[1]))
                verts.append(T(pts[2], pts[3]))
                codes += [MplPath.CURVE3, MplPath.CURVE3]
                cx, cy = pts[2], pts[3]
        elif cmd in ("Z", "z"):
            if verts:
                verts.append(verts[-1]); codes.append(MplPath.CLOSEPOLY)

    return MplPath(verts, codes) if verts else None


# ─────────────────────────────────────────────────────────────────────────────
#  VẼ CHỮ HÁN VÀO AXES
# ─────────────────────────────────────────────────────────────────────────────

def draw_character_in_axes(
    ax,
    strokes: list,
    num_strokes: int,
    highlight_last: bool = False,
    alpha: float = 1.0,
    color_done: str = COL_STROKE,
    color_current: str = COL_CURRENT,
    lw: float = 0.6,
):
    """
    Vẽ num_strokes nét đầu tiên của chữ vào axes ax.

    Tọa độ Hanzi Writer (0–1024, y-tăng lên trên) được ánh xạ sang [0,1]×[0,1].
    Nét cuối cùng được tô màu highlight_color nếu highlight_last=True.
    """
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_aspect("equal"); ax.axis("off")

    PAD   = 0.06
    SCALE = (1.0 - 2 * PAD) / HW_SIZE

    def hw_to_unit(x, y):
        return x * SCALE + PAD, y * SCALE + PAD

    for i, stroke_d in enumerate(strokes[:num_strokes]):
        is_last    = (i == num_strokes - 1)
        fill_color = color_current if (highlight_last and is_last) else color_done
        path       = svg_path_to_mpl(stroke_d, transform_fn=hw_to_unit)
        if path is None:
            continue
        ax.add_patch(patches.PathPatch(
            path,
            facecolor=fill_color, edgecolor=fill_color,
            lw=lw, alpha=alpha, zorder=2 + i,
        ))


# ─────────────────────────────────────────────────────────────────────────────
#  VẼ Ô LUYỆN MIZiGe (米字格)
# ─────────────────────────────────────────────────────────────────────────────

def draw_mizige(ax, x0: float, y0: float, size: float, lw: float = 0.55):
    """
    Vẽ một ô 米字格 vào axes ax.
      - Viền ngoài liền nét
      - Đường ngang/dọc giữa: nét đứt
      - Đường chéo chữ X: nét đứt
    Tọa độ (x0, y0) là góc dưới trái, đơn vị = data coords của ax.
    """
    dash = dict(color=COL_GRID_DASH, linewidth=lw,
                linestyle=(0, (4, 4)), solid_capstyle="round", zorder=1)

    x1 = x0 + size; y1 = y0 + size
    cx = x0 + size / 2; cy = y0 + size / 2

    # Nền trắng + viền ngoài
    ax.add_patch(patches.Rectangle(
        (x0, y0), size, size,
        linewidth=lw * 1.6, edgecolor=COL_GRID_OUTER,
        facecolor="white", zorder=0,
    ))
    # Đường ngang giữa
    ax.plot([x0, x1], [cy, cy], **dash)
    # Đường dọc giữa
    ax.plot([cx, cx], [y0, y1], **dash)
    # Chéo trái-trên → phải-dưới
    ax.plot([x0, x1], [y1, y0], **dash)
    # Chéo trái-dưới → phải-trên
    ax.plot([x0, x1], [y0, y1], **dash)


# ─────────────────────────────────────────────────────────────────────────────
#  LẬP BẢNG LUYỆN VIẾT
# ─────────────────────────────────────────────────────────────────────────────

def build_sheet(
    char: str,
    strokes: list,
    pinyin: str = "",
    nghia: str = "",
    output_path: str = None,
):
    """Tạo và lưu file PNG bảng luyện viết."""

    num_strokes = len(strokes)
    if output_path is None:
        output_path = f"practice_sheet_{char}.png"

    # ── Tính số hàng bảng thứ tự nét ────────────────────────────────────
    # Mỗi hàng tối đa MAX_STEPS_PER_ROW ô; nếu nhiều hơn thì xuống hàng
    n_step_rows = math.ceil(num_strokes / MAX_STEPS_PER_ROW)

    # ── Tính chiều cao trang ─────────────────────────────────────────────
    h_total = (
        MARGIN_Y
        + H_HEADER
        + H_SECTION_LBL
        + n_step_rows * H_STEP_ROW
        + H_SECTION_LBL
        + PRACTICE_ROWS * H_PRACTICE
        + MARGIN_Y
    )

    fig = plt.figure(figsize=(PAGE_WIDTH, h_total), dpi=PAGE_DPI)
    fig.patch.set_facecolor("white")

    # ── Hàm chuyển đổi tọa độ (inches → fraction) ───────────────────────
    def iy(inches_from_top):  return 1.0 - inches_from_top / h_total
    def ih(inches):           return inches / h_total
    def ix(inches_from_left): return inches_from_left / PAGE_WIDTH
    def iw(inches):           return inches / PAGE_WIDTH

    content_w = PAGE_WIDTH - 2 * MARGIN_X   # chiều rộng nội dung (inches)
    draw_y    = MARGIN_Y                     # con trỏ dọc (inches từ trên xuống)

    # ════════════════════════════════════════════════════════════════════
    #  HEADER
    # ════════════════════════════════════════════════════════════════════
    ax_hdr = fig.add_axes([
        ix(MARGIN_X), iy(draw_y + H_HEADER),
        iw(content_w), ih(H_HEADER),
    ])
    ax_hdr.set_xlim(0, 1); ax_hdr.set_ylim(0, 1); ax_hdr.axis("off")

    # Nền header
    ax_hdr.add_patch(patches.FancyBboxPatch(
        (-0.01, -0.05), 1.02, 1.10,
        boxstyle="round,pad=0.01",
        facecolor=COL_HEADER_BG, edgecolor="#dddddd", linewidth=0.8,
        transform=ax_hdr.transAxes, clip_on=False,
    ))

    # Thanh màu trang trí bên trái
    ax_hdr.add_patch(patches.Rectangle(
        (0.175, 0.08), 0.005, 0.84,
        facecolor=COL_ACCENT_BAR, edgecolor="none",
        transform=ax_hdr.transAxes,
    ))

    # Chữ Hán lớn – dùng FontProperties để tránh fallback sang DejaVu
    ax_hdr.text(
        0.04, 0.52, char,
        fontproperties=get_cjk_prop(64),
        ha="left", va="center", color=COL_STROKE,
        transform=ax_hdr.transAxes,
    )

    # Nhãn số nét
    ax_hdr.text(
        0.04, 0.09,
        f"{num_strokes} nét",
        fontsize=9, ha="left", va="bottom",
        color="#888888", transform=ax_hdr.transAxes,
    )

    # Phiên âm (pinyin)
    ax_hdr.text(
        0.21, 0.72,
        pinyin if pinyin else "—",
        fontsize=22, ha="left", va="center",
        color="#333333", transform=ax_hdr.transAxes,
    )

    # Nghĩa tiếng Việt
    ax_hdr.text(
        0.21, 0.36,
        nghia if nghia else "—",
        fontsize=12, ha="left", va="center",
        color="#555555", style="italic",
        transform=ax_hdr.transAxes,
    )

    # Đường kẻ dưới header
    ax_hdr.plot([0, 1], [-0.05, -0.05], color="#cccccc", linewidth=0.5,
                transform=ax_hdr.transAxes, clip_on=False)

    draw_y += H_HEADER


    # ════════════════════════════════════════════════════════════════════
    #  NHÃN "THỨ TỰ NÉT VIẾT"
    # ════════════════════════════════════════════════════════════════════
    ax_lbl1 = fig.add_axes([
        ix(MARGIN_X), iy(draw_y + H_SECTION_LBL),
        iw(content_w), ih(H_SECTION_LBL),
    ])
    ax_lbl1.axis("off"); ax_lbl1.set_xlim(0,1); ax_lbl1.set_ylim(0,1)
    ax_lbl1.text(
        0.0, 0.5, "◆  Thứ tự nét viết",
        fontsize=8.5, va="center", color=COL_SECTION_TITLE,
        fontweight="bold", transform=ax_lbl1.transAxes,
    )
    draw_y += H_SECTION_LBL

    # ════════════════════════════════════════════════════════════════════
    #  BẢNG THỨ TỰ NÉT  – đa hàng nếu cần
    # ════════════════════════════════════════════════════════════════════
    box_gap = 0.03   # khoảng cách giữa các ô (inches)

    for row_idx in range(n_step_rows):
        # Các nét thuộc hàng này
        step_start = row_idx * MAX_STEPS_PER_ROW
        step_end   = min(step_start + MAX_STEPS_PER_ROW, num_strokes)
        n_in_row   = step_end - step_start

        box_w = (content_w - (n_in_row - 1) * box_gap) / n_in_row
        box_h = H_STEP_ROW

        for col_idx in range(n_in_row):
            stroke_num = step_start + col_idx + 1   # 1-indexed
            bx = MARGIN_X + col_idx * (box_w + box_gap)
            by = draw_y

            ax_step = fig.add_axes([
                ix(bx), iy(by + box_h),
                iw(box_w), ih(box_h),
            ])
            ax_step.set_xlim(0, 1); ax_step.set_ylim(0, 1)
            ax_step.set_aspect("equal", adjustable="box")
            ax_step.axis("off")

            # Nền ô
            ax_step.add_patch(patches.Rectangle(
                (0, 0), 1, 1,
                facecolor="#f9f9f9", edgecolor=COL_GRID_DASH,
                linewidth=0.5, transform=ax_step.transAxes,
            ))

            draw_character_in_axes(
                ax_step, strokes,
                num_strokes=stroke_num,
                highlight_last=True,
            )

            # Số thứ tự bên dưới ô
            ax_step.text(
                0.5, -0.12, str(stroke_num),
                fontsize=6, ha="center", va="top",
                color="#888888", transform=ax_step.transAxes,
            )

        draw_y += box_h

    # ════════════════════════════════════════════════════════════════════
    #  NHÃN "LUYỆN TẬP"
    # ════════════════════════════════════════════════════════════════════
    ax_lbl2 = fig.add_axes([
        ix(MARGIN_X), iy(draw_y + H_SECTION_LBL),
        iw(content_w), ih(H_SECTION_LBL),
    ])
    ax_lbl2.axis("off"); ax_lbl2.set_xlim(0,1); ax_lbl2.set_ylim(0,1)
    ax_lbl2.text(
        0.0, 0.5,
        "◆  Luyện tập  (3 ô đầu: đồ theo chữ mẫu)",
        fontsize=8.5, va="center", color=COL_SECTION_TITLE,
        fontweight="bold", transform=ax_lbl2.transAxes,
    )
    draw_y += H_SECTION_LBL


    # ════════════════════════════════════════════════════════════════════
    #  CÁC HÀNG Ô LUYỆN TẬP (米字格)
    # ════════════════════════════════════════════════════════════════════
    sq_gap  = 0.02   # khoảng cách giữa các ô (inches)
    sq_size = (content_w - (PRACTICE_COLS - 1) * sq_gap) / PRACTICE_COLS

    for row_i in range(PRACTICE_ROWS):
        row_top = draw_y + row_i * H_PRACTICE

        # Một Axes chứa toàn bộ 10 ô trong hàng
        ax_row = fig.add_axes([
            ix(MARGIN_X), iy(row_top + H_PRACTICE),
            iw(content_w), ih(H_PRACTICE),
        ])
        ax_row.set_xlim(0, content_w)
        ax_row.set_ylim(0, H_PRACTICE)
        ax_row.set_aspect("equal", adjustable="datalim")
        ax_row.axis("off")

        for col_i in range(PRACTICE_COLS):
            sq_x = col_i * (sq_size + sq_gap)
            sq_y = (H_PRACTICE - sq_size) / 2   # căn giữa dọc

            draw_mizige(ax_row, sq_x, sq_y, sq_size)

            # 3 ô đầu tiên: vẽ chữ mẫu mờ để đồ
            flat_idx = row_i * PRACTICE_COLS + col_i
            if flat_idx < TRACE_SQUARES:
                # Tọa độ figure-fraction cho ô này
                cell_fx = ix(MARGIN_X + sq_x)
                cell_fy = iy(row_top + sq_y + H_PRACTICE - (H_PRACTICE - sq_size) / 2)
                cell_fw = iw(sq_size)
                cell_fh = ih(sq_size)

                ax_guide = fig.add_axes([cell_fx, cell_fy, cell_fw, cell_fh])
                draw_character_in_axes(
                    ax_guide, strokes,
                    num_strokes=num_strokes,
                    highlight_last=False,
                    alpha=0.15,              # mờ vừa đủ để đồ theo
                    color_done=COL_STROKE,
                    color_current=COL_STROKE,
                )

    # ════════════════════════════════════════════════════════════════════
    #  FOOTER
    # ════════════════════════════════════════════════════════════════════
    footer_top = draw_y + PRACTICE_ROWS * H_PRACTICE
    ax_foot = fig.add_axes([
        ix(MARGIN_X), iy(footer_top + MARGIN_Y * 0.9),
        iw(content_w), ih(MARGIN_Y * 0.9),
    ])
    ax_foot.axis("off")
    ax_foot.text(
        0.5, 0.5,
        "Dữ liệu nét: Make Me A Hanzi / hanzi-writer-data (CC BY 4.0)",
        fontsize=5.5, ha="center", va="center",
        color="#bbbbbb", transform=ax_foot.transAxes,
    )

    # ════════════════════════════════════════════════════════════════════
    #  LƯU FILE
    # ════════════════════════════════════════════════════════════════════
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*Glyph.*missing.*font")
        fig.savefig(
            output_path, dpi=PAGE_DPI,
            bbox_inches="tight", facecolor="white", pad_inches=0.1,
        )
    plt.close(fig)
    print(f"✓ Đã lưu: {output_path}")


# ─────────────────────────────────────────────────────────────────────────────
#  ĐIỂM VÀO (CLI)
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Tạo bảng luyện viết chữ Hán (PNG).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  python generate_sheet.py --char 你
  python generate_sheet.py --char 好 --pinyin hao3 --nghia "tốt; giỏi"
  python generate_sheet.py --char 水 --output bang_nuoc.png
        """,
    )
    parser.add_argument("--char",   "-c", required=True,
                        help="Chữ Hán cần tạo bảng (vd: 你)")
    parser.add_argument("--pinyin", "-p", default="",
                        help="Phiên âm pinyin (vd: nǐ)")
    parser.add_argument("--nghia",  "-n", default="",
                        help="Nghĩa tiếng Việt (vd: bạn, anh, chị…)")
    parser.add_argument("--output", "-o", default=None,
                        help="Đường dẫn file output (mặc định: practice_sheet_<char>.png)")

    args = parser.parse_args()

    # ── Kiểm tra đầu vào ─────────────────────────────────────────────────
    char = args.char.strip()
    if not char:
        print("Lỗi: --char không được để trống.", file=sys.stderr)
        sys.exit(1)
    if len(char) > 1:
        print(
            f"Cảnh báo: '{char}' có nhiều hơn 1 ký tự; "
            f"chỉ dùng ký tự đầu tiên: '{char[0]}'",
            file=sys.stderr,
        )
        char = char[0]

    output_path = args.output or f"practice_sheet_{char}.png"

    # ── Thông báo font ────────────────────────────────────────────────────
    if _CJK_FONT_PATH:
        print(f"Font CJK: {os.path.basename(_CJK_FONT_PATH)}")
    else:
        print("Cảnh báo: Không tìm thấy font CJK; chữ trong header có thể hiện sai.",
              file=sys.stderr)

    # ── Tải dữ liệu nét ──────────────────────────────────────────────────
    print(f"Đang tải dữ liệu nét cho '{char}' …")
    try:
        data = fetch_character_data(char)
    except RuntimeError as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        sys.exit(1)

    strokes = data["strokes"]
    if not strokes:
        print(f"Lỗi: Không có dữ liệu nét cho '{char}'.", file=sys.stderr)
        sys.exit(1)

    print(f"  Tìm thấy {len(strokes)} nét.")

    # ── Tra cứu từ điển tự động nếu thiếu ────────────────────────────────
    pinyin = args.pinyin
    nghia = args.nghia
    if not pinyin or not nghia:
        print("Đang tra cứu từ điển (Thi Viện)...")
        dict_data = fetch_dict_data(char)
        if not pinyin:
            pinyin = dict_data.get("pinyin", "")
        if not nghia:
            nghia = dict_data.get("nghia", "")
            
    if pinyin: print(f"  Pinyin: {pinyin}")
    if nghia: print(f"  Nghĩa: {nghia}")

    # ── Tạo bảng luyện ───────────────────────────────────────────────────
    print("Đang tạo bảng luyện viết …")
    try:
        build_sheet(
            char=char,
            strokes=strokes,
            pinyin=pinyin,
            nghia=nghia,
            output_path=output_path,
        )
    except Exception as exc:
        print(f"Lỗi khi tạo bảng: {exc}", file=sys.stderr)
        import traceback; traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
