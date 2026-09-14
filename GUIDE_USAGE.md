# 🎯 Hướng Dẫn Sử Dụng Chi Tiết

## Khởi Động Ứng Dụng

### Cách 1: Double-click file BAT (Windows)
```
Nhấp đúp vào: run_gui.bat
```

### Cách 2: Chạy trực tiếp Python
```bash
python hanzi_workbook_gui.py
```

### Cách 3: Từ Command Line với encoding UTF-8
```bash
chcp 65001
python hanzi_workbook_gui.py
```

---

## Giao Diện Chính

```
┌─────────────────────────────────────────────────────┐
│   📝 TẠO TẬP LUYỆN VIẾT CHỮ HÁN                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─ Nhập danh sách chữ Hán ───────────────────┐   │
│  │ Nhập hoặc dán các chữ Hán muốn luyện...    │   │
│  │                                              │   │
│  │  ┌──────────────────────────────────────┐  │   │
│  │  │ 你 好 学 中 水 龙 爱               │  │   │
│  │  │                                      │  │   │
│  │  │                                      │  │   │
│  │  │  [Font: Microsoft YaHei, 14pt]      │  │   │
│  │  └──────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
│  ┌─ Cài đặt file PDF đầu ra ───────────────────┐   │
│  │ Tên file: [tap_luyen_chu_han.pdf       ]   │   │
│  │          [Chọn thư mục...]                  │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
│          ┌───────────────────────────┐             │
│          │ 🚀 BẮT ĐẦU XUẤT FILE PDF │             │
│          └───────────────────────────┘             │
│                                                     │
│  ┌─ Tiến trình ─────────────────────────────────┐  │
│  │  [████████████████░░░░░░░░░░] 60%           │  │
│  │  Đang xử lý chữ: 学 (6/10)                  │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## Ví Dụ Thực Tế

### Ví Dụ 1: Tạo tập luyện cơ bản (3 chữ)

**Input trong ô text:**
```
你 好 学
```

**Metadata (tùy chọn - hiện tại là placeholder):**
- Pinyin và nghĩa sẽ được thêm trong phiên bản sau
- Hiện tại: chữ Hán + dữ liệu nét + bố cục luyện tập

**Kết quả PDF:**
- File: `tap_luyen_chu_han.pdf`
- Kích thước: ~13 KB
- Số trang: 1 (3 block trên cùng trang)

---

### Ví Dụ 2: Tập luyện nâng cao (chữ nhiều nét)

**Input:**
```
龙 爱 赢
```

**Đặc điểm:**
- 龙 (5 nét): đơn giản
- 爱 (10 nét): trung bình
- 赢 (17 nét): phức tạp, bảng thứ tự nét sẽ dùng 2 hàng (16 + 1)

**Kết quả:**
- File: ~15 KB
- Chữ "赢" có bảng thứ tự nét rộng hơn để hiển thị đủ 17 bước

---

### Ví Dụ 3: Nhập hàng loạt (paste từ list)

**Input (copy từ file/web):**
```
水火木金土
日月星云风
山川河海林
```

**Xử lý:**
1. Script tự động trích xuất tất cả chữ Hán: 水, 火, 木, 金, 土, 日, 月, 星, 云, 风, 山, 川, 河, 海, 林
2. Loại bỏ trùng lặp (nếu có)
3. Tải dữ liệu song song
4. Tạo PDF đa trang

**Thời gian ước tính:** ~25-30 giây cho 15 chữ

---

## Xử Lý Lỗi Phổ Biến

### 1. Lỗi "No module named 'reportlab'"

**Nguyên nhân:** Chưa cài thư viện

**Giải pháp:**
```bash
pip install -r requirements.txt
```

Hoặc:
```bash
pip install reportlab requests pillow
```

---

### 2. Cảnh báo "Không tìm thấy font CJK"

**Nguyên nhân:** Hệ thống không có font hỗ trợ chữ Hán

**Giải pháp:**

**Windows:**
- Thường có sẵn Microsoft YaHei hoặc SimSun
- Nếu không: Control Panel → Fonts → Cài thêm font

**macOS:**
- Có sẵn PingFang
- Nếu lỗi: cài Noto Sans CJK từ Google Fonts

**Linux:**
```bash
sudo apt install fonts-noto-cjk
# hoặc
sudo apt install fonts-wqy-zenhei
```

---

### 3. Ký Tự Không Tìm Thấy

**Popup hiện:**
```
┌─────────────────────────────────┐
│ ⚠️  Cảnh báo                    │
├─────────────────────────────────┤
│ Không thể tải dữ liệu cho '🐉'  │
│ Chữ này sẽ bị bỏ qua.          │
│                                 │
│          [ OK ]                 │
└─────────────────────────────────┘
```

**Nguyên nhân:**
- Emoji không phải chữ Hán
- Ký tự hiếm không có trong database
- Ký tự tiếng Nhật/Hàn Quốc (có thể trùng nhưng không phải Hanzi chuẩn)

**Xử lý:**
- Ký tự đó bị bỏ qua
- Các ký tự khác vẫn được xử lý bình thường

---

## Kết Quả PDF Mẫu

### Cấu Trúc Một Block (Mỗi Chữ)

```
╔═══════════════════════════════════════════════════════╗
║  赢    yíng                                           ║
║  17 nét  chiến thắng; thắng cuộc                      ║
╠═══════════════════════════════════════════════════════╣
║  ◆ Thứ tự nét viết                                    ║
║  ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐  ║
║  │一│ │二│ │三│ │四│ │五│ │六│ │七│ │八│ │九│ │十│ │十│ │十│  ║
║  └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘  ║
║   1   2   3   4   5   6   7   8   9  10  11  12     ║
║  ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐                                ║
║  │十│ │十│ │十│ │十│ │完│                                ║
║  └─┘ └─┘ └─┘ └─┘ └─┘                                ║
║   13  14  15  16  17                                 ║
╠═══════════════════════════════════════════════════════╣
║  ◆ Luyện tập (3 ô đầu: đồ theo chữ mẫu)              ║
║  ┌米┐ ┌米┐ ┌米┐ ┌米┐ ┌米┐ ┌米┐ ┌米┐ ┌米┐ ┌米┐ ┌米┐    ║
║  │赢│ │赢│ │赢│ │  │ │  │ │  │ │  │ │  │ │  │ │  │    ║
║  └字┘ └字┘ └字┘ └格┘ └格┘ └格┘ └格┘ └格┘ └格┘ └格┘    ║
║   ^ mờ  ^ mờ  ^ mờ  [trống x7]                       ║
║                                                       ║
║  ┌米┐ ┌米┐ ┌米┐ ┌米┐ ┌米┐ ┌米┐ ┌米┐ ┌米┐ ┌米┐ ┌米┐    ║
║  │  │ │  │ │  │ │  │ │  │ │  │ │  │ │  │ │  │ │  │    ║
║  └格┘ └格┘ └格┘ └格┘ └格┘ └格┘ └格┘ └格┘ └格┘ └格┘    ║
║   [hàng 2: hoàn toàn trống]                          ║
║                                                       ║
║  ┌米┐ ┌米┐ ┌米┐ ┌米┐ ┌米┐ ┌米┐ ┌米┐ ┌米┐ ┌米┐ ┌米┐    ║
║  │  │ │  │ │  │ │  │ │  │ │  │ │  │ │  │ │  │ │  │    ║
║  └格┘ └格┘ └格┘ └格┘ └格┘ └格┘ └格┘ └格┘ └格┘ └格┘    ║
║   [hàng 3: hoàn toàn trống]                          ║
╚═══════════════════════════════════════════════════════╝
```

---

## Tips & Best Practices

### ✅ Nên Làm

1. **Sắp xếp theo độ khó:** Nhập chữ đơn giản trước (vd: 一二三), chữ phức tạp sau
2. **Nhóm theo chủ đề:** Ví dụ: chữ về thời tiết (雨雪云风), chữ về gia đình (父母子女)
3. **Check preview:** Mở PDF ngay để kiểm tra trước khi in
4. **Lưu input:** Copy danh sách chữ ra file text để tái sử dụng

### ❌ Không Nên

1. **Đừng nhập quá nhiều một lúc:** >30 chữ sẽ mất nhiều thời gian (2-3 phút)
2. **Tránh ký tự đặc biệt:** Emoji, số La Mã, chữ Latin sẽ bị bỏ qua
3. **Đừng đóng app:** Trong khi đang xử lý, không đóng cửa sổ

---

## Troubleshooting Quick Reference

| Vấn Đề | Kiểm Tra | Giải Pháp |
|--------|----------|-----------|
| App không mở | Python version | Cần Python 3.10+ |
| Lỗi import | Thư viện | `pip install -r requirements.txt` |
| Chữ Hán hiện "X" | Font CJK | Cài Microsoft YaHei / Noto CJK |
| Không tải được dữ liệu | Internet | Kiểm tra kết nối mạng |
| PDF bị cắt ngang | Bug | Báo lỗi (không nên xảy ra) |
| Tiến trình đơ | Quá nhiều chữ | Chia nhỏ danh sách (<20 chữ/lần) |

---

## Output File Organization

### Đề Xuất Cấu Trúc Thư Mục

```
my_hanzi_practice/
├── beginner/
│   ├── basic_strokes.pdf      (一二三四五)
│   ├── numbers.pdf             (十百千万亿)
│   └── family.pdf              (父母子女)
├── intermediate/
│   ├── verbs.pdf               (学习工作)
│   └── adjectives.pdf          (好美大小)
└── advanced/
    ├── complex_chars.pdf       (赢躁繁)
    └── idioms.pdf              (成语相关字)
```

---

**Chúc bạn luyện viết vui vẻ! 🎉**
