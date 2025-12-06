import streamlit as st
import pandas as pd
import io
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import utils as U

# ==========================================
# 🎨 UI 配置 (V11.2 Chinese Title Edition)
# ==========================================
st.set_page_config(
    page_title="77 SYSTEM",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

def render_ui_header():
    """渲染自适应系统主题的 UI"""
    st.markdown("""
    <style>
    /* 引入 Inter 字体 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, -apple-system, "Microsoft YaHei", sans-serif;
    }

    /* --- 卡片容器 --- */
    .stTabs [data-baseweb="tab-panel"], [data-testid="stExpander"] {
        background-color: var(--secondary-background-color);
        border-radius: 16px;
        padding: 24px;
        border: 1px solid rgba(128, 128, 128, 0.1);
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    
    [data-testid="stExpander"] {
        border: none;
        padding: 10px;
    }

    /* --- 标题与 Logo --- */
    .main-logo-text {
        font-family: 'Inter', sans-serif;
        font-size: 52px;
        font-weight: 900;
        letter-spacing: -1px;
        color: var(--text-color);
        margin: 0;
        line-height: 1.2;
    }
    .brand-blue { color: #0071e3; }
    
    /* 副标题样式优化：中文适配 */
    .sub-title {
        font-size: 16px; /* 稍微调大一点 */
        opacity: 0.8;
        font-weight: 500;
        margin-top: 8px;
        letter-spacing: 1px;
        font-family: "Microsoft YaHei", sans-serif; /* 确保中文显示优雅 */
    }

    /* --- 按钮 --- */
    div.stButton > button[kind="primary"] {
        background-color: #0071e3; color: white !important;
        border: none; border-radius: 99px; padding: 12px 28px;
        font-weight: 600; transition: all 0.2s ease;
        box-shadow: 0 4px 10px rgba(0, 113, 227, 0.3);
    }
    div.stButton > button[kind="primary"]:hover {
        transform: scale(1.02); box-shadow: 0 6px 15px rgba(0, 113, 227, 0.4);
    }
    div.stButton > button[kind="secondary"] {
        background-color: transparent; border: 1px solid var(--text-color);
        color: var(--text-color); border-radius: 99px; opacity: 0.6;
    }
    div.stButton > button[kind="secondary"]:hover {
        opacity: 1.0; border-color: #0071e3; color: #0071e3;
    }

    /* --- 圆环进度条样式优化 --- */
    .progress-ring-circle {
        stroke: #0071e3; transition: stroke-dashoffset 1s ease;
    }
    .progress-ring-bg {
        stroke: var(--text-color); opacity: 0.1;
    }
    /* 强制文字颜色继承系统变量，确保可见 */
    .progress-text-container {
        color: var(--text-color);
    }

    /* --- 指标卡片 --- */
    .metric-card-adaptive {
        background-color: var(--secondary-background-color);
        border-radius: 16px; padding: 20px; text-align: center;
        border: 1px solid rgba(128, 128, 128, 0.1);
    }
    .metric-val { font-size: 40px; font-weight: 800; color: var(--text-color); }
    .metric-lbl { font-size: 13px; font-weight: 600; opacity: 0.6; text-transform: uppercase;}

    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    </style>

    <div style="margin-bottom: 30px;">
        <h1 class='main-logo-text'>77 <span class='brand-blue'>SYSTEM</span></h1>
        <p class='sub-title'>全学段体测数据智能中枢 // v11.2 Professional</p>
    </div>
    """, unsafe_allow_html=True)

    if os.path.exists("77_poster.png"):
        st.markdown('<div style="border-radius: 12px; overflow: hidden; margin-bottom: 20px;">', unsafe_allow_html=True)
        st.image("77_poster.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

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
    st.markdown("### 🎛️ 控制台")
    EFFECTIVE_KEY = ""
    if BACKEND_API_KEY:
        st.success("✅ 云端 Key 已激活")
        EFFECTIVE_KEY = BACKEND_API_KEY
    else:
        user_key = st.text_input("API Key", type="password", help="在此输入您的阿里云 Key")
        if user_key: EFFECTIVE_KEY = user_key
    
    st.markdown("---")
    school_level = st.selectbox(
        "🎓 学段选择",
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

    # === Tab 1: AI 识图 ===
    with t1:
        st.caption("💡 提示：支持批量上传多张图片。")
        c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
        with c1: imgs = st.file_uploader("上传成绩单", type=['jpg','png','jpeg'], accept_multiple_files=True)
        with c2: start_ocr = st.button("✨ 开始识别", type="primary", use_container_width=True)

        if start_ocr:
            if not imgs: st.warning("⚠️ 请先上传图片")
            elif not EFFECTIVE_KEY: st.error("❌ 请输入 API Key")
            else:
                data_list, errs = [], []
                prog_bar, status_text = st.progress(0), st.empty()
                with st.spinner("🚀 正在分析图像..."):
                    with ThreadPoolExecutor(max_workers=5) as pool:
                        futures = {pool.submit(U.call_qwen_vl_ocr, img, EFFECTIVE_KEY): img for img in imgs}
                        for i, f in enumerate(as_completed(futures)):
                            img_file = futures[f]
                            prog_bar.progress((i + 1) / len(imgs))
                            status_text.text(f"处理中: {img_file.name}...")
                            try:
                                res = f.result()
                                if res.startswith("Error"): errs.append(f"{img_file.name}: {res}")
                                else: data_list.append(pd.DataFrame(json.loads(res)))
                            except Exception as e:
                                if "Expecting value" in str(e): errs.append(f"{img_file.name}: 无法识别有效表格")
                                else: errs.append(f"{img_file.name}: {str(e)}")
                prog_bar.empty(); status_text.empty()
                if data_list:
                    st.session_state['ocr_df'] = pd.concat(data_list, ignore_index=True)
                    st.success(f"✅ 成功提取 **{len(st.session_state['ocr_df'])}** 条数据")
                if errs:
                    with st.expander(f"⚠️ {len(errs)} 张图片失败"): st.write(errs)

        if st.session_state['ocr_df'] is not None:
            st.markdown("---")
            st.caption("请核对下方识别结果：")
            ed_ocr = st.data_editor(st.session_state['ocr_df'], num_rows="dynamic", use_container_width=True)
            if st.button("📥 确认合并到总表", type="primary", use_container_width=True):
                new_master, _, changes_df = U.merge_ocr_to_master(st.session_state['m_df'], ed_ocr)
                st.session_state['m_df'] = new_master
                
                anomalies = U.validate_data_ranges(new_master)
                if not anomalies.empty:
                    with st.expander("💡 数据核对提醒 (点击展开)", expanded=True):
                        st.info("系统检测到部分数值较大或较小，建议扫视确认（如无误请忽略）：")
                        st.dataframe(anomalies, use_container_width=True)
                
                if not changes_df.empty:
                    st.success(f"🎉 已成功更新 {len(changes_df)} 条数据！")
                    with st.expander("查看详细变更记录"):
                        st.dataframe(changes_df, use_container_width=True)
                else: st.warning("未检测到有效更新")

    # === Tab 2: 数据处理 ===
    with t2:
        current_rate = U.calculate_good_rate(st.session_state['m_df'], school_level)
        c_left, c_mid, c_right = st.columns([1, 2, 1])

        with c_mid:
            # 动态计算圆环
            circumference = 565
            offset = circumference - (current_rate / 100 * circumference)
            
            # 圆环 SVG
            st.markdown(f"""
            <div class="progress-ring-container" style="position: relative; width: 180px; height: 180px; margin: 0 auto;">
                <svg class="progress-ring" width="180" height="180">
                    <circle class="progress-ring-bg" cx="90" cy="90" r="80" stroke-width="10" fill="none"></circle>
                    <circle class="progress-ring-circle" cx="90" cy="90" r="80" stroke-width="10" fill="none"
                            style="stroke-dasharray: {circumference}; stroke-dashoffset: {offset}; transform: rotate(-90deg); transform-origin: 50% 50%;">
                    </circle>
                </svg>
                <div class="progress-text-container" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; z-index: 10;">
                    <div style="font-size: 48px; font-weight: 800; line-height: 1; letter-spacing: -1px;">{current_rate:.1f}%</div>
                    <div style="font-size: 13px; font-weight: 600; opacity: 0.6; margin-top: 5px;">当前优良率</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            st.markdown("##### 🎯 设定目标优良率")
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
                    <div class="metric-card-adaptive">
                        <div class="metric-lbl">✨ 调整后实际优良率</div>
                        <div class="metric-val">{achieved_rate:.1f}%</div>
                        <div style="margin-top:8px; color:#28a745; font-weight:bold;">+{achieved_rate - current_rate:.1f}% 提升</div>
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