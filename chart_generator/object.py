import json
import pandas as pd
from datetime import datetime, timedelta
from chart_generator.functions import *

from dotenv import load_dotenv
from elasticsearch import Elasticsearch
load_dotenv()  

es = Elasticsearch(os.getenv('ES_HOST',"http://34.101.178.71:9200/"),
    basic_auth=(os.getenv("ES_USERNAME","elastic"),os.getenv('ES_PASSWORD',"elasticpassword"))  # Sesuaikan dengan kredensial Anda
        )

def create_sentiment_distribution_chart_backup(df, title="Sentiment Distribution by Entity", figsize=(20, 15)):

    # Convert to DataFrame and sort by total mentions
    df = df.sort_values('total_mentions')
    
    # Create figure with two subplots (left for labels, right for chart)
    fig, (ax_labels, ax) = plt.subplots(1, 2, figsize=figsize, 
                                        gridspec_kw={'width_ratios': [1, 4]})
    
    # Set background color to white
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    ax_labels.set_facecolor('white')
    
    # Create horizontal bars in the right subplot
    y_pos = np.arange(len(df))
    bar_height = 0.6  # Thinner bars
    
    # Plot negative mentions (left side)
    negative_bars = ax.barh(y_pos, -df['negative_mentions'], height=bar_height, 
                           align='center', color='#FF9999', zorder=3)
    
    # Plot positive mentions (right side)
    positive_bars = ax.barh(y_pos, df['positive_mentions'], height=bar_height, 
                           align='center', color='#8fdfa8', zorder=3)
    
    # Add entity labels in the left subplot
    for i, entity in enumerate(df['object_item']):
        # Add light gray background for entity names
        entity_bg = patches.Rectangle((0, i-0.3), 1, 0.6, 
                                     facecolor='#f0f0f0', 
                                     edgecolor=None,
                                     zorder=1)
        ax_labels.add_patch(entity_bg)
        
        # Add entity name
        ax_labels.text(0.05, i, entity, va='center', fontsize=16, zorder=4)
    
    # Add value labels to the main chart
    for i, (pos, neg) in enumerate(zip(df['positive_mentions'], df['negative_mentions'])):
        if pos > 0:
            ax.text(pos + 3, i, f"{int(pos)} ({df['positive_percentage'].iloc[i]:.1f}%)", 
                    va='center', color='#228B22', fontsize=16, zorder=4)
        if neg > 0:
            ax.text(-neg - 3, i, f"{int(neg)} ({df['negative_percentage'].iloc[i]:.1f}%)", 
                    va='center', ha='right', color='#B22222', fontsize=16, zorder=4)
        elif neg == 0:
            ax.text(-3, i, f"{int(neg)} ({df['negative_percentage'].iloc[i]:.1f}%)", 
                    va='center', ha='right', color='#B22222', fontsize=16, zorder=4)
    
    # Create symmetrical x-axis for the main chart
    max_value = max(df['positive_mentions'].max(), df['negative_mentions'].max())
    buffer = max_value * 0.15  # Add some buffer space
    ax.set_xlim(-max_value - buffer, max_value + buffer)
    
    # Format x-axis with custom tick locations
    ticks = [tick for tick in range(-350, 351, 50) if tick != 0]
    ax.set_xticks(ticks)
    ax.set_xticklabels([str(abs(tick)) for tick in ticks])
    
    # Remove ticks from both subplots
    ax.set_yticks([])
    ax_labels.set_yticks([])
    ax_labels.set_xticks([])
    
    # Set limits for the labels subplot
    ax_labels.set_xlim(0, 1)
    ax_labels.set_ylim(-0.5, len(df) - 0.5)
    
    # Add a center line to the main chart
    ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8, zorder=2)
    
    # Remove all spines
    for spine in ax.spines.values():
        spine.set_visible(False)
    for spine in ax_labels.spines.values():
        spine.set_visible(False)
    
    # Labels for the main chart
    ax.set_xlabel('Number of mentions', fontsize=16, labelpad=10)
    
    # Add labels for the sides
    fig.text(0.35, 0.062, 'Negative mentions', ha='center', color='#B22222', fontsize=16)
    fig.text(0.75, 0.062, 'Positive mentions', ha='center', color='#228B22', fontsize=16)
    
    # Ensure no space between subplots
    plt.subplots_adjust(wspace=0)
    
    # Adjust layout and add more padding at the bottom
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    
    return fig, ax_labels, ax

