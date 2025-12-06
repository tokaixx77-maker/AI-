import streamlit as st
import pandas as pd
import io
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import utils as U

# ==========================================
# 🎨 UI 配置 (V10.5 Force Light & Fixes)
# ==========================================
st.set_page_config(
    page_title="77 SYSTEM",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

def render_ui_header():
    """渲染强制亮色风格 UI"""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* --- 1. 强制覆盖 Streamlit 默认暗黑模式 --- */
    [data-testid="stAppViewContainer"], .stApp {
        background-color: #F5F5F7 !important; /* 强制背景灰白 */
        color: #1D1D1F !important; /* 强制文字深灰 */
    }
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E5E5E5 !important;
    }
    [data-testid="stHeader"] {
        background-color: rgba(255,255,255,0) !important; /* 顶部条透明 */
    }
    
    /* --- 2. 修复输入框在暗黑模式下的显示 --- */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stNumberInput input {
        background-color: #FFFFFF !important;
        color: #1D1D1F !important;
        border: 1px solid #D2D2D7 !important;
    }
    /* 修复文件上传框 */
    [data-testid="stFileUploader"] {
        background-color: #FFFFFF !important;
        border-radius: 12px;
        padding: 10px;
    }

    /* --- 3. 核心容器美化 --- */
    .stTabs [data-baseweb="tab-panel"] {
        background-color: #FFFFFF !important;
        border-radius: 18px;
        padding: 32px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.04);
        border: 1px solid rgba(0,0,0,0.02);
    }
    
    [data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border-radius: 12px;
        border: none;
        box-shadow: 0 2px 12px rgba(0,0,0,0.03);
        color: #1D1D1F !important;
    }
    
    /* --- 4. 标题与 Logo --- */
    .main-logo-text {
        font-family: 'Inter', sans-serif;
        font-size: 56px;
        font-weight: 800;
        letter-spacing: -1.5px;
        color: #1D1D1F !important;
        margin: 0;
        line-height: 1.1;
    }
    .main-logo-text span { color: #0071e3; }
    .sub-title {
        font-size: 16px; color: #86868b !important; font-weight: 500; margin-top: 8px;
    }
    
    /* --- 5. 按钮样式 --- */
    div.stButton > button[kind="primary"] {
        background-color: #0071e3 !important;
        color: white !important;
        border-radius: 980px;
        padding: 12px 28px;
        font-size: 15px; font-weight: 600; border: none;
        box-shadow: 0 4px 6px rgba(0, 113, 227, 0.2);
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #0077ED !important;
        transform: scale(1.02);
    }
    div.stButton > button[kind="secondary"] {
        background-color: #F5F5F7 !important;
        color: #1D1D1F !important;
        border-radius: 980px;
        border: 1px solid #D2D2D7;
    }

    /* --- 6. 圆环与图表 --- */
    .progress-ring-container { position: relative; width: 180px; height: 180px; margin: 0 auto; }
    .progress-ring-bg { fill: none; stroke: #E5E5E5; stroke-width: 10; }
    .progress-ring-circle { 
        fill: none; stroke-width: 10; stroke: #0071e3; stroke-linecap: round; 
        transform: rotate(-90deg); transform-origin: 50% 50%; 
        transition: stroke-dashoffset 1s ease; 
    }
    .progress-ring-value { 
        font-size: 48px; font-weight: 700; color: #1D1D1F; letter-spacing: -1px; 
    }
    .progress-ring-label { 
        font-size: 14px; color: #86868b; font-weight: 500; margin-top: 5px; 
    }
    .metric-card-apple {
        background: #FFFFFF !important;
        border-radius: 16px; padding: 24px; text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.03); border: 1px solid rgba(0,0,0,0.02);
    }
    .metric-value { font-size: 42px; font-weight: 700; color: #1D1D1F; }
    
    /* 隐藏多余元素 */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    </style>

    <div style="margin-bottom: 40px;">
        <h1 class='main-logo-text'>77 <span>SYSTEM</span></h1>
        <p class='sub-title'>全学段体育数据智能中枢 // Professional Edition</p>
    </div>
    """, unsafe_allow_html=True)

    if os.path.exists("77_poster.png"):
        st.image("77_poster.png", use_container_width=True)

# ==========================================
# 🔐 逻辑部分
# ==========================================
try: BACKEND_API_KEY = st.secrets["DASHSCOPE_API_KEY"]
except: BACKEND_API_KEY = None

if 'init' not in st.session_state:
    st.session_state.update({
        'init': True, 'm_file_bytes': None, 'm_name': '', 'm_df': None, 'ocr_df': None,
        'target_rate_coarse': 90.0, 'school_level_index': 0
    })

render_ui_header()

# --- 侧边栏 ---
with st.sidebar:
    st.markdown("### 🎛️ 控制中心")
    EFFECTIVE_KEY = ""
    if BACKEND_API_KEY:
        st.success("✅ 云端 Key 已激活")
        EFFECTIVE_KEY = BACKEND_API_KEY
    else:
        user_key = st.text_input("输入阿里云 API Key", type="password")
        if user_key: EFFECTIVE_KEY = user_key
    
    st.markdown("---")
    school_level = st.selectbox(
        "🎓 选择学段",
        ("初中", "高中", "大学", "小学(低年级)", "小学(中年级)", "小学(高年级)"),
        index=st.session_state['school_level_index'],
        key='school_level_select'
    )
    st.session_state['school_level_index'] = ["初中", "高中", "大学", "小学(低年级)", "小学(中年级)", "小学(高年级)"].index(school_level)

# --- 主界面 ---
st.write("")
with st.expander("📂 第一步：上传模版总表 (Excel)", expanded=True):
    mf = st.file_uploader("点击上传文件", type=['xlsx'], label_visibility="collapsed")
    if mf and mf.name != st.session_state['m_name']:
        df = pd.read_excel(mf)
        st.session_state.update({'m_df': df, 'm_file_bytes': mf.getvalue(), 'm_name': mf.name})
        st.toast(f"✅ 已加载: {mf.name}")

if st.session_state['m_df'] is not None:
    st.write("")
    t1, t2 = st.tabs(["📸 AI 识图 & 合并", "🚀 数据智能处理"])

    # === Tab 1: AI 识图 (修复按钮无反应问题) ===
    with t1:
        st.caption("💡 提示：按住 `Ctrl` 或 `Shift` 可批量选择图片。")
        c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
        with c1: imgs = st.file_uploader("上传成绩单图片", type=['jpg','png','jpeg'], accept_multiple_files=True)
        with c2: start_ocr = st.button("✨ 开始 AI 识别", type="primary", use_container_width=True)

        # 【修复逻辑】把判断拆开写，方便调试和反馈
        if start_ocr:
            if not imgs:
                st.warning("⚠️ 请先上传图片，再点击识别。")
            elif not EFFECTIVE_KEY:
                st.error("❌ 无法运行：未检测到 API Key，请在侧边栏输入。")
            else:
                # 只有 Key 和 图片都有时，才执行
                data_list, errs = [], []
                prog_bar, status_text = st.progress(0), st.empty()
                
                try:
                    with st.spinner("🚀 AI 正在极速分析中..."):
                        with ThreadPoolExecutor(max_workers=5) as pool:
                            futures = {pool.submit(U.call_qwen_vl_ocr, img, EFFECTIVE_KEY): img for img in imgs}
                            for i, f in enumerate(as_completed(futures)):
                                img_file = futures[f]
                                prog_bar.progress((i + 1) / len(imgs))
                                status_text.text(f"正在处理: {img_file.name}...")
                                try:
                                    res = f.result()
                                    if res.startswith("Error"): errs.append(f"{img_file.name}: {res}")
                                    else: data_list.append(pd.DataFrame(json.loads(res)))
                                except Exception as e:
                                    if "Expecting value" in str(e):
                                        errs.append(f"{img_file.name}: 无法识别有效表格")
                                    else:
                                        errs.append(f"{img_file.name}: {str(e)}")
                    
                    prog_bar.empty(); status_text.empty()
                    
                    if data_list:
                        st.session_state['ocr_df'] = pd.concat(data_list, ignore_index=True)
                        st.success(f"✅ 识别成功！获取 **{len(st.session_state['ocr_df'])}** 条数据。")
                    
                    if errs:
                        with st.expander(f"⚠️ {len(errs)} 张图片识别失败"): st.write(errs)
                        
                except Exception as e:
                    st.error(f"❌ 运行出错: {str(e)}")

        if st.session_state['ocr_df'] is not None:
            st.markdown("---")
            st.markdown("##### 📝 结果核对")
            ed_ocr = st.data_editor(st.session_state['ocr_df'], num_rows="dynamic", use_container_width=True)
            
            if st.button("📥 合并到总表", type="primary", use_container_width=True):
                new_master, _, changes_df = U.merge_ocr_to_master(st.session_state['m_df'], ed_ocr)
                st.session_state['m_df'] = new_master
                
                # 【优化提示】使用温和的提示语
                anomalies = U.validate_data_ranges(new_master)
                if not anomalies.empty:
                    with st.expander("💡 数据核对提醒 (点击展开)", expanded=True):
                        st.info("系统检测到部分数值较大或较小，建议您简单扫视确认（如数据无误请忽略）：")
                        st.dataframe(anomalies, use_container_width=True)
                
                if not changes_df.empty:
                    st.markdown("##### 📋 合并报告")
                    st.dataframe(changes_df, use_container_width=True)
                    st.success(f"🎉 已更新 {len(changes_df)} 条数据！")
                else: st.warning("未检测到有效更新。")

    # === Tab 2: 数据处理 ===
    with t2:
        current_rate = U.calculate_good_rate(st.session_state['m_df'], school_level)
        c_left, c_mid, c_right = st.columns([1, 2, 1])

        with c_mid:
            # 极简白圆环
            circumference = 565
            offset = circumference - (current_rate / 100 * circumference)
            st.markdown(f"""
            <div class="progress-ring-container">
                <svg class="progress-ring" width="180" height="180">
                    <circle class="progress-ring-bg" cx="90" cy="90" r="80"></circle>
                    <circle class="progress-ring-circle" cx="90" cy="90" r="80"
                            style="stroke-dasharray: {circumference}; stroke-dashoffset: {offset};">
                    </circle>
                </svg>
                <div class="progress-ring-text">
                    <div class="progress-ring-value">{current_rate:.1f}%</div>
                    <div class="progress-ring-label">当前优良率</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            st.markdown("##### 🎯 设定目标")
            sld, inp = st.columns([3, 1])
            rs = sld.slider("粗调", 0.0, 100.0, key='target_rate_coarse', step=1.0, label_visibility="collapsed")
            tr = inp.number_input("精调", 0.0, 100.0, float(rs), 0.1, label_visibility="collapsed")
            
            run_btn = st.button("⚡ 执行智能调整", type="primary", use_container_width=True)

        if run_btn:
            if not U.STANDARDS_DB: st.error("❌ 标准库丢失")
            else:
                df_c, _ = U.smart_clean(st.session_state['m_df'], school_level)
                df_f, boost_logs = U.auto_boost(df_c, tr, school_level)
                st.session_state['m_df'] = df_f
                achieved_rate = U.calculate_good_rate(df_f, school_level)
                
                st.write("")
                st.markdown("---")
                rc1, rc2, rc3 = st.columns([1, 2, 1])
                with rc2:
                    st.markdown(f"""
                    <div class="metric-card-apple">
                        <div style="font-size:14px; color:#86868b; margin-bottom:5px;">✨ 调整后优良率</div>
                        <div class="metric-value">{achieved_rate:.1f}%</div>
                        <div style="margin-top:8px;"><span class="metric-delta">+{achieved_rate - current_rate:.1f}% 提升</span></div>
                    </div>
                    """, unsafe_allow_html=True)
                
                if not boost_logs.empty:
                    with st.expander(f"📋 查看调整明细 ({len(boost_logs)} 项)", expanded=True):
                        st.dataframe(boost_logs, use_container_width=True, hide_index=True)

        if st.session_state['m_df'] is not None and st.session_state['m_file_bytes']:
            st.write("")
            st.markdown("#### 📤 第三步：下载成果")
            c_dl, _ = st.columns([1, 2])
            ex_data, msg = U.save_data_keeping_format(io.BytesIO(st.session_state['m_file_bytes']), st.session_state['m_df'])
            if ex_data:
                c_dl.download_button("📥 下载 Excel", ex_data, f"77体测_{school_level}_最终.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary", use_container_width=True)
            else: st.error(msg)