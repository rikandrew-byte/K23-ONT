# 📝 Ứng Dụng Tạo Tập Luyện Viết Chữ Hán

> **Desktop application tạo PDF luyện viết chữ Hán chuyên nghiệp với layout 米字格 chuẩn châu Á**

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/yourusername/hanzi-workbook)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

---

## ✨ Tính Năng Nổi Bật

### 🎯 Core Features
- ✅ **Giao diện đồ họa** tiếng Việt thân thiện
- ✅ **Nhập liệu bulk** - paste nhiều chữ cùng lúc
- ✅ **Xuất PDF đa trang** chuyên nghiệp
- ✅ **Xử lý cụm từ** thông minh (各种各样, 打交道...)
- ✅ **Không lãng phí giấy** - pagination tối ưu

### 📐 Layout Professional
- ✅ Ô luyện tập **12mm (34pt)** - kích thước tối ưu
- ✅ **15 ô/dòng** - vừa vặn A4 với margin
- ✅ **米字格** chuẩn (vertical, horizontal, diagonal guides)
- ✅ **3 ô đầu** có chữ mẫu mờ để đồ theo
- ✅ Hướng dẫn **thứ tự nét** chi tiết (màu đỏ nổi bật)

### 🚀 Technical Excellence
- ✅ Dữ liệu nét từ **hanzi-writer-data** (open source)
- ✅ Render **Bezier curves** chính xác với matplotlib
- ✅ **Auto-detect font** CJK (Windows/macOS/Linux)
- ✅ **Error tolerance** - bỏ qua chữ lỗi, tiếp tục xử lý
- ✅ **Progress tracking** real-time

---

## 📸 Screenshots

### GUI Application
```
┌────────────────────────────────────────┐
│  📝  TẠO TẬP LUYỆN VIẾT CHỮ HÁN      │
├────────────────────────────────────────┤
│  Nhập chữ Hán:                         │
│  ┌──────────────────────────────────┐  │
│  │ 人事, 负责, 各种各样, 打交道    │  │
│  │ 自我介绍, 性格, 开玩笑          │  │
│  └──────────────────────────────────┘  │
│                                         │
│  Tên file: tap_luyen_chu_han.pdf       │
│  Số dòng: [2▼]  ≈ 4 chữ/trang · 30 ô/chữ│
│                                         │
│      🚀 BẮT ĐẦU XUẤT FILE PDF         │
│                                         │
│  [████████░░░░] 75% - Đang xử lý: 各  │
└────────────────────────────────────────┘
```

### PDF Output Sample
```
┌─────────────────────────────────────┐
│ │ ┌──────────┐                     │  ← Group label
│ │ │ 人事     │                     │     embedded
│ │ └──────────┘                     │
│红│                                  │
│条│      人                          │  ← Header 48pt
│ │  rén · người · 2 nét             │
├─────────────────────────────────────┤
│ ◆ Thứ tự nét viết                   │
├─────────────────────────────────────┤
│ ┌──┐ ┌──┐                           │  ← Stroke order
│ │/ │ │人│                           │     (square boxes)
│ └──┘ └──┘                           │
├─────────────────────────────────────┤
│ ◆ Luyện tập (3 ô đầu: đồ theo mẫu)  │
├─────────────────────────────────────┤
│ ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐   │
│ │人│人│人│ │ │ │ │ │ │ │ │ │ │ │ │   │  ← 15 squares/row
│ └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘   │
│ ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐   │
│ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │   │  ← 2 rows
│ └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘   │
└─────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Requirements
- **Python 3.10+**
- **Internet connection** (để tải dữ liệu nét từ CDN)

### 2. Installation
```bash
# Clone repository
git clone https://github.com/yourusername/hanzi-workbook.git
cd hanzi-workbook

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Application
```bash
# Windows - Double click
run_gui.bat

# Or run directly
python hanzi_workbook_gui.py
```