def create_sentiment_distribution_chart(df,  figsize=(22, 15), SAVE_PATH=None):
    # Prepare data
    if 'total_mentions' not in df.columns:
        df['total_mentions'] = df['positive_mentions'] + df['negative_mentions'] + df['neutral_mentions']
    df = df.sort_values('total_mentions', ascending=True).reset_index(drop=True)
    df['negative_percentage'] = (df['negative_mentions'] / df['total_mentions']) * 100
    df['neutral_percentage'] = (df['neutral_mentions'] / df['total_mentions']) * 100
    df['positive_percentage'] = (df['positive_mentions'] / df['total_mentions']) * 100

    # Colors
    COLOR_NEG = "#FF9999"
    COLOR_NEU = "#f0f0f0"
    COLOR_POS = "#8fdfa8"

    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    y_pos = np.arange(len(df))
    bar_height = 0.5

    # Draw bars
    neg_bars = ax.barh(y_pos, df['negative_mentions'], height=bar_height, color=COLOR_NEG, zorder=3)
    neu_bars = ax.barh(y_pos, df['neutral_mentions'], height=bar_height,
                       left=df['negative_mentions'], color=COLOR_NEU, zorder=3)
    pos_bars = ax.barh(y_pos, df['positive_mentions'], height=bar_height,
                       left=df['negative_mentions'] + df['neutral_mentions'], color=COLOR_POS, zorder=3)

    for bar in neg_bars + neu_bars + pos_bars:
        bar.set_edgecolor('white')
        bar.set_linewidth(0.6)

    # Add entity labels on left (inside ax), no ax_labels used anymore
    for i, entity in enumerate(df['object_item']):
        ax.text(-20, i, entity, va='center', ha='right', fontsize=12, fontweight='medium', color='#333')

    # Add percentage and total labels
    for i, row in df.iterrows():
        neg, neu, pos, total = row['negative_mentions'], row['neutral_mentions'], row['positive_mentions'], row['total_mentions']
        neg_perc, neu_perc, pos_perc = row['negative_percentage'], row['neutral_percentage'], row['positive_percentage']
        min_width = 50

        if neg > min_width:
            ax.text(neg / 2, i, f"{neg_perc:.0f}%", va='center', ha='center', color='#722F37', fontsize=10, fontweight='medium')
        elif neg > 0:
            ax.text(5, i, f"{neg_perc:.0f}%", va='center', ha='left', color='#722F37', fontsize=10)

        if neu > min_width:
            ax.text(neg + neu / 2, i, f"{neu_perc:.0f}%", va='center', ha='center', color='#555', fontsize=10)

        if pos > min_width:
            ax.text(neg + neu + pos / 2, i, f"{pos_perc:.0f}%", va='center', ha='center', color='#337B5F', fontsize=10)

        ax.text(neg + neu + pos + 10, i, f"Total: {int(total)}", va='center', ha='left', color='#333', fontsize=10)

    # Adjust layout
    max_val = df['total_mentions'].max()
    buffer = max_val * 0.15
    ax.set_xlim(-50, max_val + buffer)  # allow space for labels on the left
    ax.set_ylim(-0.5, len(df) - 0.5)
    ax.set_yticks([])
    ax.set_xticks(np.arange(0, max_val + buffer, max(100, int(max_val / 8))))
    ax.set_xticklabels([str(int(x)) for x in ax.get_xticks()], fontsize=10)
    ax.set_xlabel('Number of mentions', fontsize=12)

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.grid(axis='x', linestyle='--', alpha=0.3, zorder=1)

    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color=COLOR_NEG, lw=10, label='Negative'),
        Line2D([0], [0], color=COLOR_NEU, lw=10, label='Neutral'),
        Line2D([0], [0], color=COLOR_POS, lw=10, label='Positive'),
    ]
    ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, -0.08),
              frameon=False, fontsize=11, ncol=3)

    plt.tight_layout(rect=[0, 0.08, 1, 0.95])
    save_file = os.path.join(SAVE_PATH, 'sentiment_distribution_by_entity.png')
    plt.savefig(save_file, dpi=70, bbox_inches='tight', transparent=True)
