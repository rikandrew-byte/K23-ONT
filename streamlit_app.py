import streamlit as st
import io
import re
import traceback
from hanzi_workbook_gui import (
    LayoutConfig, fetch_character_data, fetch_dictionary_data_bulk, 
    generate_workbook_pdf
)

# Cấu hình trang cơ bản
st.set_page_config(
    page_title="EHOU K23 - Tạo Tập Luyện Chữ Hán", 
    page_icon="🏮", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS để làm đẹp giao diện và ẩn các nút của Streamlit
st.markdown("""
<style>
    /* Ẩn Hamburger menu và Footer mặc định của Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Ẩn nút Manage App (chỉ admin mới thấy nhưng ẩn đi cho đẹp) */
    .stDeployButton {display:none;}
    
    /* Chỉnh tiêu đề chính */
    .main-title {
        color: #c62828;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0px;
        padding-top: 20px;
        font-size: 2.2rem;
    }
    
    /* Chỉnh subtitle */
    .sub-title {
        text-align: center;
        color: #666;
        font-size: 1rem;
        margin-top: 5px;
        margin-bottom: 25px;
    }
    
    /* Nút bấm full width trên mobile */
    .stButton>button {
        width: 100%;
        height: 55px;
        font-weight: bold;
        font-size: 18px;
        border-radius: 8px;
    }
    
    .stDownloadButton>button {
        width: 100%;
        height: 55px;
        font-weight: bold;
        font-size: 18px;
        background-color: #2e7d32;
        color: white;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Giao diện chính (Main area)
st.markdown("<h1 class='main-title'>🏮 TẠO TẬP LUYỆN VIẾT CHỮ HÁN</h1>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Hệ thống tự động tra cứu thứ tự nét, Pinyin và Nghĩa Hán Việt</div>", unsafe_allow_html=True)

# Khung nhập liệu
text_input = st.text_area(
    "📝 Dán danh sách chữ Hán của bạn vào đây:", 
    height=150, 
    value="你好学中水龙爱",
    placeholder="Ví dụ: 统一, 一连, 个人..."
)

# Cấu hình ngay bên dưới (phù hợp mobile)
with st.expander("⚙️ Tùy chỉnh cài đặt", expanded=True):
    rows = st.number_input("📏 Số dòng mỗi chữ (Mỗi dòng 10 ô):", min_value=1, max_value=6, value=3)
    
    st.markdown("**Bộ lọc thông minh:**")
    dedup = st.checkbox("🧹 Lọc bỏ chữ trùng lặp", value=True)
    skip_basic = st.checkbox("⚡ Bỏ qua chữ cơ bản (< 4 nét)", value=False)

st.markdown("<br>", unsafe_allow_html=True)

# Nút Action full width
btn_generate = st.button("🚀 TIẾN HÀNH TẠO PDF", type="primary", use_container_width=True)

if btn_generate:
    if not text_input.strip():
        st.warning("⚠️ Vui lòng nhập ít nhất một chữ Hán!")
    else:
        # Tạo hiệu ứng status loading
        with st.status("⏳ Đang xử lý dữ liệu...", expanded=True) as status:
            try:
                st.write("1️⃣ Phân tích cụm từ...")
                separators = re.compile(r'[,，;；\n]+')
                raw_groups = separators.split(text_input)
                groups = [re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', raw) for raw in raw_groups if raw]
                
                all_chars_flat = []
                seen = set()
                for g in groups:
                    for c in g:
                        if c not in seen:
                            seen.add(c)
                            all_chars_flat.append(c)
                
                total = len(all_chars_flat)
                st.write(f"2️⃣ Đang tải nét vẽ cho {total} chữ...")
                stroke_cache = {ch: (fetch_character_data(ch) or {}).get("strokes", []) for ch in all_chars_flat}
                
                st.write("3️⃣ Đang tra cứu từ điển...")
                dict_cache = fetch_dictionary_data_bulk(all_chars_flat)
                
                st.write("4️⃣ Áp dụng bộ lọc...")
                pdf_groups = []
                practiced_chars = set()
                for group in groups:
                    group_text = "".join(group)
                    char_list = []
                    for ch in group:
                        strokes_data = stroke_cache.get(ch, [])
                        if not strokes_data: continue
                        
                        if dedup and ch in practiced_chars: continue
                        if skip_basic and len(strokes_data) < 4:
                            practiced_chars.add(ch)
                            continue
                            
                        practiced_chars.add(ch)
                        ch_info = dict_cache.get(ch, {"pinyin": "", "nghia": ""})
                        char_list.append((ch, ch_info.get("pinyin", ""), ch_info.get("nghia", ""), strokes_data))
                            
                    if char_list:
                        pdf_groups.append((group_text, char_list))
                
                st.write("5️⃣ Đang vẽ file PDF...")
                out_path = "temp_output.pdf"
                generate_workbook_pdf(pdf_groups, out_path, LayoutConfig(rows))
                
                status.update(label="✅ Đã xử lý xong!", state="complete", expanded=False)
                
                with open(out_path, "rb") as f:
                    pdf_bytes = f.read()
                    
                st.markdown("<br>", unsafe_allow_html=True)
                st.download_button(
                    label="📥 TẢI FILE PDF VỀ MÁY",
                    data=pdf_bytes,
                    file_name="Tap_Luyen_Chu_Han_K23.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
                st.balloons()
                
            except Exception as e:
                status.update(label="❌ Có lỗi xảy ra!", state="error")
                st.error(f"Lỗi: {e}")
                st.code(traceback.format_exc())

# Footer chuyên nghiệp ở cuối trang
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #999; font-size: 13px;'>
    Dự án nội bộ dành cho <b>EHOU - ONT K23</b><br>
    Phát triển bởi Andrew Tseng<br><br>
    <img src="https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fk23-ont-tuvung.streamlit.app&count_bg=%23c62828&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=L%C6%B0%E1%BB%A3t+truy+c%E1%BA%ADp&edge_flat=true" alt="Lượt truy cập">
</div>
""", unsafe_allow_html=True)
