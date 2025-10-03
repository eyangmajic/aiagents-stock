import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
from datetime import datetime
import time
import base64
import os

from stock_data import StockDataFetcher
from ai_agents import StockAnalysisAgents
from pdf_generator import display_pdf_export_section
from database import db
from monitor_manager import display_monitor_manager, get_monitor_summary
from monitor_service import monitor_service
from notification_service import notification_service

# 页面配置
st.set_page_config(
    page_title="复合多AI智能体股票团队分析系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 模型选择器
def model_selector():
    """模型选择器"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("🤖 AI模型选择")
    
    model_options = {
        "deepseek-chat": "DeepSeek Chat (默认)",
        "deepseek-reasoner": "DeepSeek Reasoner (推理增强)"
    }
    
    selected_model = st.sidebar.selectbox(
        "选择AI模型",
        options=list(model_options.keys()),
        format_func=lambda x: model_options[x],
        help="DeepSeek Reasoner提供更强的推理能力，但响应时间可能更长"
    )
    
    return selected_model

# 自定义CSS样式 - 专业版
st.markdown("""
<style>
    /* 全局样式 */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    .stApp {
        background: transparent;
    }
    
    /* 主容器 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        margin-top: 1rem;
    }
    
    /* 顶部导航栏 */
    .top-nav {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }
    
    .nav-title {
        font-size: 2rem;
        font-weight: 800;
        color: white;
        text-align: center;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        letter-spacing: 1px;
    }
    
    .nav-subtitle {
        text-align: center;
        color: rgba(255, 255, 255, 0.9);
        font-size: 0.95rem;
        margin-top: 0.5rem;
        font-weight: 300;
    }
    
    /* 标签页样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        color: white;
        font-weight: 600;
        font-size: 1.1rem;
        padding: 0 2rem;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.2);
        transform: translateY(-2px);
    }
    
    .stTabs [aria-selected="true"] {
        background: white !important;
        color: #667eea !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* 侧边栏美化 */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        padding-top: 2rem;
    }
    
    .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3,
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: white !important;
    }
    
    .css-1d391kg .stMarkdown, [data-testid="stSidebar"] .stMarkdown {
        color: rgba(255, 255, 255, 0.95) !important;
    }
    
    /* 分析师卡片 */
    .agent-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border-left: 5px solid #667eea;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease;
    }
    
    .agent-card:hover {
        transform: translateX(5px);
    }
    
    /* 决策卡片 */
    .decision-card {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        padding: 2rem;
        border-radius: 15px;
        border: 3px solid #4caf50;
        margin: 1.5rem 0;
        box-shadow: 0 8px 30px rgba(76, 175, 80, 0.2);
    }
    
    /* 警告卡片 */
    .warning-card {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #ff9800;
        box-shadow: 0 4px 15px rgba(255, 152, 0, 0.2);
    }
    
    /* 指标卡片 */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        text-align: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border-top: 4px solid #667eea;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
    }
    
    /* 按钮美化 */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(102, 126, 234, 0.4);
    }
    
    /* 输入框美化 */
    .stTextInput>div>div>input {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        padding: 0.75rem;
        font-size: 1rem;
        transition: border-color 0.3s ease;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* 进度条美化 */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* 成功/错误/警告/信息消息框 */
    .stSuccess, .stError, .stWarning, .stInfo {
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    
    /* 图表容器 */
    .js-plotly-plot {
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }
    
    /* Expander美化 */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 10px;
        font-weight: 600;
    }
    
    /* 数据框美化 */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    
    /* 隐藏Streamlit默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 响应式设计 */
    @media (max-width: 768px) {
        .nav-title {
            font-size: 1.5rem;
        }
        .stTabs [data-baseweb="tab"] {
            font-size: 0.9rem;
            padding: 0 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

def main():
    # 顶部标题栏
    st.markdown("""
    <div class="top-nav">
        <h1 class="nav-title">📈 复合多AI智能体股票团队分析系统</h1>
        <p class="nav-subtitle">基于DeepSeek的专业量化投资分析平台 | Multi-Agent Stock Analysis System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 侧边栏
    with st.sidebar:
        # 快捷导航 - 移到顶部
        st.markdown("### 🔍 快捷导航")
        
        if st.button("📖 历史记录", use_container_width=True, key="nav_history"):
            st.session_state.show_history = True
            if 'show_monitor' in st.session_state:
                del st.session_state.show_monitor
        
        if st.button("📊 实时监测", use_container_width=True, key="nav_monitor"):
            st.session_state.show_monitor = True
            if 'show_history' in st.session_state:
                del st.session_state.show_history
        
        if st.button("🏠 返回首页", use_container_width=True, key="nav_home"):
            if 'show_history' in st.session_state:
                del st.session_state.show_history
            if 'show_monitor' in st.session_state:
                del st.session_state.show_monitor
        
        st.markdown("---")
        
        # 系统配置
        st.markdown("### ⚙️ 系统配置")
        
        # API密钥检查
        api_key_status = check_api_key()
        if api_key_status:
            st.success("✅ API已连接")
        else:
            st.error("❌ API未配置")
            st.caption("请在.env中配置API密钥")
            
        st.markdown("---")
        
        # 模型选择器
        selected_model = model_selector()
        st.session_state.selected_model = selected_model
        
        st.markdown("---")
        
        # 系统状态面板
        st.markdown("### 📊 系统状态")
        
        monitor_status = "🟢 运行中" if monitor_service.running else "🔴 已停止"
        st.markdown(f"**监测服务**: {monitor_status}")
        
        try:
            from monitor_db import monitor_db
            stocks = monitor_db.get_monitored_stocks()
            notifications = monitor_db.get_pending_notifications()
            record_count = db.get_record_count()
            
            st.markdown(f"**分析记录**: {record_count}条")
            st.markdown(f"**监测股票**: {len(stocks)}只")
            st.markdown(f"**待处理**: {len(notifications)}条")
        except:
            pass
        
        st.markdown("---")
        
        # 分析参数设置
        st.markdown("### 📊 分析参数")
        period = st.selectbox(
            "数据周期",
            ["1y", "6mo", "3mo", "1mo"],
            index=0,
            help="选择历史数据的时间范围"
        )
        
        st.markdown("---")
        
        # 帮助信息
        with st.expander("💡 使用帮助"):
            st.markdown("""
            **股票代码格式**
            - 🇨🇳 A股：6位数字（如600519）
            - 🇺🇸 美股：字母代码（如AAPL）
            
            **功能说明**
            - **智能分析**：AI团队深度分析
            - **实时监测**：价格监控与提醒
            - **历史记录**：查看分析历史
            
            **AI分析流程**
            1. 数据获取 → 2. 技术分析
            3. 基本面分析 → 4. 资金分析
            5. 风险评估 → 6. 情绪分析
            7. 团队讨论 → 8. 最终决策
            """)
    
    # 检查是否显示历史记录
    if 'show_history' in st.session_state and st.session_state.show_history:
        display_history_records()
        return
    
    # 检查是否显示监测面板
    if 'show_monitor' in st.session_state and st.session_state.show_monitor:
        display_monitor_manager()
        return
    
    # 主界面
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        stock_input = st.text_input(
            "🔍 请输入股票代码或名称", 
            placeholder="例如: AAPL, 000001, 600036",
            help="支持美股代码(如AAPL)和A股代码(如000001)"
        )
    
    with col2:
        analyze_button = st.button("🚀 开始分析", type="primary", use_container_width=True)
    
    with col3:
        if st.button("🔄 清除缓存", use_container_width=True):
            st.cache_data.clear()
            st.success("缓存已清除")
    
    if analyze_button and stock_input:
        if not api_key_status:
            st.error("❌ 请先配置 DeepSeek API Key")
            return
        
        # 清除之前的分析结果
        if 'analysis_completed' in st.session_state:
            del st.session_state.analysis_completed
        if 'stock_info' in st.session_state:
            del st.session_state.stock_info
        if 'agents_results' in st.session_state:
            del st.session_state.agents_results
        if 'discussion_result' in st.session_state:
            del st.session_state.discussion_result
        if 'final_decision' in st.session_state:
            del st.session_state.final_decision
            
        run_stock_analysis(stock_input, period)
    
    # 检查是否有已完成的分析结果
    if 'analysis_completed' in st.session_state and st.session_state.analysis_completed:
        # 重新显示分析结果
        stock_info = st.session_state.stock_info
        agents_results = st.session_state.agents_results
        discussion_result = st.session_state.discussion_result
        final_decision = st.session_state.final_decision
        
        # 重新获取股票数据用于显示图表
        stock_info_current, stock_data, indicators = get_stock_data(stock_info['symbol'], period)
        
        # 显示股票基本信息
        display_stock_info(stock_info, indicators)
        
        # 显示股票图表
        if stock_data is not None:
            display_stock_chart(stock_data, stock_info)
        
        # 显示各分析师报告
        display_agents_analysis(agents_results)
        
        # 显示团队讨论
        display_team_discussion(discussion_result)
        
        # 显示最终决策
        display_final_decision(final_decision, stock_info, agents_results, discussion_result)
    
    # 示例和说明
    elif not stock_input:
        show_example_interface()

def check_api_key():
    """检查API密钥是否配置"""
    try:
        import config
        return bool(config.DEEPSEEK_API_KEY and config.DEEPSEEK_API_KEY.strip())
    except:
        return False

@st.cache_data(ttl=300)  # 缓存5分钟
def get_stock_data(symbol, period):
    """获取股票数据（带缓存）"""
    fetcher = StockDataFetcher()
    stock_info = fetcher.get_stock_info(symbol)
    stock_data = fetcher.get_stock_data(symbol, period)
    
    if isinstance(stock_data, dict) and "error" in stock_data:
        return stock_info, None, None
    
    stock_data_with_indicators = fetcher.calculate_technical_indicators(stock_data)
    indicators = fetcher.get_latest_indicators(stock_data_with_indicators)
    
    return stock_info, stock_data_with_indicators, indicators

def run_stock_analysis(symbol, period):
    """运行股票分析"""
    
    # 进度条
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # 1. 获取股票数据
        status_text.text("📈 正在获取股票数据...")
        progress_bar.progress(10)
        
        stock_info, stock_data, indicators = get_stock_data(symbol, period)
        
        if "error" in stock_info:
            st.error(f"❌ {stock_info['error']}")
            return
        
        if stock_data is None:
            st.error("❌ 无法获取股票历史数据")
            return
        
        # 显示股票基本信息
        display_stock_info(stock_info, indicators)
        progress_bar.progress(20)
        
        # 显示股票图表
        display_stock_chart(stock_data, stock_info)
        progress_bar.progress(30)
        
        # 2. 获取财务数据
        status_text.text("📊 正在获取财务数据...")
        fetcher = StockDataFetcher()  # 创建fetcher实例
        financial_data = fetcher.get_financial_data(symbol)
        progress_bar.progress(35)
        
        # 3. 初始化AI分析系统
        status_text.text("🤖 正在初始化AI分析系统...")
        # 使用选择的模型
        selected_model = st.session_state.get('selected_model', 'deepseek-chat')
        agents = StockAnalysisAgents(model=selected_model)
        progress_bar.progress(45)
        
        # 4. 运行多智能体分析
        status_text.text("🔍 AI分析师团队正在分析...")
        agents_results = agents.run_multi_agent_analysis(stock_info, stock_data, indicators, financial_data)
        progress_bar.progress(70)
        
        # 显示各分析师报告
        display_agents_analysis(agents_results)
        
        # 5. 团队讨论
        status_text.text("🤝 分析团队正在讨论...")
        discussion_result = agents.conduct_team_discussion(agents_results, stock_info)
        progress_bar.progress(85)
        
        # 显示团队讨论
        display_team_discussion(discussion_result)
        
        # 6. 最终决策
        status_text.text("📋 正在制定最终投资决策...")
        final_decision = agents.make_final_decision(discussion_result, stock_info, indicators)
        progress_bar.progress(100)
        
        # 保存分析结果到session_state
        st.session_state.analysis_completed = True
        st.session_state.stock_info = stock_info
        st.session_state.agents_results = agents_results
        st.session_state.discussion_result = discussion_result
        st.session_state.final_decision = final_decision
        
        # 保存到数据库
        try:
            db.save_analysis(
                symbol=stock_info.get('symbol', ''),
                stock_name=stock_info.get('name', ''),
                period=period,
                stock_info=stock_info,
                agents_results=agents_results,
                discussion_result=discussion_result,
                final_decision=final_decision
            )
            st.success("✅ 分析记录已保存到数据库")
        except Exception as e:
            st.warning(f"⚠️ 保存到数据库时出现错误: {str(e)}")
        
        # 显示最终决策
        display_final_decision(final_decision, stock_info, agents_results, discussion_result)
        
        status_text.text("✅ 分析完成！")
        time.sleep(1)
        status_text.empty()
        progress_bar.empty()
        
    except Exception as e:
        st.error(f"❌ 分析过程中出现错误: {str(e)}")
        progress_bar.empty()
        status_text.empty()

def display_stock_info(stock_info, indicators):
    """显示股票基本信息"""
    st.subheader(f"📊 {stock_info.get('name', 'N/A')} ({stock_info.get('symbol', 'N/A')})")
    
    # 基本信息卡片
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        current_price = stock_info.get('current_price', 'N/A')
        st.metric("当前价格", f"{current_price}")
    
    with col2:
        change_percent = stock_info.get('change_percent', 'N/A')
        if isinstance(change_percent, (int, float)):
            st.metric("涨跌幅", f"{change_percent:.2f}%", f"{change_percent:.2f}%")
        else:
            st.metric("涨跌幅", f"{change_percent}")
    
    with col3:
        pe_ratio = stock_info.get('pe_ratio', 'N/A')
        st.metric("市盈率", f"{pe_ratio}")
    
    with col4:
        pb_ratio = stock_info.get('pb_ratio', 'N/A')
        st.metric("市净率", f"{pb_ratio}")
    
    with col5:
        market_cap = stock_info.get('market_cap', 'N/A')
        if isinstance(market_cap, (int, float)):
            market_cap_str = f"{market_cap/1e9:.2f}B" if market_cap > 1e9 else f"{market_cap/1e6:.2f}M"
            st.metric("市值", market_cap_str)
        else:
            st.metric("市值", f"{market_cap}")
    
    # 技术指标
    if indicators and not isinstance(indicators, dict) or "error" not in indicators:
        st.subheader("📈 关键技术指标")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            rsi = indicators.get('rsi', 'N/A')
            if isinstance(rsi, (int, float)):
                rsi_color = "normal"
                if rsi > 70:
                    rsi_color = "inverse"
                elif rsi < 30:
                    rsi_color = "off"
                st.metric("RSI", f"{rsi:.2f}")
            else:
                st.metric("RSI", f"{rsi}")
        
        with col2:
            ma20 = indicators.get('ma20', 'N/A')
            if isinstance(ma20, (int, float)):
                st.metric("MA20", f"{ma20:.2f}")
            else:
                st.metric("MA20", f"{ma20}")
        
        with col3:
            volume_ratio = indicators.get('volume_ratio', 'N/A')
            if isinstance(volume_ratio, (int, float)):
                st.metric("量比", f"{volume_ratio:.2f}")
            else:
                st.metric("量比", f"{volume_ratio}")
        
        with col4:
            macd = indicators.get('macd', 'N/A')
            if isinstance(macd, (int, float)):
                st.metric("MACD", f"{macd:.4f}")
            else:
                st.metric("MACD", f"{macd}")

def display_stock_chart(stock_data, stock_info):
    """显示股票图表"""
    st.subheader("📈 股价走势图")
    
    # 创建蜡烛图
    fig = go.Figure()
    
    # 添加蜡烛图
    fig.add_trace(go.Candlestick(
        x=stock_data.index,
        open=stock_data['Open'],
        high=stock_data['High'],
        low=stock_data['Low'],
        close=stock_data['Close'],
        name="K线"
    ))
    
    # 添加移动平均线
    if 'MA5' in stock_data.columns:
        fig.add_trace(go.Scatter(
            x=stock_data.index,
            y=stock_data['MA5'],
            name="MA5",
            line=dict(color='orange', width=1)
        ))
    
    if 'MA20' in stock_data.columns:
        fig.add_trace(go.Scatter(
            x=stock_data.index,
            y=stock_data['MA20'],
            name="MA20",
            line=dict(color='blue', width=1)
        ))
    
    if 'MA60' in stock_data.columns:
        fig.add_trace(go.Scatter(
            x=stock_data.index,
            y=stock_data['MA60'],
            name="MA60",
            line=dict(color='purple', width=1)
        ))
    
    # 布林带
    if 'BB_upper' in stock_data.columns and 'BB_lower' in stock_data.columns:
        fig.add_trace(go.Scatter(
            x=stock_data.index,
            y=stock_data['BB_upper'],
            name="布林上轨",
            line=dict(color='red', width=1, dash='dash')
        ))
        fig.add_trace(go.Scatter(
            x=stock_data.index,
            y=stock_data['BB_lower'],
            name="布林下轨",
            line=dict(color='green', width=1, dash='dash'),
            fill='tonexty',
            fillcolor='rgba(0,100,80,0.1)'
        ))
    
    fig.update_layout(
        title=f"{stock_info.get('name', 'N/A')} 股价走势",
        xaxis_title="日期",
        yaxis_title="价格",
        height=500,
        showlegend=True
    )
    
    # 生成唯一的key
    chart_key = f"main_stock_chart_{stock_info.get('symbol', 'unknown')}_{int(time.time())}"
    st.plotly_chart(fig, use_container_width=True, key=chart_key)
    
    # 成交量图
    if 'Volume' in stock_data.columns:
        fig_volume = go.Figure()
        fig_volume.add_trace(go.Bar(
            x=stock_data.index,
            y=stock_data['Volume'],
            name="成交量",
            marker_color='lightblue'
        ))
        
        fig_volume.update_layout(
            title="成交量",
            xaxis_title="日期",
            yaxis_title="成交量",
            height=200
        )
        
        # 生成唯一的key
        volume_key = f"volume_chart_{stock_info.get('symbol', 'unknown')}_{int(time.time())}"
        st.plotly_chart(fig_volume, use_container_width=True, key=volume_key)

def display_agents_analysis(agents_results):
    """显示各分析师报告"""
    st.subheader("🤖 AI分析师团队报告")
    
    # 创建标签页
    tab_names = []
    tab_contents = []
    
    for agent_key, agent_result in agents_results.items():
        agent_name = agent_result.get('agent_name', '未知分析师')
        tab_names.append(agent_name)
        tab_contents.append(agent_result)
    
    tabs = st.tabs(tab_names)
    
    for i, tab in enumerate(tabs):
        with tab:
            agent_result = tab_contents[i]
            
            # 分析师信息
            st.markdown(f"""
            <div class="agent-card">
                <h4>👨‍💼 {agent_result.get('agent_name', '未知')}</h4>
                <p><strong>职责：</strong>{agent_result.get('agent_role', '未知')}</p>
                <p><strong>关注领域：</strong>{', '.join(agent_result.get('focus_areas', []))}</p>
                <p><strong>分析时间：</strong>{agent_result.get('timestamp', '未知')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # 分析报告
            st.markdown("**📄 分析报告:**")
            st.write(agent_result.get('analysis', '暂无分析'))

def display_team_discussion(discussion_result):
    """显示团队讨论"""
    st.subheader("🤝 分析团队讨论")
    
    st.markdown("""
    <div class="agent-card">
        <h4>💭 团队综合讨论</h4>
        <p>各位分析师正在就该股票进行深入讨论，整合不同维度的分析观点...</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write(discussion_result)

def display_final_decision(final_decision, stock_info, agents_results=None, discussion_result=None):
    """显示最终投资决策"""
    st.subheader("📋 最终投资决策")
    
    if isinstance(final_decision, dict) and "decision_text" not in final_decision:
        # JSON格式的决策
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # 投资评级
            rating = final_decision.get('rating', '未知')
            rating_color = {"买入": "🟢", "持有": "🟡", "卖出": "🔴"}.get(rating, "⚪")
            
            st.markdown(f"""
            <div class="decision-card">
                <h3 style="text-align: center;">{rating_color} {rating}</h3>
                <h4 style="text-align: center;">投资评级</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # 关键指标
            confidence = final_decision.get('confidence_level', 'N/A')
            st.metric("信心度", f"{confidence}/10")
            
            target_price = final_decision.get('target_price', 'N/A')
            st.metric("目标价格", f"{target_price}")
            
            position_size = final_decision.get('position_size', 'N/A')
            st.metric("建议仓位", f"{position_size}")
        
        with col2:
            # 详细建议
            st.markdown("**🎯 操作建议:**")
            st.write(final_decision.get('operation_advice', '暂无建议'))
            
            st.markdown("**📍 关键位置:**")
            col2_1, col2_2 = st.columns(2)
            
            with col2_1:
                st.write(f"**进场区间:** {final_decision.get('entry_range', 'N/A')}")
                st.write(f"**止盈位:** {final_decision.get('take_profit', 'N/A')}")
            
            with col2_2:
                st.write(f"**止损位:** {final_decision.get('stop_loss', 'N/A')}")
                st.write(f"**持有周期:** {final_decision.get('holding_period', 'N/A')}")
        
        # 风险提示
        risk_warning = final_decision.get('risk_warning', '')
        if risk_warning:
            st.markdown(f"""
            <div class="warning-card">
                <h4>⚠️ 风险提示</h4>
                <p>{risk_warning}</p>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        # 文本格式的决策
        decision_text = final_decision.get('decision_text', str(final_decision))
        st.write(decision_text)
    
    # 添加PDF导出功能
    st.markdown("---")
    if agents_results and discussion_result:
        display_pdf_export_section(stock_info, agents_results, discussion_result, final_decision)
    else:
        st.warning("⚠️ PDF导出功能需要完整的分析数据")

def show_example_interface():
    """显示示例界面"""
    st.subheader("💡 使用说明")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🚀 如何使用
        1. **输入股票代码**：支持美股(如AAPL、MSFT)和A股(如000001、600036)
        2. **点击开始分析**：系统将启动AI分析师团队
        3. **查看分析报告**：5位专业分析师将从不同角度分析
        4. **获得投资建议**：获得最终的投资评级和操作建议
        
        ### 📊 分析维度
        - **技术面**：趋势、指标、支撑阻力
        - **基本面**：财务、估值、行业分析
        - **资金面**：资金流向、主力行为
        - **风险管理**：风险识别与控制
        - **市场情绪**：情绪指标、热点分析
        """)
    
    with col2:
        st.markdown("""
        ### 📈 示例股票代码
        
        **美股热门**
        - AAPL (苹果)
        - MSFT (微软)
        - GOOGL (谷歌)
        - TSLA (特斯拉)
        - NVDA (英伟达)
        
        **A股热门**
        - 000001 (平安银行)
        - 600036 (招商银行)
        - 000002 (万科A)
        - 600519 (贵州茅台)
        - 000858 (五粮液)
        """)
    
    st.info("💡 提示：首次运行需要配置DeepSeek API Key，请在.env中设置DEEPSEEK_API_KEY")

def display_history_records():
    """显示历史分析记录"""
    st.subheader("📚 历史分析记录")
    
    # 获取所有记录
    records = db.get_all_records()
    
    if not records:
        st.info("📭 暂无历史分析记录")
        return
    
    st.write(f"📊 共找到 {len(records)} 条分析记录")
    
    # 搜索和筛选
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("🔍 搜索股票代码或名称", placeholder="输入股票代码或名称进行搜索")
    with col2:
        st.write("")
        st.write("")
        if st.button("🔄 刷新列表"):
            st.rerun()
    
    # 筛选记录
    filtered_records = records
    if search_term:
        filtered_records = [
            record for record in records 
            if search_term.lower() in record['symbol'].lower() or 
               search_term.lower() in record['stock_name'].lower()
        ]
    
    if not filtered_records:
        st.warning("🔍 未找到匹配的记录")
        return
    
    # 显示记录列表
    for record in filtered_records:
        # 根据评级设置颜色和图标
        rating = record.get('rating', '未知')
        rating_color = {
            "买入": "🟢",
            "持有": "🟡", 
            "卖出": "🔴",
            "强烈买入": "🟢",
            "强烈卖出": "🔴"
        }.get(rating, "⚪")
        
        with st.expander(f"{rating_color} {record['stock_name']} ({record['symbol']}) - {record['analysis_date']}"):
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            
            with col1:
                st.write(f"**股票代码:** {record['symbol']}")
                st.write(f"**股票名称:** {record['stock_name']}")
            
            with col2:
                st.write(f"**分析时间:** {record['analysis_date']}")
                st.write(f"**数据周期:** {record['period']}")
                st.write(f"**投资评级:** **{rating}**")
            
            with col3:
                if st.button("👀 查看详情", key=f"view_{record['id']}"):
                    st.session_state.viewing_record_id = record['id']
            
            with col4:
                if st.button("🗑️ 删除", key=f"delete_{record['id']}"):
                    if db.delete_record(record['id']):
                        st.success("✅ 记录已删除")
                        st.rerun()
                    else:
                        st.error("❌ 删除失败")
    
    # 查看详细记录
    if 'viewing_record_id' in st.session_state:
        display_record_detail(st.session_state.viewing_record_id)

def display_record_detail(record_id):
    """显示单条记录的详细信息"""
    st.markdown("---")
    st.subheader("📋 详细分析记录")
    
    record = db.get_record_by_id(record_id)
    if not record:
        st.error("❌ 记录不存在")
        return
    
    # 基本信息
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("股票代码", record['symbol'])
    with col2:
        st.metric("股票名称", record['stock_name'])
    with col3:
        st.metric("分析时间", record['analysis_date'])
    
    # 股票基本信息
    st.subheader("📊 股票基本信息")
    stock_info = record['stock_info']
    if stock_info:
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            current_price = stock_info.get('current_price', 'N/A')
            st.metric("当前价格", f"{current_price}")
        
        with col2:
            change_percent = stock_info.get('change_percent', 'N/A')
            if isinstance(change_percent, (int, float)):
                st.metric("涨跌幅", f"{change_percent:.2f}%", f"{change_percent:.2f}%")
            else:
                st.metric("涨跌幅", f"{change_percent}")
        
        with col3:
            pe_ratio = stock_info.get('pe_ratio', 'N/A')
            st.metric("市盈率", f"{pe_ratio}")
        
        with col4:
            pb_ratio = stock_info.get('pb_ratio', 'N/A')
            st.metric("市净率", f"{pb_ratio}")
        
        with col5:
            market_cap = stock_info.get('market_cap', 'N/A')
            if isinstance(market_cap, (int, float)):
                market_cap_str = f"{market_cap/1e9:.2f}B" if market_cap > 1e9 else f"{market_cap/1e6:.2f}M"
                st.metric("市值", market_cap_str)
            else:
                st.metric("市值", f"{market_cap}")
    
    # 各分析师报告
    st.subheader("🤖 AI分析师团队报告")
    agents_results = record['agents_results']
    if agents_results:
        tab_names = []
        tab_contents = []
        
        for agent_key, agent_result in agents_results.items():
            agent_name = agent_result.get('agent_name', '未知分析师')
            tab_names.append(agent_name)
            tab_contents.append(agent_result)
        
        tabs = st.tabs(tab_names)
        
        for i, tab in enumerate(tabs):
            with tab:
                agent_result = tab_contents[i]
                
                st.markdown(f"""
                <div class="agent-card">
                    <h4>👨‍💼 {agent_result.get('agent_name', '未知')}</h4>
                    <p><strong>职责：</strong>{agent_result.get('agent_role', '未知')}</p>
                    <p><strong>关注领域：</strong>{', '.join(agent_result.get('focus_areas', []))}</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("**📄 分析报告:**")
                st.write(agent_result.get('analysis', '暂无分析'))
    
    # 团队讨论
    st.subheader("🤝 分析团队讨论")
    discussion_result = record['discussion_result']
    if discussion_result:
        st.markdown("""
        <div class="agent-card">
            <h4>💭 团队综合讨论</h4>
        </div>
        """, unsafe_allow_html=True)
        st.write(discussion_result)
    
    # 最终决策
    st.subheader("📋 最终投资决策")
    final_decision = record['final_decision']
    if final_decision:
        if isinstance(final_decision, dict) and "decision_text" not in final_decision:
            col1, col2 = st.columns([1, 2])
            
            with col1:
                rating = final_decision.get('rating', '未知')
                rating_color = {"买入": "🟢", "持有": "🟡", "卖出": "🔴"}.get(rating, "⚪")
                
                st.markdown(f"""
                <div class="decision-card">
                    <h3 style="text-align: center;">{rating_color} {rating}</h3>
                    <h4 style="text-align: center;">投资评级</h4>
                </div>
                """, unsafe_allow_html=True)
                
                confidence = final_decision.get('confidence_level', 'N/A')
                st.metric("信心度", f"{confidence}/10")
                
                target_price = final_decision.get('target_price', 'N/A')
                st.metric("目标价格", f"{target_price}")
                
                position_size = final_decision.get('position_size', 'N/A')
                st.metric("建议仓位", f"{position_size}")
            
            with col2:
                st.markdown("**🎯 操作建议:**")
                st.write(final_decision.get('operation_advice', '暂无建议'))
                
                st.markdown("**📍 关键位置:**")
                col2_1, col2_2 = st.columns(2)
                
                with col2_1:
                    st.write(f"**进场区间:** {final_decision.get('entry_range', 'N/A')}")
                    st.write(f"**止盈位:** {final_decision.get('take_profit', 'N/A')}")
                
                with col2_2:
                    st.write(f"**止损位:** {final_decision.get('stop_loss', 'N/A')}")
                    st.write(f"**持有周期:** {final_decision.get('holding_period', 'N/A')}")
        else:
            decision_text = final_decision.get('decision_text', str(final_decision))
            st.write(decision_text)
    
    # 返回按钮
    st.markdown("---")
    if st.button("⬅️ 返回历史记录列表"):
        if 'viewing_record_id' in st.session_state:
            del st.session_state.viewing_record_id
        st.rerun()

if __name__ == "__main__":
    main()