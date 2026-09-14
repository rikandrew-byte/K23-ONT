# 📝 Ứng Dụng Tạo Tập Luyện Viết Chữ Hán

Ứng dụng desktop GUI để tạo file PDF luyện viết chữ Hán với bố cục chuyên nghiệp, hỗ trợ nhập hàng loạt và xuất thành tập luyện đa trang.

## ✨ Tính Năng

### 🎨 Giao Diện Đồ Họa (GUI)
- Giao diện tkinter đơn giản, thân thiện
- Ô nhập liệu lớn hỗ trợ nhập/dán nhiều chữ cùng lúc
- Chọn đường dẫn file output tùy chỉnh
- Thanh tiến trình theo dõi real-time
- Hoàn toàn bằng tiếng Việt

### 📄 PDF Đa Trang
- Xuất file PDF duy nhất chứa tất cả ký tự
- Tự động phân trang thông minh (không cắt ngang block)
- Mỗi ký tự có một block hoàn chỉnh gồm:
  - **Header**: Chữ Hán lớn + Pinyin + Nghĩa tiếng Việt
  - **Bảng thứ tự nét**: Hiển thị từng bước xây dựng ký tự (hỗ trợ đa hàng cho chữ nhiều nét)
  - **30 ô luyện tập**: 3 hàng × 10 ô 米字格 (MiZiGe), 3 ô đầu có chữ mẫu mờ để đồ theo

### 🔤 Xử Lý Font CJK Hoàn Hảo
- Tự động phát hiện và sử dụng font hỗ trợ chữ Hán (Microsoft YaHei, SimSun, Noto Sans CJK...)
- **Không còn ô "X" thiếu glyph** trong PDF
- Hỗ trợ cả Windows, macOS, và Linux

### 🚀 Xử Lý Hàng Loạt
- Nhập nhiều chữ cùng lúc (vd: "学 龙 赢 水")
- Tự động loại bỏ trùng lặp
- Hỗ trợ ký tự phức tạp (17+ nét như "赢")
- Tải dữ liệu song song với feedback tiến trình

## 📦 Cài Đặt

### Yêu Cầu
- Python 3.10+
- Thư viện:
  ```bash
  pip install reportlab requests pillow
  ```

### Cấu Trúc File
```
hanzi_workbook_gui.py       # Ứng dụng GUI chính
generate_sheet.py           # Script CLI (tạo PNG đơn lẻ - phiên bản cũ)
test_pdf_generation.py      # Script test PDF
test_complex_chars.py       # Test với ký tự phức tạp
README_GUI.md               # File này
```

## 🎯 Cách Sử Dụng

### Chạy Ứng Dụng GUI

```bash
python hanzi_workbook_gui.py
```

### Các Bước Trong Giao Diện

1. **Nhập chữ Hán**: Gõ hoặc dán các chữ Hán vào ô lớn (cách nhau bằng khoảng trắng hoặc xuống dòng)
   - Ví dụ: `你 好 学 中 水 龙 爱 赢`

2. **Chọn file đầu ra**: 
   - Tên file mặc định: `tap_luyen_chu_han.pdf`
   - Click "Chọn thư mục..." để đổi đường dẫn

3. **Bắt đầu xuất**: Click nút **"🚀 BẮT ĐẦU XUẤT FILE PDF"**

4. **Theo dõi tiến trình**: 
   - Thanh tiến trình hiển thị % hoàn thành
   - Nhãn trạng thái cho biết đang xử lý chữ nào

5. **Hoàn thành**: Hộp thoại xác nhận xuất hiện, có thể mở file PDF ngay

### Ví Dụ Test Nhanh (CLI)

```bash
# Test với 3 chữ đơn giản
python test_pdf_generation.py

# Test với chữ phức tạp (17 nét)
python test_complex_chars.py
```

## 🛠️ Kiến Trúc Kỹ Thuật

### Core Components

1. **Font CJK Detection** (`find_cjk_font()`)
   - Quét hệ thống tìm font TrueType/OpenType hỗ trợ chữ Hán
   - Test render thực tế để verify glyph coverage
   - Đăng ký vào ReportLab PDF engine

2. **Data Fetching** (`fetch_character_data()`)
   - Tải dữ liệu nét từ hanzi-writer-data CDN (MIT license)
   - Fallback giữa version 2.0 và @latest
   - Timeout 10s, retry logic

3. **SVG Path Rendering** (`parse_svg_path_to_pil()`)
   - Parse SVG path commands (M, L, C, Q, Z)
   - Render thành PIL Image với alpha channel
   - Scale từ 1024×1024 HW space → arbitrary size

