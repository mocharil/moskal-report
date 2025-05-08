from chart_generator.functions import *
import numpy as np
from elasticsearch import Elasticsearch
from dotenv import load_dotenv
load_dotenv()  

es = Elasticsearch(os.getenv('ES_HOST',"http://34.101.178.71:9200/"),
    basic_auth=(os.getenv("ES_USERNAME","elastic"),os.getenv('ES_PASSWORD',"elasticpassword"))  # Sesuaikan dengan kredensial Anda
        )

def plot_half_donut_sentiment(sentiment_counts, colors=None, title=None, save_path = None):
    """
    Buat half-donut gauge chart dari distribusi sentimen.
    """
    labels = list(sentiment_counts.keys())
    values = list(sentiment_counts.values())
    total = sum(values)
    angles = [v / total * 180 for v in values]

    # Default colors
    if colors is None:
        colors = {
            'Positive': '#53b06c',  # green
            'Neutral': '#f5f5f5',   # gray
            'Negative': '#de5242'   # red
        }

    fig, ax = plt.subplots(figsize=(8, 5), subplot_kw={'projection': 'polar'})
    ax.set_theta_direction(-1)
    ax.set_theta_offset(np.pi)
    ax.set_axis_off()

    current_angle = 0
    for label, angle in zip(labels, angles):
        ax.bar(
            x=np.radians(current_angle + angle / 2),
            height=0.4,                 # donut thickness
            width=np.radians(angle),
            bottom=0.7,                 # offset from center (creates hole)
            color=colors.get(label, 'gray'),
            edgecolor='white',
            linewidth=2
        )
        current_angle += angle

    # Legend Labels & Color-Coded Dots
    legend_labels = [f"{label} ({sentiment_counts[label]})" for label in labels]
    handles = [
        mlines.Line2D(
            [], [], color=colors[label], marker='o', linestyle='None',
            markersize=14, label=legend_labels[i]
        )
        for i, label in enumerate(labels)
    ]

    ax.legend(
        handles,
        legend_labels,
        loc='lower center',
        bbox_to_anchor=(0.5, 0.35),
        ncol=len(labels),
        frameon=False
    )
    plt.tight_layout()
    plt.savefig(save_path, dpi=75, bbox_inches='tight',transparent=True)
 
def plot_sentiment_by_channel(df, title="Sentiment Breakdown per Channel", save_path=None):
    df = df.sort_values(by='total_mentions', ascending=False).reset_index(drop=True)
    labels = df['channel']
    pos = df['Positive']
    neu = df['Neutral']
    neg = df['Negative']
    totals = pos + neu + neg
    pos_pct = pos / totals * 100
    neu_pct = neu / totals * 100
    neg_pct = neg / totals * 100
    x = np.arange(len(labels))
    width = 0.6
    fig, ax = plt.subplots(figsize=(8, 4))
    colors = {
        'Positive': '#53b06c',
        'Neutral': '#f5f5f5',
        'Negative': '#de5242'
    }
    p1 = ax.bar(x, pos, width, label='Positive', color=colors['Positive'])
    p2 = ax.bar(x, neu, width, bottom=pos, label='Neutral', color=colors['Neutral'])
    p3 = ax.bar(x, neg, width, bottom=pos+neu, label='Negative', color=colors['Negative'])
    # Tambahkan label persentase dengan background box
    for i in range(len(x)):
        if pos[i] > 0:
            ax.text(
                x[i], pos[i] / 2,
                f"{pos_pct[i]:.1f}%",
                ha='center', va='center',
                fontsize=9, color='white',
                bbox=dict(boxstyle='round,pad=0.2', facecolor=colors['Positive'], edgecolor='none')
            )
        if neu[i] > 0:
            ax.text(
                x[i], pos[i] + neu[i] / 2,
                f"{neu_pct[i]:.1f}%",
                ha='center', va='center',
                fontsize=9, color='black',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='none')
            )
        if neg[i] > 0:
            ax.text(
                x[i], pos[i] + neu[i] + neg[i] / 2,
                f"{neg_pct[i]:.1f}%",
                ha='center', va='center',
                fontsize=9, color='white',
                bbox=dict(boxstyle='round,pad=0.2', facecolor=colors['Negative'], edgecolor='none')
            )
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    # Add this:
    ax.tick_params(axis='x', colors='#757575')
    ax.tick_params(axis='y', colors='#757575')
    ax.set_ylim(0, df[['Positive', 'Neutral', 'Negative']].sum(axis=1).max() * 1.2)
    # Remove all spines
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    # Menghapus baris yang error - tidak ada ax_labels yang didefinisikan
    # for spine in ax_labels.spines.values():
    #     spine.set_visible(False)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=75, bbox_inches='tight', transparent=True)

