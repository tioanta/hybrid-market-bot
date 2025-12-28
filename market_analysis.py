import yfinance as yf
import pandas as pd
from prophet import Prophet
import feedparser
from textblob import TextBlob

def get_technical_forecast(ticker):
    """Mengambil data historis dan melakukan prediksi Prophet"""
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df.empty: return None, None, None
        
        df.reset_index(inplace=True)
        if 'Date' in df.columns: df['ds'] = df['Date']
        else: df['ds'] = df.index
        
        if isinstance(df.columns, pd.MultiIndex):
            try: df['y'] = df[('Close', ticker)]
            except KeyError: df['y'] = df['Close']
        else: df['y'] = df['Close']
        
        df = df[['ds', 'y']].dropna()
        
        m = Prophet(daily_seasonality=True)
        m.fit(df)
        future = m.make_future_dataframe(periods=1)
        forecast = m.predict(future)
        
        current_price = float(df.iloc[-1]['y'])
        predicted_price = forecast.iloc[-1]['yhat']
        
        return df, current_price, predicted_price
        
    except Exception as e:
        print(f"Error Technical {ticker}: {e}")
        return None, None, None

def get_news_sentiment(keyword):
    """Membaca berita dan menghitung skor sentimen"""
    try:
        query = keyword.replace(" ", "%20")
        rss_url = f"https://news.google.com/rss/search?q={query}+when:2d&hl=en-ID&gl=ID&ceid=ID:en"
        feed = feedparser.parse(rss_url)
        
        if not feed.entries: return 0, "No News"

        polarities = []
        for entry in feed.entries[:5]:
            analysis = TextBlob(entry.title)
            polarities.append(analysis.sentiment.polarity)
        
        if not polarities: return 0, "Neutral"

        avg = sum(polarities) / len(polarities)
        
        if avg > 0.1: return avg, "Positif 🟢"
        elif avg < -0.1: return avg, "Negatif 🔴"
        else: return avg, "Netral ⚪"
        
    except Exception as e:
        print(f"Error News: {e}")
        return 0, "Error"

def get_hybrid_signal(current, pred, sentiment_score):
    """Menggabungkan hasil Teknikal dan Sentimen"""
    diff_percent = (pred - current) / current
    
    tech_signal = "HOLD"
    if diff_percent > 0.005: tech_signal = "BUY"
    elif diff_percent < -0.005: tech_signal = "SELL"
    
    final_call = "HOLD"
    reason = "Wait & See"

    if tech_signal == "BUY":
        if sentiment_score > 0.05:
            final_call = "STRONG BUY 🚀"
            reason = "Tech Up + News Good"
        elif sentiment_score < -0.05:
            final_call = "WEAK BUY ⚠️"
            reason = "Tech Up but News Bad"
        else:
            final_call = "BUY"
            reason = "Technical Breakout"
    elif tech_signal == "SELL":
        if sentiment_score < -0.05:
            final_call = "STRONG SELL 🔻"
            reason = "Tech Down + News Bad"
        elif sentiment_score > 0.05:
            final_call = "WAIT 👀"
            reason = "Tech Down but News Good"
        else:
            final_call = "SELL"
            reason = "Technical Correction"
    else:
        if abs(sentiment_score) > 0.15:
            final_call = "WATCHLIST 📋"
            reason = "High Volatility News"
            
    return final_call, f"{diff_percent*100:.2f}%", reason