4. **Character Stroke Rendering** (`render_character_strokes()`)
   - Composite nhiều nét thành ảnh hoàn chỉnh
   - Hỗ trợ highlight nét cuối (đỏ) cho bảng thứ tự
   - Điều chỉnh opacity cho chữ mẫu mờ

5. **PDF Block Drawing** (`draw_character_block()`)
   - Vẽ header với PIL-rendered CJK text
   - Bảng thứ tự nét: đa hàng tự động (16 ô/hàng)
   - Grid 米字格: 3×10 ô, viền liền + cross/diagonal đứt nét

6. **Multi-Page PDF Generation** (`generate_workbook_pdf()`)
   - Layout engine tính toán chiều cao còn lại
   - Auto page-break khi hết chỗ
   - Footer với credit CC BY 4.0

7. **GUI Application** (`HanziWorkbookApp`)
   - tkinter UI với thread worker
   - Progress callback từ worker → main thread
   - Error handling + user feedback

## 📐 Thông Số Bố Cục

| Thông Số | Giá Trị | Ghi Chú |
|----------|---------|---------|
| Kích thước trang | A4 (595×842 pt) | Chuẩn quốc tế |
| Margin | 40 pt | Trái/Phải/Trên/Dưới |
| Header block | 50 pt | Chữ Hán + metadata |
| Stroke order | 80 pt | Tự động đa hàng |
| Practice grid | 200 pt | 3 hàng × 10 ô |
| Block spacing | 15 pt | Khoảng cách giữa các chữ |
| Max strokes/row | 16 | Thứ tự nét |

## 🎨 Color Scheme

| Element | Hex | RGB | Mục đích |
|---------|-----|-----|----------|
| Stroke (done) | #1a1a2e | (0.10, 0.10, 0.18) | Nét hoàn thành |
| Stroke (current) | #e63946 | (0.90, 0.22, 0.27) | Nét đang vẽ (highlight) |
| Grid outer | #444444 | (0.27, 0.27, 0.27) | Viền ô |
| Grid dash | #bbbbbb | (0.73, 0.73, 0.73) | Đường phụ trong ô |

## 🐛 Xử Lý Lỗi

### Font Không Tìm Thấy
**Hiện tượng**: Warning popup khi khởi động  
**Giải pháp**: 
- Windows: Cài Microsoft YaHei hoặc SimSun (thường có sẵn)
- macOS: PingFang (built-in)
- Linux: `sudo apt install fonts-noto-cjk`

### Ký Tự Không Tìm Thấy
**Hiện tượng**: Popup cảnh báo với tên ký tự  
**Nguyên nhân**: 
- Ký tự hiếm không có trong hanzi-writer-data
- Input không phải chữ Hán (số, chữ Latin, emoji...)
**Xử lý**: Ký tự đó bị bỏ qua, các ký tự khác vẫn tiếp tục

### Lỗi Kết Nối
**Hiện tượng**: "Không có kết nối internet"  
**Giải pháp**: Kiểm tra kết nối mạng và thử lại

## 📊 Performance

| Số ký tự | Thời gian (ước tính) | Kích thước PDF |
|----------|----------------------|----------------|
| 3 chữ | ~3-5 giây | 13 KB |
| 6 chữ | ~8-12 giây | 23 KB |
| 10 chữ | ~15-20 giây | 35-40 KB |
| 20 chữ | ~30-40 giây | 70-80 KB |

*Thời gian phụ thuộc vào tốc độ mạng (tải dữ liệu CDN) và CPU (render SVG)*

## 📝 Giấy Phép & Credit

- **Ứng dụng**: Mã nguồn mở
- **Dữ liệu nét**: [hanzi-writer-data](https://github.com/chanind/hanzi-writer-data) (CC BY 4.0)
- **Nguồn gốc nét**: [Make Me A Hanzi](https://github.com/skishore/makemeahanzi) project

## 🔮 Tính Năng Tương Lai

- [ ] Nhập metadata (Pinyin, nghĩa) từ file CSV/Excel
- [ ] Tùy chỉnh số hàng/cột ô luyện
- [ ] Chế độ "chỉ thứ tự nét" (không có ô luyện)
- [ ] Export SVG thay vì PDF
- [ ] Dictionary lookup tự động (Pinyin + nghĩa)
- [ ] Theme color customization

## 💬 Hỗ Trợ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra file README này
2. Chạy test scripts để verify setup
3. Đảm bảo đã cài đủ thư viện: `pip install -r requirements.txt` (nếu có)

---

**Phiên bản**: 1.0  
**Ngày cập nhật**: 26/06/2026