def get_sentiment_posts(KEYWORDS, START_DATE, END_DATE, limit=50):
    
    # Definisikan channel dan indeks
    default_channels = ['reddit', 'youtube', 'linkedin', 'twitter', 
                       'tiktok', 'instagram', 'facebook', 'news', 'threads']
    indices = [f"{ch}_data" for ch in default_channels]
    
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
    
    # Script untuk menghitung engagement score
    engagement_script = """
    def likes = doc.containsKey('likes') && !doc['likes'].empty ? doc['likes'].value : 0;
    def shares = doc.containsKey('shares') && !doc['shares'].empty ? doc['shares'].value : 0;
    def comments = doc.containsKey('comments') && !doc['comments'].empty ? doc['comments'].value : 0;
    def favorites = doc.containsKey('favorites') && !doc['favorites'].empty ? doc['favorites'].value : 0;
    def views = doc.containsKey('views') && !doc['views'].empty ? doc['views'].value : 0;
    def retweets = doc.containsKey('retweets') && !doc['retweets'].empty ? doc['retweets'].value : 0;
    def replies = doc.containsKey('replies') && !doc['replies'].empty ? doc['replies'].value : 0;
    def reposts = doc.containsKey('reposts') && !doc['reposts'].empty ? doc['reposts'].value : 0;
    def votes = doc.containsKey('votes') && !doc['votes'].empty ? doc['votes'].value : 0;
    def reach_score = doc.containsKey('reach_score') && !doc['reach_score'].empty ? doc['reach_score'].value : 0;
    def viral_score = doc.containsKey('viral_score') && !doc['viral_score'].empty ? doc['viral_score'].value : 0;
    
    return likes + shares + comments + favorites + views + retweets + replies + reposts + votes + reach_score + viral_score;
    """
    
    # Fungsi untuk mendapatkan post berdasarkan sentiment
    def get_posts_by_sentiment(sentiment):
        query = {
            "size": limit,
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
                            "term": {
                                "sentiment": sentiment
                            }
                        }
                    ]
                }
            },
            "_source": ["post_caption", "channel", "sentiment", "likes", "shares", "comments", 
                        "favorites", "views", "retweets", "replies", "reposts", "votes", 
                        "reach_score", "viral_score", "link_post"],
            "sort": [
                {
                    "_script": {
                        "type": "number",
                        "script": {
                            "source": engagement_script
                        },
                        "order": "desc"
                    }
                }
            ]
        }
        
        try:
            response = es.search(
                index=",".join(indices),
                body=query
            )
            
            posts = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                
                # Hitung engagement score seperti di query SQL
                engagement = (
                    source.get("likes", 0) or 0 +
                    source.get("shares", 0) or 0 +
                    source.get("comments", 0) or 0 +
                    source.get("favorites", 0) or 0 +
                    source.get("views", 0) or 0 +
                    source.get("retweets", 0) or 0 +
                    source.get("replies", 0) or 0 +
                    source.get("reposts", 0) or 0 +
                    source.get("votes", 0) or 0 +
                    source.get("reach_score", 0) or 0 +
                    source.get("viral_score", 0) or 0
                )
                
                posts.append({
                    "post_caption": source.get("post_caption", ""),
                    "channel": source.get("channel", ""),
                    "sentiment": source.get("sentiment", ""),
                    "engagement": engagement,
                    "link_post": source.get("link_post", "")
                })
            
            return posts
            
        except Exception as e:
            print(f"Error querying Elasticsearch for {sentiment} posts: {e}")
            return []
    
    # Dapatkan posts dengan sentiment positif
    positive_posts = get_posts_by_sentiment("positive")
    
    # Dapatkan posts dengan sentiment negatif
    negative_posts = get_posts_by_sentiment("negative")
    
    # Gabungkan hasil
    all_posts = positive_posts + negative_posts
    
    # Konversi ke DataFrame
    sentiment_post = pd.DataFrame(all_posts)
    
    return sentiment_post

