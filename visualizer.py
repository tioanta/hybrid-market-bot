import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from datetime import timedelta
import config

def setup_canvas(date_str):
    sns.set_theme(style="darkgrid")
    plt.rcParams['figure.figsize'] = (12, 12)
    plt.rcParams['font.family'] = 'sans-serif'
    plt.style.use('dark_background')
    
    fig, axs = plt.subplots(2, 2)
    fig.suptitle(f"MARKET FORECAST (Hybrid Analysis)\n{date_str}", fontsize=16, fontweight='bold', color='white')
    return fig, axs.flatten()

def plot_asset(ax, name, df_recent, current, pred, signal, change, sentiment_label):
    ax.plot(df_recent['ds'], df_recent['y'], label='Historis', color='#3498db', linewidth=2)
    
    pred_date = df_recent['ds'].iloc[-1] + timedelta(days=1)
    ax.scatter(pred_date, pred, color='#e67e22', s=150, zorder=5)
    
    ax.annotate(f"{current:,.0f}", (df_recent['ds'].iloc[-1], current), 
                xytext=(10, -20), textcoords='offset points', color='white', fontsize=8)
    
    bg_color = config.COLORS['HOLD']
    if 'BUY' in signal: bg_color = config.COLORS['BELI']
    elif 'SELL' in signal: bg_color = config.COLORS['JUAL']
    
    box_text = f"{name}\n{signal}\n({change})\nNews: {sentiment_label}"
    props = dict(boxstyle='round,pad=0.5', facecolor=bg_color, alpha=0.9, edgecolor='none')
    
    ax.text(0.05, 0.95, box_text, transform=ax.transAxes, fontsize=10,
            fontweight='bold', color='white', verticalalignment='top', bbox=props)

    ax.set_title(f"{name}", fontsize=11, color='white')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
    ax.set_facecolor('#2c3e50')

def save_image(filename="market_forecast.png"):
    plt.tight_layout(rect=[0, 0.03, 1, 0.90])
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Gambar berhasil disimpan: {filename}")
