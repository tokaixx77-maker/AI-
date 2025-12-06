import streamlit as st
import pandas as pd
import io
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import utils as U
# 【新增】引入绘图库 (解决痛点一)
import plotly.figure_factory as ff

# ==========================================
# 🎨 UI 配置 (V12.0 Ultimate Pro Toolkit)
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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, -apple-system, "Microsoft YaHei", sans-serif;
    }

    .stTabs [data-baseweb="tab-panel"], [data-testid="stExpander"] {
        background-color: var(--secondary-background-color);
        border-radius: 16px; padding: 24px;
        border: 1px solid rgba(128, 128, 128, 0.1);
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    [data-testid="stExpander"] { border: none; padding: 10px; }

    .main-logo-text {
        font-family: 'Inter', sans-serif; font-size: 52px; font-weight: 900; letter-spacing: -1px;
        color: var(--text-color); margin: 0; line-height: 1.2;
    }
    .brand-blue { color: #0071e3; }
    .sub-title {
        font-size: 16px; opacity: 0.8; font-weight: 500; margin-top: 8px; letter-spacing: 1px;
        font-family: "Microsoft YaHei", sans-serif;
    }

    div.stButton > button[kind="primary"] {
        background-color: #0071e3; color: white !important;
        border: none; border-radius: 99px; padding: 12px 28px; font-weight: 600; transition: all 0.2s ease;
        box-shadow: 0 4px 10px rgba(0, 113, 227, 0.3);
    }
    div.stButton > button[kind="primary"]:hover {
        transform: scale(1.02); box-shadow: 0 6px 15px rgba(0, 113, 227, 0.4);
    }
    div.stButton > button[kind="secondary"] {
        background-color: transparent; border: 1px solid var(--text-color);
        color: var(--text-color); border-radius: 99px; opacity: 0.6;
    }
    div.stButton > button[kind="secondary"]:hover { opacity: 1.0; border-color: #0071e3; color: #0071e3; }

    .progress-ring-circle { stroke: #0071e3; transition: stroke-dashoffset 1s ease; }
    .progress-ring-bg { stroke: var(--text-color); opacity: 0.1; }
    .progress-text-container { color: var(--text-color); }

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
        <p class='sub-title'>全学段体测数据智能中枢 // v12.0 Pro Toolkit</p>
    </div>
    """, unsafe_allow_html=True)

    if os.path.exists("77_poster.png"):
        st.markdown('<div style="border-radius: 12px; overflow: hidden; margin-bottom: 20px;">', unsafe_allow_html=True)
        st.image("77_poster.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 📈 绘图函数 (解决痛点一)
# ==========================================
def render_distribution_chart(df_old, df_new):
    """绘制调整前后的成绩分布对比图"""
    # 提取所有数值型体育项目列
    score_cols = [col for col in df_new.columns if any(k in col for k in U.SCORE_COLUMNS_MAP.keys())]
    if not score_cols: return None
    
    selected_col = st.selectbox("📊 选择要查看分布变化的项目：", score_cols)
    
    clean_old = pd.to_numeric(df_old[selected_col], errors='coerce').dropna()
    clean_new = pd.to_numeric(df_new[selected_col], errors='coerce').dropna()
    
    if len(clean_old) > 0 and len(clean_new) > 0:
        hist_data = [clean_old, clean_new]
        group_labels = ['调整前 (原始)', '调整后 (优化)']
        colors = ['#A0A0A0', '#0047FF'] # 灰色 vs 克莱因蓝
        
        # 创建分布图 (需要 scipy 库支持)
        try:
            fig = ff.create_distplot(hist_data, group_labels, show_hist=False, show_rug=False, colors=colors)
            fig.update_layout(
                title_text=f"{selected_col} - 数据分布趋势对比",
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font={'family': "Inter"},
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=20, r=20, t=60, b=20), height=350,
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=False)
            )
            return fig
        except Exception as e:
            st.warning(f"无法绘制图表，可能数据量过少或缺少依赖库 (scipy)。错误: {e}")
            return None
    return None

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

st.write("")
with st.expander("📂 第一步：上传模版总表 (Excel)", expanded=True):
    mf = st.file_uploader("点击上传文件", type=['xlsx'], label_visibility="collapsed")
    if mf and mf.name != st.session_state['m_name']:
        df = pd.read_excel(mf)
        st.session_state.update({'m_df': df, 'm_file_bytes': mf.getvalue(), 'm_name': mf.name})
        st.toast(f"✅ 已加载: {mf.name}")
        
        # 【新增】解决痛点二：智能表头识别报告
        identified_cols = []
        unidentified_cols = []
        for col in df.columns:
            is_identified = False
            for std_name, aliases in U.SCORE_COLUMNS_MAP.items():
                if col == std_name or col in aliases:
                    identified_cols.append(f"`{col}` (识别为: {std_name})")
                    is_identified = True
                    break
            if not is_identified and col not in ['姓名', '性别', '班级', '学号']:
                unidentified_cols.append(f"`{col}`")
        
        with st.expander("🔎 智能表头识别报告 (点击查看)", expanded=False):
            if identified_cols:
                 st.success(f"✅ 成功识别以下体育项目列：\n\n" + ", ".join(identified_cols))
            if unidentified_cols:
                 st.info(f"ℹ️ 以下列未被识别为标准体育项目（将被忽略或仅作参考）：\n\n" + ", ".join(unidentified_cols) + "\n\n💡 提示：如果需要识别，请修改 Excel 表头为标准名称（如“50米”）。")

if st.session_state['m_df'] is not None:
    st.write("")
    t1, t2 = st.tabs(["📸 AI 识图 & 合并", "🚀 数据智能处理"])

    # === Tab 1: AI 识图 (解决痛点三) ===
    with t1:
        st.caption("💡 提示：支持批量上传多张图片。")
        c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
        # 【新增】保存上传的图片对象，用于后续展示
        with c1: imgs = st.file_uploader("上传成绩单", type=['jpg','png','jpeg'], accept_multiple_files=True)
        with c2: start_ocr = st.button("✨ 开始识别", type="primary", use_container_width=True)

        if imgs:
            # 【新增】图片库展示
            with st.expander("🖼️ 已上传图片库 (点击展开查看原图)", expanded=False):
                cols = st.columns(len(imgs))
                for i, img_file in enumerate(imgs):
                    with cols[i]:
                        st.image(img_file, caption=img_file.name, use_container_width=True)

        if start_ocr:
            if not imgs: st.warning("⚠️ 请先上传图片")
            elif not EFFECTIVE_KEY: st.error("❌ 请输入 API Key")
            else:
                data_list, errs = [], []
                prog_bar, status_text = st.progress(0), st.empty()
                with st.spinner("🚀 正在分析图像..."):
                    with ThreadPoolExecutor(max_workers=5) as pool:
                        # 【修改】传递 filename 给工具函数
                        futures = {pool.submit(U.call_qwen_vl_ocr, img, EFFECTIVE_KEY, img.name): img for img in imgs}
                        for i, f in enumerate(as_completed(futures)):
                            img_file = futures[f]
                            prog_bar.progress((i + 1) / len(imgs))
                            status_text.text(f"处理中: {img_file.name}...")
                            try:
                                res = f.result()
                                if isinstance(res, str) and res.startswith("Error"): errs.append(f"{img_file.name}: {res}")
                                else: data_list.append(pd.DataFrame(res))
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
            # 【新增】提示用户最右侧有来源图片列
            st.caption("请核对下方识别结果 (最右侧列可查看数据来源图片)：")
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
                    with st.expander("查看详细变更记录 (含来源图片)"):
                        st.dataframe(changes_df, use_container_width=True)
                else: st.warning("未检测到有效更新")

    # === Tab 2: 数据处理 ===
    with t2:
        current_rate = U.calculate_good_rate(st.session_state['m_df'], school_level)
        c_left, c_mid, c_right = st.columns([1, 2, 1])

        with c_mid:
            circumference = 565
            offset = circumference - (current_rate / 100 * circumference)
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
                # 【新增】保存旧数据快照用于对比
                df_old_snapshot = st.session_state['m_df'].copy()
                
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
                
                st.write("")
                # 【新增】解决痛点一：数据分布可视化
                with st.expander("📊 数据分布可视化分析 (点击查看专业图表)", expanded=True):
                    chart_fig = render_distribution_chart(df_old_snapshot, df_f)
                    if chart_fig:
                        st.plotly_chart(chart_fig, use_container_width=True)
                    else:
                        st.info("暂无足够数据生成对比图表，请确保表格中包含体育项目数据。")

                if not boost_logs.empty:
                    with st.expander(f"📋 查看调整明细 ({len(boost_logs)} 项)", expanded=False):
                        st.dataframe(boost_logs, use_container_width=True, hide_index=True)

        if st.session_state['m_df'] is not None and st.session_state['m_file_bytes']:
            st.write("")
            st.markdown("#### 📤 第三步：下载成果")
            c_dl, _ = st.columns([1, 2])
            ex_data, msg = U.save_data_keeping_format(io.BytesIO(st.session_state['m_file_bytes']), st.session_state['m_df'])
            if ex_data:
                c_dl.download_button("📥 下载 Excel", ex_data, f"77体测_{school_level}_最终.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary", use_container_width=True)
            else: st.error(msg)