def get_sentiment_data(KEYWORDS, START_DATE, END_DATE):
    """
    Mendapatkan data sentiment dari Elasticsearch berdasarkan keyword dan rentang tanggal.
    
    Parameters:
    -----------
    KEYWORDS : List[str]
        Daftar keyword untuk filter
    START_DATE : str
        Tanggal awal periode (YYYY-MM-DD)
    END_DATE : str
        Tanggal akhir periode (YYYY-MM-DD)
        
    Returns:
    --------
    Tuple[Dict, pd.DataFrame]
        - sentiment_counts: Dict yang berisi total mentions per sentiment
        - pivot_sentiment: DataFrame dengan pivot sentiment per channel
    """
    
    # Definisikan channel dan indeks
    default_channels = ['reddit', 'youtube', 'linkedin', 'twitter', 
                       'tiktok', 'instagram', 'facebook', 'news', 'threads']
    indices = [f"{ch}_data" for ch in default_channels]
    
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
    
    # Query untuk mendapatkan data sentiment per channel
    query = {
        "size": 0,
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
                    keyword_filter
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
            "sentiments": {
                "terms": {
                    "field": "sentiment",
                    "size": 10
                },
                "aggs": {
                    "channels": {
                        "terms": {
                            "field": "channel",
                            "size": 20
                        }
                    }
                }
            }
        }
    }
    
    try:
        # Execute query
        response = es.search(
            index=",".join(indices),
            body=query
        )
        
        # Proses hasil untuk membuat sentiment_data DataFrame
        sentiment_data_rows = []
        
        sentiment_buckets = response["aggregations"]["sentiments"]["buckets"]
        for sentiment_bucket in sentiment_buckets:
            sentiment = sentiment_bucket["key"].lower()  # Lowercase untuk konsistensi
            
            channel_buckets = sentiment_bucket["channels"]["buckets"]
            for channel_bucket in channel_buckets:
                channel = channel_bucket["key"]
                total_mentions = channel_bucket["doc_count"]
                
                sentiment_data_rows.append({
                    "sentiment": sentiment,
                    "channel": channel,
                    "total_mentions": total_mentions
                })
        
        # Buat DataFrame
        sentiment_data = pd.DataFrame(sentiment_data_rows)
        
        # Title case sentiment (seperti dalam kode original)
        if not sentiment_data.empty:
            sentiment_data['sentiment'] = sentiment_data['sentiment'].str.title()
            
            # Hitung sentiment_counts (total mentions per sentiment)
            sentiment_counts = sentiment_data.groupby('sentiment')['total_mentions'].sum().to_dict()
            
            # Buat pivot_sentiment
            pivot_sentiment = pd.pivot_table(
                sentiment_data, 
                index=['channel'],
                columns=['sentiment'],
                values=['total_mentions'],
                aggfunc='sum',
                fill_value=0
            ).reset_index()
            
            # Flatten multi-index columns seperti pada kode original
            pivot_sentiment.columns = [''.join(i).replace('total_mentions', '') for i in pivot_sentiment.columns]
            
            # Tambahkan kolom total_mentions (jumlah dari semua sentiment per channel)
            non_channel_columns = [col for col in pivot_sentiment.columns if col != 'channel']
            pivot_sentiment['total_mentions'] = pivot_sentiment[non_channel_columns].sum(axis=1)
            
            return sentiment_counts, pivot_sentiment
        else:
            print("No sentiment data found")
            return {}, pd.DataFrame()
        
    except Exception as e:
        print(f"Error querying Elasticsearch: {e}")
        return {}, pd.DataFrame()

def summarize(TOPIC,KEYWORDS,START_DATE,END_DATE,sentiment_counts,pivot_sentiment, SAVE_PATH):
    # Mendapatkan data sentiment posts
    sentiment_post = get_sentiment_posts(
        KEYWORDS=KEYWORDS,
        START_DATE=START_DATE,
        END_DATE=END_DATE,
        limit=50
    )
    
    

    prompt = f"""
    You are a media analyst assistant. the TOPICS is about [{TOPIC}].

    Here is the supporting data:

    1. **Sentiment Breakdown (total mentions)**  
    {sentiment_counts}

    2. **Platform Breakdown (total mentions)**  
    {pivot_sentiment.to_dict(orient = 'records')}

    3. **Top Posts based on engagement**  
    {sentiment_post[['post_caption','channel','sentiment']].to_dict(orient='records')}

    ---

    **Instruction:**  
    - summarize the topic for Positive and Negative Topics
    - Summarize in **1 paragraph only** what likely caused the spike, which platform contributed the most, what sentiment dominated, and what topic(s) were most discussed — **only if relevant to [{TOPIC}]**. 
    - Use a professional, concise tone.
    - output in JSON format


    ** Sample Output **
    {{
    "positive_summarize":<summarize for sentiment positive no more than 50 words>,
    "negative_summarize":<summarize for sentiment negative no more than 50 words>
    }}


    """
    summarize_sentiment = call_gemini(prompt)


    with open(os.path.join(SAVE_PATH,'sentiment_analysis.json'),'w') as f:

        json.dump(eval(re.findall(r'\{.*\}', summarize_sentiment, flags = re.I|re.S)[0]), f)
                
def generate_sentiment_analysis(TOPIC,KEYWORDS,START_DATE,END_DATE, SAVE_PATH):
    sentiment_counts, pivot_sentiment = get_sentiment_data(KEYWORDS, START_DATE, END_DATE)
    


    with open(os.path.join(SAVE_PATH,'sentiment_breakdown.json'),'w') as f:
        f.write(json.dumps(sentiment_counts))
        
    with open(os.path.join(SAVE_PATH,'sentiment_by_categories.json'),'w') as f:
        f.write(json.dumps(pivot_sentiment.to_dict(orient = 'records')))
    #breakdown
    plot_half_donut_sentiment(sentiment_counts, title='Sentiment Distribution',
                              save_path = os.path.join(SAVE_PATH,'sentiment_breakdown.png'))

    #per platform
    plot_sentiment_by_channel(pivot_sentiment, save_path = os.path.join(SAVE_PATH,'sentiment_by_categories.png'))

    #summarize
    summarize(TOPIC,KEYWORDS,START_DATE,END_DATE,sentiment_counts,pivot_sentiment, SAVE_PATH)