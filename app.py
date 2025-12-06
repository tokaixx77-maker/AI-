import streamlit as st
import pandas as pd
import io
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
# 【重要】引入我们自己写的工具箱 utils.py
import utils as U

# ==========================================
# 🎨 UI 配置与极致美化 (V7.4 Chinese Design Edition)
# ==========================================
st.set_page_config(
    page_title="77智能体测系统",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

def render_ui_header():
    """渲染极简风格的顶部区域，包含核心 CSS 样式"""
    st.markdown("""
    <style>
    /* 引入现代无衬线字体 Inter */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap');
    
    /* 全局字体与背景设置 */
    html, body, [class*="css"] {
        font-family: 'Inter', '微软雅黑', sans-serif;
        background-color: #fbfbfd; /* 高级感的极浅灰色背景 */
    }

    /* --- 核心容器：毛玻璃卡片风格 --- */
    .stTabs [data-baseweb="tab-panel"] {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(20px); /* 毛玻璃模糊效果 */
        -webkit-backdrop-filter: blur(20px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 4px 24px -1px rgba(0, 0, 0, 0.05);
        padding: 24px;
        margin-top: 10px;
    }
    /* 上传文件区域的卡片化 */
    [data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(20px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 4px 24px -1px rgba(0, 0, 0, 0.05);
        overflow: hidden;
    }

    /* --- 主 LOGO：极简科技感 --- */
    .main-logo-container {
        text-align: left; margin-bottom: 20px;
    }
    .main-logo-text {
        font-family: 'Inter', sans-serif; font-size: 48px; font-weight: 900; letter-spacing: -1px;
        background: linear-gradient(135deg, #1d1d1f 0%, #424245 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;
    }
    .sub-title {
        font-size: 14px; color: #86868b; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;
    }

    /* --- 侧边栏美化 --- */
    [data-testid="stSidebar"] {
        background-color: #f5f5f7; border-right: 1px solid rgba(0,0,0,0.05);
    }
    .secure-key-badge {
        background: rgba(52, 199, 89, 0.1); color: #009900; padding: 8px 12px; border-radius: 8px;
        font-size: 13px; font-weight: 600; display: flex; align-items: center; border: 1px solid rgba(52, 199, 89, 0.2);
    }

    /* --- 按钮：特斯拉风格的实体感 --- */
    div.stButton > button[kind="primary"] {
        background: #0071e3; /* 电光蓝 */
        border: none; border-radius: 12px; padding: 12px 24px; font-weight: 600; letter-spacing: 0.5px;
        box-shadow: 0 4px 12px rgba(0, 113, 227, 0.3);
        transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
    }
    div.stButton > button[kind="primary"]:hover {
        background: #0077ED; transform: scale(1.02); box-shadow: 0 6px 16px rgba(0, 113, 227, 0.4);
    }
    div.stButton > button[kind="secondary"] {
         border-radius: 12px; border: 1px solid #d2d2d7; color: #1d1d1f; font-weight: 600;
    }

    /* --- 核心亮点：纯CSS圆环进度条 (类似 Apple Watch) --- */
    .progress-ring-container { position: relative; width: 160px; height: 160px; margin: 0 auto; }
    .progress-ring-bg, .progress-ring-circle { fill: none; stroke-width: 12; transform: rotate(-90deg); transform-origin: 50% 50%; }
    .progress-ring-bg { stroke: #e6e6e7; opacity: 0.5; }
    .progress-ring-circle { stroke: #0071e3; stroke-linecap: round; transition: stroke-dashoffset 1s cubic-bezier(0.25, 0.8, 0.25, 1); }
    .progress-ring-text { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; }
    .progress-ring-value { font-size: 36px; font-weight: 900; color: #1d1d1f; letter-spacing: -1px; line-height: 1; }
    .progress-ring-label { font-size: 13px; color: #86868b; font-weight: 600; margin-top: 4px; }

    /* --- 指标卡片优化 --- */
    .metric-container { text-align: center; padding: 20px; }
    .metric-label { font-size: 14px; color: #86868b; font-weight: 600; }
    .metric-value-big { font-size: 42px; font-weight: 900; color: #1d1d1f; letter-spacing: -1.5px;}
    .metric-delta-pos { color: #34c759; font-size: 14px; font-weight: 600; background: rgba(52, 199, 89, 0.1); padding: 4px 8px; border-radius: 6px;}

    /* 隐藏 Streamlit 默认的页脚和菜单 */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    </style>

    <div class="main-logo-container">
        <h1 class='main-logo-text'>77 SYSTEM</h1>
        <p class='sub-title'>全学段体育数据智能中枢 // Professional Edition</p>
    </div>
    """, unsafe_allow_html=True)

    # 如果当前目录下有宣传海报图片，就显示出来
    if os.path.exists("77_poster.png"):
        st.image("77_poster.png", use_container_width=True)

# ==========================================
# 🔐 安全与状态初始化
# ==========================================
try: BACKEND_API_KEY = st.secrets["DASHSCOPE_API_KEY"]
except Exception: BACKEND_API_KEY = None

if 'init' not in st.session_state:
    st.session_state.update({
        'init': True, 'm_file_bytes': None, 'm_name': '', 'm_df': None, 'ocr_df': None,
        'target_rate_coarse': 90.0, 'school_level_index': 0
    })

# ==========================================
# 🎮 主程序界面逻辑
# ==========================================
render_ui_header()

# --- 侧边栏 ---
with st.sidebar:
    st.markdown("### 🎛️ 控制面板")
    EFFECTIVE_KEY = ""
    if BACKEND_API_KEY:
        st.markdown('<div class="secure-key-badge">✅ 云端专属 Key 已加载 (安全)</div>', unsafe_allow_html=True)
        EFFECTIVE_KEY = BACKEND_API_KEY
    else:
        user_key = st.text_input("请输入阿里云 API Key", type="password", help="因未配置云端 Secrets，本地运行需手动输入。")
        if user_key: EFFECTIVE_KEY = user_key
    
    st.markdown("---")
    # 学段选择
    school_level = st.selectbox(
        "🎯 请选择目标学段",
        ("初中", "高中", "大学", "小学(低年级)", "小学(中年级)", "小学(高年级)"),
        index=st.session_state['school_level_index'],
        key='school_level_select'
    )
    st.session_state['school_level_index'] = ["初中", "高中", "大学", "小学(低年级)", "小学(中年级)", "小学(高年级)"].index(school_level)

# --- 主界面内容 ---
# 1. 上传区域
with st.expander("📂 第一步：模版总表上传 (Excel)", expanded=True):
    mf = st.file_uploader("上传Excel总表", type=['xlsx'], label_visibility="collapsed")
    if mf and mf.name != st.session_state['m_name']:
        df = pd.read_excel(mf)
        st.session_state.update({'m_df': df, 'm_file_bytes': mf.getvalue(), 'm_name': mf.name})
        st.toast(f"✅ 模板 [{mf.name}] 加载成功！", icon="💿")

# 只有数据加载后才显示后续内容
if st.session_state['m_df'] is not None:
    st.write("") # Add some space
    # 创建 Tabs
    t1, t2 = st.tabs(["📸 AI 识图 & 合并", "🚀 数据处理 (清洗+调整)"])

    # === Tab 1: AI 识图 (中文界面 + 吸睛按钮) ===
    with t1:
        st.caption("💡 小贴士：在选择文件窗口中，按住 `Ctrl` 或 `Shift` 键可以一次性选择多张图片进行批量上传。")
        c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
        with c1: imgs = st.file_uploader("上传手写成绩单图片", type=['jpg','png','jpeg'], accept_multiple_files=True, label_visibility="collapsed")
        # 【关键修改】恢复了带有 Emoji 的吸睛按钮标题
        with c2: start_ocr = st.button("✨ 批量 AI 识图", type="primary", use_container_width=True)

        if start_ocr and imgs:
            if not EFFECTIVE_KEY:
                st.error("❌ 无法运行：未检测到有效的 API Key。请检查配置。")
            else:
                data_list, errs = [], []
                prog_bar, status_text = st.progress(0), st.empty()
                
                with st.spinner("🚀 AI 引擎全速运转中，正在并行处理多张图片..."):
                    with ThreadPoolExecutor(max_workers=5) as pool:
                        futures = {pool.submit(U.call_qwen_vl_ocr, img, EFFECTIVE_KEY): img for img in imgs}
                        for i, f in enumerate(as_completed(futures)):
                            img_file = futures[f]
                            prog_bar.progress((i + 1) / len(imgs))
                            status_text.text(f"🤖 正在分析第 {i+1}/{len(imgs)} 张图片: {img_file.name}...")
                            try:
                                res = f.result()
                                if "Error" in res: errs.append(f"{img_file.name}: {res}")
                                else: data_list.append(pd.DataFrame(json.loads(res)))
                            except Exception as e: errs.append(f"{img_file.name}: 处理异常 {str(e)}")
                
                prog_bar.empty(); status_text.empty()
                
                if data_list:
                    st.session_state['ocr_df'] = pd.concat(data_list, ignore_index=True)
                    st.success(f"✅ 处理完成！成功识别 **{len(imgs) - len(errs)}** 张图片，共提取出 **{len(st.session_state['ocr_df'])}** 条学生数据。")
                if errs:
                    with st.expander(f"⚠️ 有 {len(errs)} 张图片识别失败，点击查看详情"): st.write(errs)

        if st.session_state['ocr_df'] is not None:
            st.markdown("---")
            st.markdown("##### 📝 识别结果预览与编辑")
            ed_ocr = st.data_editor(st.session_state['ocr_df'], num_rows="dynamic", use_container_width=True)
            
            if st.button("📥 确认无误，合并置入总表", type="primary", use_container_width=True):
                new_master, _, changes_df = U.merge_ocr_to_master(st.session_state['m_df'], ed_ocr)
                st.session_state['m_df'] = new_master
                
                # 数据校验
               # 数据校验 (优化文案)
                anomalies = U.validate_data_ranges(new_master)
                if not anomalies.empty:
                    # 改用 info 或 expander，降低警报级别
                    with st.expander("💡 数据核对提醒 (点击展开)", expanded=True):
                        st.info("系统检测到以下数据数值较大或较小，建议您简单扫视确认一下（如数据无误请直接忽略）：")
                        st.dataframe(anomalies, use_container_width=True)

                if not changes_df.empty:
                    st.markdown("##### 📋 数据合并详情报告")
                    st.dataframe(changes_df, use_container_width=True)
                    st.success(f"🎉 成功！已将 **{len(changes_df)}** 个新的数据点更新到总表中。")
                else:
                    st.warning("🤔 未检测到有效的数据更新。请检查识别结果中的姓名是否与总表一致。")

    # === Tab 2: 数据处理 (中文界面 + 圆环UI) ===
    with t2:
        current_rate = U.calculate_good_rate(st.session_state['m_df'], school_level)
        
        # 使用 3列布局，中间放核心圆环
        c_left, c_mid, c_right = st.columns([1.2, 2, 1.2])

        with c_left: st.write("") # 占位

        # --- 核心区域：特斯拉风格圆环进度条 ---
        with c_mid:
            # 计算圆环的 stroke-dasharray 来实现进度效果
            circumference = 440
            offset = circumference - (current_rate / 100 * circumference)
            
            # 渲染纯 HTML/CSS 圆环组件
            st.markdown(f"""
            <div class="progress-ring-container">
                <svg class="progress-ring" width="160" height="160">
                    <circle class="progress-ring-bg" cx="80" cy="80" r="70"></circle>
                    <circle class="progress-ring-circle" cx="80" cy="80" r="70"
                            style="stroke-dasharray: {circumference}; stroke-dashoffset: {offset};">
                    </circle>
                </svg>
                <div class="progress-ring-text">
                    <div class="progress-ring-value">{current_rate:.1f}%</div>
                    <div class="progress-ring-label">当前优良率</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("") # Spacing
            # 目标设定区域
            st.markdown("##### 🎯 设定目标优良率")
            sld, inp = st.columns([3, 1])
            rs = sld.slider("粗调", 0.0, 100.0, key='target_rate_coarse', step=1.0, label_visibility="collapsed")
            tr = inp.number_input("精调", 0.0, 100.0, float(rs), 0.1, label_visibility="collapsed")
            
            # 核心按钮
            run_btn = st.button("⚡ 执行智能清洗与调整算法", type="primary", use_container_width=True)

        with c_right: st.write("") # 占位

        # --- 执行结果显示区域 ---
        if run_btn:
            if not U.STANDARDS_DB: st.error("❌ 严重错误：找不到评分标准文件 `standards.json`。")
            else:
                # 1. 执行清洗
                df_c, _ = U.smart_clean(st.session_state['m_df'], school_level)
                # 2. 执行智能调整 (V7.2 优先微调算法)，并接收日志
                df_f, boost_logs = U.auto_boost(df_c, tr, school_level)
                
                st.session_state['m_df'] = df_f
                achieved_rate = U.calculate_good_rate(df_f, school_level)
                
                st.write("")
                st.markdown("---")
                # 使用美化后的指标显示结果
                res_c1, res_c2, res_c3 = st.columns(3)
                with res_c2:
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-label">✨ 调整后实际优良率</div>
                        <div class="metric-value-big">{achieved_rate:.1f}%</div>
                        <div style="margin-top:8px;"><span class="metric-delta-pos">+{achieved_rate - current_rate:.1f}% 增长</span></div>
                    </div>
                    """, unsafe_allow_html=True)

                if not boost_logs.empty:
                    # 使用 expander 展示详细日志
                    with st.expander(f"📋 智能调整详情报告 (共微调 {len(boost_logs)} 项)", expanded=True):
                        st.dataframe(boost_logs, use_container_width=True, hide_index=True)

        # --- 下载区域 ---
        if st.session_state['m_df'] is not None and st.session_state['m_file_bytes']:
            st.write("")
            st.markdown("#### 📤 第三步：下载最终成果")
            c_dl, _ = st.columns([1, 2])
            ex_data, msg = U.save_data_keeping_format(io.BytesIO(st.session_state['m_file_bytes']), st.session_state['m_df'])
            if ex_data:
                c_dl.download_button("📥 下载最终报表 (XLSX)", ex_data, f"77智能体测_{school_level}_最终.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary", use_container_width=True)
            else: st.error(msg)