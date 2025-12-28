import os
import random
import yfinance as yf
import pandas as pd
from prophet import Prophet
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from instagrapi import Client
import feedparser
from textblob import TextBlob

# --- KONFIGURASI ---
sns.set_theme(style="darkgrid")
plt.rcParams['figure.figsize'] = (12, 12)
plt.rcParams['font.family'] = 'sans-serif'

COLORS = {'BELI': '#2ecc71', 'JUAL': '#e74c3c', 'HOLD': '#95a5a6'}

# Daftar Aset (Forex & Saham)
# Format Saham Indonesia di Yahoo Finance pakai akhiran .JK
ASSETS = {
    'USD': {'ticker': 'USDIDR=X', 'type': 'forex', 'keyword': 'USD IDR currency'},
    'JPY': {'ticker': 'JPYIDR=X', 'type': 'forex', 'keyword': 'JPY IDR currency'},
    'BBRI': {'ticker': 'BBRI.JK', 'type': 'stock', 'keyword': 'Bank BRI Indonesia stock'},
    'TLKM': {'ticker': 'TLKM.JK', 'type': 'stock', 'keyword': 'Telkom Indonesia stock'}
}

# Bank Pertanyaan
QUESTIONS = [
    "Saham atau Forex, mana yang bikin cuan hari ini? 🤔",
    "Sentimen berita lagi panas! Apa strategimu? 🔥",
    "BBRI & TLKM lagi jadi sorotan, tim serok atau tim kabur? 🏃‍♂️",
    "Menurutmu analisa berita ngaruh banget gak sih ke harga? 📰",
    "Ada yang portofolionya hijau royo-royo hari ini? 🍀"
]

# --- FUNGSI SENTIMEN BERITA (BARU) ---
def get_news_sentiment(keyword):
    """
    Mengambil berita dari Google News (2 hari terakhir)
    dan menghitung rata-rata sentimennya (-1 s/d +1)
    """
    try:
        # Encode keyword spasi jadi %20
        query = keyword.replace(" ", "%20")
        # URL RSS Google News (Bahasa Inggris agar TextBlob akurat)
        rss_url = f"https://news.google.com/rss/search?q={query}+when:2d&hl=en-ID&gl=ID&ceid=ID:en"
        
        feed = feedparser.parse(rss_url)
        
        if not feed.entries:
            return 0, "No News"

        polarities = []
        print(f"   -> Menemukan {len(feed.entries)} berita untuk '{keyword}'")

        for entry in feed.entries[:5]: # Ambil 5 berita teratas saja
            analysis = TextBlob(entry.title)
            polarities.append(analysis.sentiment.polarity)
        
        if not polarities:
            return 0, "Neutral"

        avg_polarity = sum(polarities) / len(polarities)
        
        # Tentukan Label
        if avg_polarity > 0.1: label = "Positif 🟢"
        elif avg_polarity < -0.1: label = "Negatif 🔴"
        else: label = "Netral ⚪"
        
        return avg_polarity, label

    except Exception as e:
        print(f"   !! Error ambil berita: {e}")
        return 0, "Error"

# --- FUNGSI REKOMENDASI HYBRID ---
def get_hybrid_recommendation(current, pred, sentiment_score):
    # 1. Hitung Technical (Berdasarkan Harga)
    diff_percent = (pred - current) / current
    tech_signal = "HOLD"
    if diff_percent > 0.005: tech_signal = "BUY"    # Naik > 0.5%
    elif diff_percent < -0.005: tech_signal = "SELL" # Turun > 0.5%
    
    # 2. Gabungkan dengan Sentimen
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
    
    else: # HOLD Condition
        if abs(sentiment_score) > 0.15: # Jika berita sangat kuat
            final_call = "WATCHLIST 📋"
            reason = "High Volatility News"
            
    return final_call, f"{diff_percent*100:.2f}%", reason

