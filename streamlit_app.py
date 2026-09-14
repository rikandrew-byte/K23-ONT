import streamlit as st
import io
import re
import traceback
from hanzi_workbook_gui import (
    LayoutConfig, fetch_character_data, fetch_dictionary_data_bulk, 
    generate_workbook_pdf
)
import hanzi_workbook_gui as hw

st.set_page_config(page_title="Tạo Tập Luyện Viết Chữ Hán", page_icon="📝", layout="centered")

st.title("📝 TẠO TẬP LUYỆN VIẾT CHỮ HÁN")
st.markdown("**EHOU - ONT K23** | Created by Andrew Tseng")

st.write("Dán danh sách chữ Hán vào ô bên dưới (cách nhau bằng dấu cách, phẩy hoặc xuống dòng):")
text_input = st.text_area("Nhập chữ Hán:", height=150, value="你好学中水龙爱")

col1, col2 = st.columns(2)
with col1:
    rows = st.number_input("Số dòng luyện tập cho mỗi chữ:", min_value=1, max_value=6, value=3)
with col2:
    st.write("Cài đặt thông minh:")
    dedup = st.checkbox("Lọc bỏ các chữ trùng lặp", value=True)
    skip_basic = st.checkbox("Bỏ qua các chữ quá cơ bản (< 4 nét)", value=False)

if st.button("🚀 BẮT ĐẦU TẠO PDF", type="primary"):
    if not text_input.strip():
        st.warning("Vui lòng nhập ít nhất một chữ Hán!")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 1. Parsing
            separators = re.compile(r'[,，;；\n]+')
            raw_groups = separators.split(text_input)
            groups = []
            for raw in raw_groups:
                chars = re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', raw)
                if chars:
                    groups.append(chars)
            
            # 2. Fetch data
            all_chars_flat = []
            seen = set()
            for g in groups:
                for c in g:
                    if c not in seen:
                        seen.add(c)
                        all_chars_flat.append(c)
            
            total = len(all_chars_flat)
            status_text.text(f"Đang tải dữ liệu nét vẽ cho {total} chữ...")
            
            stroke_cache = {}
            for i, ch in enumerate(all_chars_flat):
                d = fetch_character_data(ch)
                stroke_cache[ch] = d["strokes"] if d else []
                progress_bar.progress(int((i+1) / total * 30))  # 30% progress for fetching
            
            status_text.text("Đang tra cứu từ điển...")
            dict_cache = fetch_dictionary_data_bulk(all_chars_flat)
            progress_bar.progress(40)
            
            # 3. Filter logic
            pdf_groups = []
            practiced_chars = set()
            for group in groups:
                group_text = "".join(group)
                char_list = []
                for ch in group:
                    if ch in stroke_cache and stroke_cache[ch]:
                        strokes_data = stroke_cache[ch]
                        
                        if dedup and ch in practiced_chars:
                            continue
                        if skip_basic and len(strokes_data) < 4:
                            practiced_chars.add(ch)
                            continue
                        
                        practiced_chars.add(ch)
                        ch_info = dict_cache.get(ch, {"pinyin": "", "nghia": ""})
                        py = ch_info.get("pinyin", "")
                        ng = ch_info.get("nghia", "")
                        char_list.append((ch, py, ng, strokes_data))
                        
                if char_list:
                    pdf_groups.append((group_text, char_list))
            
            # 4. Generate PDF
            status_text.text("Đang tiến hành vẽ trang PDF... Quá trình này có thể mất vài chục giây.")
            cfg = LayoutConfig(rows)
            
            # Use a callback to update progress
            total_filtered = sum(len(c) for _, c in pdf_groups)
            def pdf_progress(done, total_chars, msg):
                if total_chars > 0:
                    pct = 40 + int(done / total_chars * 60)
                    progress_bar.progress(min(pct, 100))
                    status_text.text(msg)
            
            # Save to temp file
            out_path = "temp_output.pdf"
            generate_workbook_pdf(pdf_groups, out_path, cfg, pdf_progress)
            
            # 5. Provide download link
            with open(out_path, "rb") as f:
                pdf_bytes = f.read()
                
            st.success("Tạo PDF thành công! Nhấn nút bên dưới để tải về.")
            st.download_button(
                label="📥 TẢI XUỐNG FILE PDF",
                data=pdf_bytes,
                file_name="tap_luyen_chu_han.pdf",
                mime="application/pdf",
                type="primary"
            )
            
        except Exception as e:
            st.error(f"Đã xảy ra lỗi: {e}")
            st.code(traceback.format_exc())