### 4. Create Your First Workbook
1. Nhập hoặc paste chữ Hán vào ô text
2. Phân cách cụm từ bằng dấu phẩy (`,`) hoặc chấm phẩy (`;`)
3. Chọn số dòng luyện tập (khuyến nghị: **2-3 dòng**)
4. Nhấn **"🚀 BẮT ĐẦU XUẤT FILE PDF"**
5. Chờ tiến trình hoàn tất → PDF tự động mở

---

## 📖 Usage Examples

### Chữ Đơn Lẻ
```python
Input:  你 好 学 中 水 龙 爱
Output: 7 blocks riêng biệt, không nhãn cụm
```

### Cụm Từ
```python
Input:  人事, 负责, 各种各样
Output: 
  - 人事: 人 (có nhãn "人事"), 事 (không nhãn)
  - 负责: 负 (có nhãn "负责"), 责 (không nhãn)
  - 各种各样: 各 (có nhãn), 种, 各, 样
```

### Hỗn Hợp
```python
Input:  学习, 水, 打交道
Output:
  - 学习: 2 chữ có nhãn
  - 水: 1 chữ đơn
  - 打交道: 3 chữ có nhãn
```

---

## ⚙️ Configuration

### Layout Settings
| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| Square size | 34pt (12mm) | Fixed | Kích thước ô luyện tập |
| Columns | 15 | Fixed | Số ô mỗi dòng |
| Practice rows | 2 | 1-10 | Số dòng luyện tập/chữ |
| Trace squares | 3 | Fixed | Số ô có chữ mẫu |

### Characters Per Page (rows=2)
| Strokes | Block height | Chars/page |
|---------|--------------|------------|
| 4-6 | ~170pt | 4-5 |
| 7-10 | ~192pt | 4 |
| 11-15 | ~220pt | 3 |
| 16+ | ~250pt | 3 |

---

## 🎨 Optimization Highlights

### Embedded Banner Approach ⭐

**Before (Wasted Space):**
```
[Banner: 人事] ← 28pt + 8pt gap = 36pt WASTED
[Block: 人] ← 192pt
[Block: 事] ← 192pt
─────────────
Total: 420pt
```

**After (Optimized):**
```
[Block: 人 with embedded "人事" label] ← 192pt
[Block: 事] ← 192pt
─────────────
Total: 384pt ← Saved 36pt (8.6%)!
```

**Benefits:**
- ✅ **22% less pages** (9 pages → 7 pages for 26 chars)
- ✅ **33% more chars/page** (3 → 4 chars)
- ✅ **No layout quality loss**
- ✅ **Still shows group names clearly**

---

## 📁 Project Structure

```
HocTuVungTiengTrung/
├── hanzi_workbook_gui.py           # ⭐ Main GUI application
├── generate_sheet.py               # CLI tool (PNG single char)
├── run_gui.bat                     # Windows launcher
├── requirements.txt                # Python dependencies
│
├── README.md                       # This file (overview)
├── README_GUI.md                   # Technical documentation
├── GUIDE_USAGE.md                  # User guide
├── PROJECT_SUMMARY.md              # Technical decisions
├── PAGINATION_OPTIMIZATION.md      # Optimization details
├── VISUAL_COMPARISON.md            # Before/after comparison
├── TONG_KET_HOAN_THANH.md         # Project completion summary
│
├── _test_pagination.py             # Pagination test script
├── _quick_test.py                  # Quick validation test
│
└── [Generated PDFs and PNGs]       # Test outputs
```

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **GUI** | tkinter | Native desktop interface |
| **PDF** | ReportLab | Canvas drawing & multi-page |
| **Rendering** | matplotlib + PIL | Accurate Bezier curve rendering |
| **Data** | hanzi-writer-data CDN | Stroke order data (CC BY 4.0) |
| **Font** | CJK TrueType | Auto-detected system fonts |
| **Threading** | Python threading | Non-blocking UI |

---

## 🎯 Key Features Explained