def generate_object(KEYWORDS, START_DATE, END_DATE, limit=10, SAVE_PATH=None):
    """
    Mengambil data sentimen terhadap objek dari Elasticsearch.
    
    Parameters:
    -----------
    KEYWORDS : List[str]
        Daftar keyword untuk filter
    START_DATE : str
        Tanggal awal periode (YYYY-MM-DD)
    END_DATE : str
        Tanggal akhir periode (YYYY-MM-DD)
    limit : int, optional
        Jumlah objek yang akan ditampilkan (default: 10)
        
    Returns:
    --------
    pd.DataFrame
        DataFrame yang berisi object_item, total_mentions, positive_mentions, 
        negative_mentions, neutral_mentions, positive_percentage,
        negative_percentage, dan neutral_percentage
    """

    
    # Definisikan channel dan indeks
    # Exclude channel news seperti di query SQL
    channels = ['reddit', 'youtube', 'linkedin', 'twitter', 
               'tiktok', 'instagram', 'facebook', 'threads']
    indices = [f"{ch}_data" for ch in channels]
    
    # Build keyword filter 
    keyword_conditions = []
    for kw in KEYWORDS:
        keyword_conditions.append({"match": {"post_caption": {"query": kw, "operator": "AND"}}})
        keyword_conditions.append({"match": {"issue": {"query": kw, "operator": "AND"}}})
    
    keyword_filter = {
        "bool": {
            "should": keyword_conditions,
            "minimum_should_match": 1
        }
    }
    
    # Bangun query untuk mengambil data dengan aggregasi
    # Karena object sudah dalam bentuk list, kita bisa gunakan nested aggregation
    query = {
        "size": 0,  # Tidak perlu dokumen, hanya aggregasi
        "query": {
            "bool": {
                "must": [
                    {
                        "range": {
                            "post_created_at": {
                                "gte": START_DATE,
                                "lte": END_DATE
                            }
                        }
                    },
                    keyword_filter,
                    {
                        "exists": {
                            "field": "object"
                        }
                    }
                ],
                "must_not": [
                    {
                        "term": {
                            "channel": "news"
                        }
                    },
                    {
                        "term": {
                            "object": "not specified"
                        }
                    }
                ],
                "filter": [
                    {
                        "terms": {
                            "sentiment": ["positive", "negative", "neutral"]
                        }
                    }
                ]
            }
        },
        "aggs": {
            "objects": {
                "terms": {
                    "field": "object",
                    "size": 1000,  # Ambil banyak objek untuk memastikan mendapat yang paling relevan
                    "order": {"_count": "desc"}
                },
                "aggs": {
                    "sentiment_breakdown": {
                        "terms": {
                            "field": "sentiment",
                            "size": 3  # positive, negative, neutral
                        }
                    }
                }
            }
        }
    }
    
    # Execute query
    response = es.search(
        index=",".join(indices),
        body=query
    )
    
    # Proses hasil aggregasi
    object_buckets = response["aggregations"]["objects"]["buckets"]
    
    # Siapkan data untuk DataFrame
    data = []
    
    for obj_bucket in object_buckets:
        object_item = obj_bucket["key"].strip().lower()
        
        # Skip objek kosong atau "not specified"
        if not object_item or object_item == "not specified":
            continue
        
        total_mentions = obj_bucket["doc_count"]
        
        # Inisialisasi hitungan sentimen
        positive_mentions = 0
        negative_mentions = 0
        neutral_mentions = 0
        
        # Ambil breakdown sentimen
        sentiment_buckets = obj_bucket["sentiment_breakdown"]["buckets"]
        
        for sentiment_bucket in sentiment_buckets:
            sentiment = sentiment_bucket["key"].lower()
            count = sentiment_bucket["doc_count"]
            
            if sentiment == "positive":
                positive_mentions = count
            elif sentiment == "negative":
                negative_mentions = count
            elif sentiment == "neutral":
                neutral_mentions = count
        
        # Hitung persentase
        positive_percentage = round((positive_mentions / total_mentions) * 100, 1) if total_mentions > 0 else 0
        negative_percentage = round((negative_mentions / total_mentions) * 100, 1) if total_mentions > 0 else 0
        neutral_percentage = round((neutral_mentions / total_mentions) * 100, 1) if total_mentions > 0 else 0
        
        data.append({
            "object_item": object_item,
            "total_mentions": total_mentions,
            "positive_mentions": positive_mentions,
            "negative_mentions": negative_mentions,
            "neutral_mentions": neutral_mentions,
            "positive_percentage": positive_percentage,
            "negative_percentage": negative_percentage,
            "neutral_percentage": neutral_percentage
        })
    
    # Buat DataFrame
    df = pd.DataFrame(data)
    
    # Jika objek berisi koma, handle seperti dipisahkan
    # Ini untuk memastikan kompatibilitas jika ada koma dalam objek
    split_data = []
    for _, row in df.iterrows():
        object_items = row["object_item"].split(",")
        
        for item in object_items:
            item = item.strip().lower()
            if not item or item == "not specified":
                continue
                
            # Tambahkan item baru dengan nilai yang sama
            split_data.append({
                "object_item": item,
                "total_mentions": row["total_mentions"],
                "positive_mentions": row["positive_mentions"],
                "negative_mentions": row["negative_mentions"],
                "neutral_mentions": row["neutral_mentions"],
                "positive_percentage": row["positive_percentage"],
                "negative_percentage": row["negative_percentage"],
                "neutral_percentage": row["neutral_percentage"]
            })
    
    # Jika ada data yang di-split, gunakan itu, jika tidak, gunakan data asli
    if split_data:
        df = pd.DataFrame(split_data)
        
        # Gabungkan item yang sama
        df = df.groupby("object_item").agg({
            "total_mentions": "sum",
            "positive_mentions": "sum",
            "negative_mentions": "sum",
            "neutral_mentions": "sum"
        }).reset_index()
        
        # Hitung ulang persentase
        df["positive_percentage"] = df.apply(
            lambda x: round((x["positive_mentions"] / x["total_mentions"]) * 100, 1) if x["total_mentions"] > 0 else 0, 
            axis=1
        )
        df["negative_percentage"] = df.apply(
            lambda x: round((x["negative_mentions"] / x["total_mentions"]) * 100, 1) if x["total_mentions"] > 0 else 0, 
            axis=1
        )
        df["neutral_percentage"] = df.apply(
            lambda x: round((x["neutral_mentions"] / x["total_mentions"]) * 100, 1) if x["total_mentions"] > 0 else 0, 
            axis=1
        )
    
    # Urutkan berdasarkan total mentions (descending) dan ambil top 'limit'
    df = df.sort_values(by="total_mentions", ascending=False).head(limit)
    

    df.to_csv(os.path.join(SAVE_PATH, 'sentiment_distribution_by_entity.csv'), index=False)


    create_sentiment_distribution_chart(df,SAVE_PATH = SAVE_PATH)

 