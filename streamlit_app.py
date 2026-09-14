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
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS để làm đẹp giao diện
st.markdown("""
<style>
    /* Chỉnh màu nền và viền của sidebar */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e0e0e0;
    }
    
    /* Chỉnh tiêu đề chính */
    .main-title {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #d32f2f;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0px;
        font-size: 2.5rem;
    }
    
    /* Chỉnh subtitle */
    .sub-title {
        text-align: center;
        color: #555;
        font-size: 1.1rem;
        font-weight: 500;
        margin-top: 5px;
        margin-bottom: 30px;
        font-style: italic;
    }
    
    /* Căn giữa nút bấm chính */
    .stButton>button {
        width: 100%;
        height: 50px;
        font-weight: bold;
        font-size: 18px;
        border-radius: 8px;
        transition: 0.3s;
    }
    
    .stDownloadButton>button {
        width: 100%;
        height: 55px;
        font-weight: bold;
        font-size: 18px;
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
    }
    
    .stDownloadButton>button:hover {
        background-color: #45a049;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Giao diện Cột trái (Sidebar)
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/Open_University_Vietnam.svg/1024px-Open_University_Vietnam.svg.png", width=100)
    st.markdown("### ⚙️ Cài đặt cấu hình")
    st.markdown("---")
    
    rows = st.number_input("📏 Số dòng mỗi chữ:", min_value=1, max_value=6, value=3, help="Mỗi dòng gồm 10 ô vuông 米字格.")
    
    st.markdown("---")
    st.markdown("### 🧠 Bộ lọc thông minh")
    dedup = st.checkbox("🧹 Lọc bỏ chữ trùng lặp", value=True, help="Các chữ Hán đã xuất hiện trước đó sẽ không bị lặp lại.")
    skip_basic = st.checkbox("⚡ Bỏ qua chữ cơ bản", value=False, help="Tự động bỏ qua các chữ có dưới 4 nét (一, 二, 人...).")
    
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #888; font-size: 12px;'>Phát triển cho<br><b>EHOU - ONT K23</b><br>© Andrew Tseng</div>", unsafe_allow_html=True)

# Giao diện Cột phải (Main area)
st.markdown("<h1 class='main-title'>🏮 TẠO TẬP LUYỆN VIẾT CHỮ HÁN</h1>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Hệ thống tự động tra cứu thứ tự nét, Pinyin và Nghĩa Hán Việt</div>", unsafe_allow_html=True)

# Bọc input text trong một container đẹp hơn
with st.container(border=True):
    text_input = st.text_area(
        "📝 Dán danh sách chữ Hán của bạn vào đây:", 
        height=200, 
        value="你好学中水龙爱",
        placeholder="Ví dụ: 统一, 一连, 个人..."
    )

st.markdown("<br>", unsafe_allow_html=True)

# Nút Action nằm giữa
col_spacer1, col_action, col_spacer2 = st.columns([1, 2, 1])
with col_action:
    btn_generate = st.button("🚀 TIẾN HÀNH TẠO PDF", type="primary")

if btn_generate:
    if not text_input.strip():
        st.warning("⚠️ Vui lòng nhập ít nhất một chữ Hán!")
    else:
        st.markdown("---")
        
        # Tạo hiệu ứng status loading chuyên nghiệp
        with st.status("⏳ Hệ thống đang xử lý dữ liệu...", expanded=True) as status:
            try:
                # 1. Parsing
                st.write("1️⃣ Phân tích cụm từ...")
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
                st.write(f"2️⃣ Đang tải dữ liệu nét vẽ cho {total} chữ độc lập...")
                
                stroke_cache = {}
                for ch in all_chars_flat:
                    d = fetch_character_data(ch)
                    stroke_cache[ch] = d["strokes"] if d else []
                
                st.write("3️⃣ Đang tra cứu Pinyin và Nghĩa qua từ điển...")
                dict_cache = fetch_dictionary_data_bulk(all_chars_flat)
                
                # 3. Filter logic
                st.write("4️⃣ Áp dụng bộ lọc thông minh...")
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
                st.write("5️⃣ Đang vẽ và kết xuất file PDF...")
                cfg = LayoutConfig(rows)
                
                out_path = "temp_output.pdf"
                generate_workbook_pdf(pdf_groups, out_path, cfg)
                
                # Hoàn thành
                status.update(label="✅ Đã xử lý xong toàn bộ!", state="complete", expanded=False)
                
                with open(out_path, "rb") as f:
                    pdf_bytes = f.read()
                    
                st.markdown("<br>", unsafe_allow_html=True)
                col_btn_sp1, col_btn, col_btn_sp2 = st.columns([1, 2, 1])
                with col_btn:
                    st.download_button(
                        label="📥 NHẤN VÀO ĐÂY ĐỂ TẢI FILE PDF",
                        data=pdf_bytes,
                        file_name="Tap_Luyen_Chu_Han_K23.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
                    st.balloons() # Thả bóng bay ăn mừng
                
            except Exception as e:
                status.update(label="❌ Có lỗi xảy ra!", state="error")
                st.error(f"Lỗi: {e}")
                st.code(traceback.format_exc())
