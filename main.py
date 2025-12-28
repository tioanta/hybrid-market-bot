import random
from datetime import datetime
import config
import market_analysis
import visualizer
import insta_uploader

def run():
    today_str = datetime.now().strftime('%Y-%m-%d')
    print(f"--- MULAI PROSES UTAMA: {today_str} ---")
    
    fig, axs = visualizer.setup_canvas(today_str)
    
    caption_summary = f"🤖 Market Analysis (Tech + News) - {today_str}\n\n"
    has_data = False

    for i, (name, info) in enumerate(config.ASSETS.items()):
        print(f"\nMemproses {name}...")
        
        df, current, pred = market_analysis.get_technical_forecast(info['ticker'])
        if df is None: continue
        
        sentiment_score, sentiment_label = market_analysis.get_news_sentiment(info['keyword'])
        signal, change, reason = market_analysis.get_hybrid_signal(current, pred, sentiment_score)
        
        visualizer.plot_asset(axs[i], name, df.tail(60), current, pred, signal, change, sentiment_label)
        
        icon = "📈" if "BUY" in signal else ("📉" if "SELL" in signal else "⚖️")
        caption_summary += f"{icon} {name}: {signal}\n   News: {sentiment_label} | {reason}\n"
        has_data = True

    if not has_data:
        print("Tidak ada data berhasil diolah. Stop.")
        return

    image_file = "market_forecast.png"
    visualizer.save_image(image_file)
    
    caption_summary += f"\n❓ {random.choice(config.QUESTIONS)}\n"
    caption_summary += "\nDisclaimer: Not Financial Advice. Hybrid Analysis (Technical + News).\n#saham #forex #investasi #bbri #tlkm"
    
    insta_uploader.upload_image(image_file, caption_summary)

if __name__ == "__main__":
    run()
