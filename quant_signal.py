import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go

st.set_page_config(page_title="퀀트 시그널", layout="wide")
st.title("📊 추세추종 퀀트 시그널")

@st.cache_data(ttl=3600)
def load_data(ticker):
    df = yf.download(ticker, period="5y")
    close = df['Close'][ticker]
    df['EMA200'] = ta.trend.ema_indicator(close, window=200)
    df['Momentum'] = close - close.shift(21)
    df['BB_upper'] = ta.volatility.bollinger_hband(close, window=20, window_dev=2)
    return df, close

def get_signal(df, ticker):
    latest = df.iloc[-1]
    c = float(latest['Close'][ticker])
    e = float(latest['EMA200'])
    m = float(latest['Momentum'])
    b = float(latest['BB_upper'])
    if c > b * 1.03:
        return '🔴 BB익절', c, e, m, b
    elif c > e and m > 0:
        return '🟢 매수유지', c, e, m, b
    else:
        return '🟡 추세청산', c, e, m, b

# 탭
tab1, tab2, tab3, tab4 = st.tabs(["QQQ", "TQQQ", "QQQU", "IONQ"])

for tab, ticker in zip([tab1, tab2, tab3, tab4], ["QQQ", "TQQQ", "QQQU", "IONQ"]):
    with tab:
        df, close = load_data(ticker)
        signal, c, e, m, b = get_signal(df, ticker)

        st.subheader(f"🗓️ {ticker} 시그널 ({df.index[-1].strftime('%Y-%m-%d')})")

        if '🔴' in signal:
            st.error(f"{signal} — 내일 시초가 매도")
        elif '🟢' in signal:
            st.success(f"{signal} — 보유 or 진입")
        else:
            st.warning(f"{signal} — 내일 시초가 매도")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric(f"{ticker} 종가", f"${c:.2f}")
        col2.metric("EMA200", f"${e:.2f}", "위" if c > e else "아래")
        col3.metric("모멘텀", f"{m:.2f}", "양수" if m > 0 else "음수")
        col4.metric("BB 상단", f"${b:.2f}", "돌파!" if c > b * 1.03 else "안전")

        df['Signal'] = '대기'
        df.loc[(close > df['EMA200']) & (df['Momentum'] > 0), 'Signal'] = '매수'
        df.loc[close > df['BB_upper'] * 1.03, 'Signal'] = 'BB익절'
        df.loc[df['Momentum'] < 0, 'Signal'] = '청산'

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=close, name=ticker, line=dict(color='white', width=1)))
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], name='EMA200', line=dict(color='yellow', width=2)))
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_upper'], name='BB 상단', line=dict(color='orange', width=1, dash='dash')))

        buy = df[df['Signal'] == '매수']
        fig.add_trace(go.Scatter(x=buy.index, y=buy['Close'][ticker], mode='markers',
            name='매수', marker=dict(color='lime', size=5)))

        bb_exit = df[df['Signal'] == 'BB익절']
        fig.add_trace(go.Scatter(x=bb_exit.index, y=bb_exit['Close'][ticker], mode='markers',
            name='BB익절', marker=dict(color='red', size=8, symbol='triangle-down')))

        fig.update_layout(template='plotly_dark', height=500, title=f'{ticker} 시그널 차트')
        st.plotly_chart(fig, use_container_width=True)

        # IONQ 경고 메시지
        if ticker == 'IONQ':
            st.info("⚠️ IONQ는 개별 종목으로 이 시스템은 QQQ 지수 기반으로 검증됐어요. 참고용으로만 활용하세요.")