def plot_asset(ax, name, df_recent, current, pred, signal, change, sentiment_label):
    # Plot Garis
    ax.plot(df_recent['ds'], df_recent['y'], label='Historis', color='#3498db', linewidth=2)
    
    # Titik Prediksi
    pred_date = df_recent['ds'].iloc[-1] + timedelta(days=1)
    ax.scatter(pred_date, pred, color='#e67e22', s=150, zorder=5)
    
    # Anotasi Harga
    ax.annotate(f"{current:,.0f}", (df_recent['ds'].iloc[-1], current), 
                xytext=(10, -20), textcoords='offset points', color='white', fontsize=8)
    
    # Info Box (Sinyal + Sentimen)
    rec_color = '#2ecc71' if 'BUY' in signal else ('#e74c3c' if 'SELL' in signal else '#95a5a6')
    
    box_text = f"{name}\n{signal}\n({change})\nNews: {sentiment_label}"
    
    props = dict(boxstyle='round,pad=0.5', facecolor=rec_color, alpha=0.9, edgecolor='none')
    ax.text(0.05, 0.95, box_text, transform=ax.transAxes, fontsize=10,
            fontweight='bold', color='white', verticalalignment='top', bbox=props)

    ax.set_title(f"{name}", fontsize=11, color='white')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
    ax.set_facecolor('#2c3e50')

def upload_to_instagram(image_path, caption_text):
    print("--- UPLOAD INSTAGRAM ---")
    username = os.environ.get("IG_USERNAME")
    password = os.environ.get("IG_PASSWORD")
    session_id = os.environ.get("IG_SESSION_ID")
    cl = Client()
    cl.delay_range = [1, 3]

    try:
        if session_id:
            print("Login via Session ID...")
            cl.login_by_sessionid(session_id)
        else:
            cl.login(username, password)
        
        try:
            cl.account_info()
        except:
            print("Session expired/invalid.")
            return

        cl.photo_upload(path=image_path, caption=caption_text)
        print("🎉 Upload Berhasil!")
        
    except Exception as e:
        print(f"Gagal Upload: {e}")

def run_bot():
    today_str = datetime.now().strftime('%Y-%m-%d')
    print(f"--- MULAI ANALISA HYBRID: {today_str} ---")
    
    plt.style.use('dark_background')
    fig, axs = plt.subplots(2, 2)
    fig.suptitle(f"MARKET FORECAST (Hybrid Analysis)\n{today_str}", fontsize=16, fontweight='bold', color='white')
    axs_flat = axs.flatten()
    
    caption_summary = f"🤖 Market Analysis (Tech + News) - {today_str}\n\n"
    has_data = False

    for i, (name, info) in enumerate(ASSETS.items()):
        ax = axs_flat[i]
        ticker = info['ticker']
        keyword = info['keyword']
        
        print(f"\nMemproses {name} ({ticker})...")
        
        try:
            # 1. AMBIL DATA HARGA
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
            if df.empty: continue
            
            df.reset_index(inplace=True)
            if 'Date' in df.columns: df['ds'] = df['Date']
            else: df['ds'] = df.index
            
            if isinstance(df.columns, pd.MultiIndex):
                try: df['y'] = df[('Close', ticker)]
                except KeyError: df['y'] = df['Close']
            else: df['y'] = df['Close']
            
            df = df[['ds', 'y']].dropna()
            
            # 2. ANALISA TEKNIKAL (PROPHET)
            m = Prophet(daily_seasonality=True)
            m.fit(df)
            future = m.make_future_dataframe(periods=1)
            forecast = m.predict(future)
            
            current = float(df.iloc[-1]['y'])
            pred = forecast.iloc[-1]['yhat']
            
            # 3. ANALISA SENTIMEN BERITA
            sentiment_score, sentiment_label = get_news_sentiment(keyword)
            
            # 4. GABUNGKAN REKOMENDASI
            signal, change, reason = get_hybrid_recommendation(current, pred, sentiment_score)
            
            # Plotting
            plot_asset(ax, name, df.tail(60), current, pred, signal, change, sentiment_label)
            
            # Caption Text
            icon = "📈" if "BUY" in signal else ("📉" if "SELL" in signal else "⚖️")
            caption_summary += f"{icon} {name}: {signal}\n   News: {sentiment_label} | {reason}\n"
            has_data = True
            
        except Exception as e:
            print(f"Error {name}: {e}")
            continue

    if not has_data: return

    plt.tight_layout(rect=[0, 0.03, 1, 0.90])
    filename = "market_forecast.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    
    # Tambahkan Pertanyaan
    caption_summary += f"\n❓ {random.choice(QUESTIONS)}\n"
    caption_summary += "\nDisclaimer: Not Financial Advice. Hybrid Analysis (Technical + News Sentiment).\n#saham #forex #bbri #tlkm #investasi #hargasaham"
    
    upload_to_instagram(filename, caption_summary)

if __name__ == "__main__":
    run_bot()