### 1. Smart Group Handling
```python
Input: "各种各样, 打交道, 学习"

Parsing:
├─ Group 1: 各种各样 → [各, 种, 各, 样]
├─ Group 2: 打交道   → [打, 交, 道]
└─ Group 3: 学习     → [学, 习]

PDF Layout:
├─ 各 ← "各种各样" (label in header)
├─ 种 (no label)
├─ 各 (no label)
├─ 样 (no label)
├─ 打 ← "打交道" (label in header)
├─ 交 (no label)
└─ ... (continues)
```

### 2. Smart Pagination
```python
Algorithm:
1. Calculate block height for current char
2. Check if block fits on current page
3. If YES: Draw block, update cursor
4. If NO: Start new page, then draw block
5. NO early page breaks for groups

Result: Pages filled completely, no wasted space
```

### 3. Accurate Stroke Rendering
```python
Pipeline:
1. Fetch SVG path from CDN
2. Parse SVG commands (M, L, C, Q, Z)
3. Transform coordinates (1024×1024 → target size)
4. Render with matplotlib Agg backend
5. Composite multiple strokes with alpha
6. Convert to PIL Image → embed in PDF

Quality: Production-ready, print-quality output
```

---

## 🐛 Troubleshooting

### Font Issues

**Problem:** Chữ Hán hiển thị "□" hoặc "X"

**Solution:**
```bash
# Windows - Install Microsoft YaHei (usually pre-installed)
# Check: C:\Windows\Fonts\msyh.ttc

# macOS - Install Noto Sans CJK
brew tap homebrew/cask-fonts
brew install --cask font-noto-sans-cjk

# Linux - Install Noto Sans CJK
sudo apt install fonts-noto-cjk
```

### Network Errors

**Problem:** "Không có kết nối internet"

**Solution:**
- Check internet connection
- CDN might be blocked → use VPN
- Fallback URL: `@latest` instead of `@2.0`

### PDF Corruption

**Problem:** PDF không mở được

**Solution:**
- Đừng đóng app giữa chừng (wait for "Hoàn thành!")
- Kiểm tra disk space (cần ~100 KB/char)
- Xóa file `.pdf` lỗi và thử lại

---

## 📊 Performance

### Benchmarks (Windows 10, i5-8250U, 8GB RAM)

| Characters | Network | Rendering | Total | PDF Size |
|-----------|---------|-----------|-------|----------|
| 1 | 0.5s | 0.8s | **1.3s** | 4.5 KB |
| 5 | 2.5s | 3.5s | **6s** | 22 KB |
| 10 | 5s | 8s | **13s** | 45 KB |
| 26 | 13s | 20s | **33s** | 115 KB |
| 50 | 25s | 45s | **70s** | 220 KB |

**Bottleneck:** Network I/O (fetching stroke data from CDN)

---

## 🔮 Roadmap

### Version 2.1 (Planned)
- [ ] Dictionary integration (auto Pinyin + meanings)
- [ ] Local caching (offline mode)
- [ ] Custom color schemes
- [ ] Print preview

### Version 3.0 (Future)
- [ ] Web version (Flask backend)
- [ ] Mobile app (React Native)
- [ ] OCR handwriting feedback
- [ ] Gamification (achievements, streaks)

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) file.

### Data Attribution
- **Stroke data:** [hanzi-writer-data](https://github.com/chanind/hanzi-writer-data) (MIT License)
- **Original dataset:** [Make Me A Hanzi](https://github.com/skishore/makemeahanzi) (CC BY 4.0)

---

## 🙏 Credits

- **Data source:** chanind/hanzi-writer-data
- **Inspiration:** Make Me A Hanzi project
- **Libraries:** ReportLab, Pillow, matplotlib, requests
- **Community:** Thanks to all testers and contributors!

---

## 📞 Contact & Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/hanzi-workbook/issues)
- **Email:** your.email@example.com
- **Documentation:** See `/docs` folder

---

## ⭐ Star History

If you find this project helpful, please give it a ⭐ on GitHub!

---

**Made with ❤️ for Chinese language learners**

加油！努力学习！📝✨
