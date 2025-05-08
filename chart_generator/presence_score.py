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

def plot_donut_score(score, title="How much attention\na topic or figure gets", save_path=None):
    """
    Create a donut chart with score (0-100) in the center.
    
    Parameters:
        score (float): Score between 0 and 100
        title (str): Text shown below the chart
        save_path (str): Optional file path to save the chart
    """
    # Colors
    main_color = '#1a73e8'
    bg_color = '#e0e0e0'

    # Create figure
    fig, ax = plt.subplots(figsize=(3, 3))
    ax.pie([score, 100 - score],
           startangle=90,
           colors=[main_color, bg_color],
           wedgeprops=dict(width=0.42),
           counterclock=False)

    # Center text
    ax.text(0, 0, f"{int(round(score))}", ha='center', va='center', fontsize=40, color='#333333')

    # Title below the donut
    plt.text(0, -1.3, title, ha='center', va='center', fontsize=12, color='#757575')

    # Remove all axes
    ax.set_aspect('equal')
    plt.axis('off')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=75, transparent=True)

def plot_presence_score_trend(data, title="Your presence score", save_path=None,
                              show_dots=True, color_theme='#1a73e8'):
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    x = df['date']
    y = df['presence_score'].values

    # Smooth
    def smooth(x, y):
        if len(x) < 4:
            return x, y
        x_numeric = np.arange(len(x))
        spl = make_interp_spline(x_numeric, y, k=3)
        xnew = np.linspace(x_numeric.min(), x_numeric.max(), 300)
        ynew = spl(xnew)
        x_interp = np.interp(xnew, x_numeric, x.astype(np.int64) // 10**9)
        x_interp = pd.to_datetime(x_interp, unit='s')
        return x_interp, ynew

    x_smooth, y_smooth = smooth(x, y)

    # Plot
    fig, ax = plt.subplots(figsize=(12, 4))  # 33.35cm x 9.14cm
    ax.set_facecolor('#ffffff')
    fig.patch.set_facecolor('#ffffff')

    ax.plot(x_smooth, y_smooth, color=color_theme, label=title, linewidth=2)

    if show_dots:
        ax.scatter(x, y, color=color_theme, s=15, zorder=3)

    # Clean styling
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.tick_params(axis='y', colors=color_theme)
    ax.yaxis.label.set_color(color_theme)
    ax.grid(axis='y', linestyle='-', linewidth=0.5, alpha=0.3)

    ax.xaxis.set_major_formatter(DateFormatter('%d %b %Y'))
    plt.xticks(rotation=0)
    ax.xaxis.label.set_color('#5f6368')

    # Annotate peak
    peak_idx = np.argmax(y)
    peak_date = x.iloc[peak_idx]
    peak_value = y[peak_idx]
    label = f"{int(round(peak_value))} on {peak_date.strftime('%d %b %Y')}"
    ax.annotate(label, xy=(peak_date, peak_value), xytext=(peak_date, peak_value + 5),
                ha='center', fontsize=9, color=color_theme,
                arrowprops=dict(arrowstyle='-', color=color_theme, lw=1))

    # Legend
    ax.legend(loc='best', frameon=False)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=75, transparent=True)
        
def get_data(KEYWORDS, START_DATE, END_DATE):
    """
    Menghitung presence score dari data Elasticsearch menggunakan aggregation.
    
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
    pd.DataFrame
        DataFrame dengan kolom date dan presence_score
    """

    # Definisikan semua channel dan indeks
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
    
    # Bangun query dengan date_histogram aggregation
    # untuk mendapatkan total_mentions, total_reach, dan total_engagement per hari
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
                ]
            }
        },
        "aggs": {
            "data_per_day": {
                "date_histogram": {
                    "field": "post_created_at",
                    "calendar_interval": "day",
                    "format": "yyyy-MM-dd",
                    "min_doc_count": 0,
                    "extended_bounds": {
                        "min": START_DATE,
                        "max": END_DATE
                    }
                },
                "aggs": {
                    "total_reach": {
                        "sum": {
                            "field": "reach_score"
                        }
                    },
                    "total_engagement": {
                        "sum": {
                            "script": {
                                "source": """
                                    def likes = doc.containsKey('likes') && !doc['likes'].empty ? doc['likes'].value : 0;
                                    def shares = doc.containsKey('shares') && !doc['shares'].empty ? doc['shares'].value : 0;
                                    def comments = doc.containsKey('comments') && !doc['comments'].empty ? doc['comments'].value : 0;
                                    def favorites = doc.containsKey('favorites') && !doc['favorites'].empty ? doc['favorites'].value : 0;
                                    def views = doc.containsKey('views') && !doc['views'].empty ? doc['views'].value : 0;
                                    def retweets = doc.containsKey('retweets') && !doc['retweets'].empty ? doc['retweets'].value : 0;
                                    def replies = doc.containsKey('replies') && !doc['replies'].empty ? doc['replies'].value : 0;
                                    def reposts = doc.containsKey('reposts') && !doc['reposts'].empty ? doc['reposts'].value : 0;
                                    def votes = doc.containsKey('votes') && !doc['votes'].empty ? doc['votes'].value : 0;          
                                    return likes + shares + comments + favorites + views + retweets + replies + reposts + votes;
                                """
                            }
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
    
    # Ekstrak data dari respons
    buckets = response["aggregations"]["data_per_day"]["buckets"]
    
    # Siapkan data untuk DataFrame
    topic_data = []
    for bucket in buckets:
        date = bucket["key_as_string"]
        total_mentions = bucket["doc_count"]
        total_reach = bucket["total_reach"]["value"]
        total_engagement = bucket["total_engagement"]["value"]
        
        topic_data.append({
            "date": date,
            "total_mentions": total_mentions,
            "total_reach": total_reach,
            "total_engagement": total_engagement
        })
    
    # Konversi ke DataFrame
    df_topic_data = pd.DataFrame(topic_data)
    
    # Jika tidak ada data, kembalikan DataFrame kosong
    if df_topic_data.empty:
        return pd.DataFrame(columns=["date", "presence_score"])
    
    # Hitung nilai maksimum
    max_mentions = df_topic_data["total_mentions"].max()
    max_reach = df_topic_data["total_reach"].max()
    max_engagement = df_topic_data["total_engagement"].max()
    
    # Hitung presence_score
    df_topic_data["presence_score"] = df_topic_data.apply(
        lambda row: round(
            ((row["total_mentions"] / max_mentions if max_mentions else 0) * 40) +
            ((row["total_reach"] / max_reach if max_reach else 0) * 40) +
            ((row["total_engagement"] / max_engagement if max_engagement else 0) * 20),
            2
        ),
        axis=1
    )
    
    # Pilih kolom yang diperlukan dan urutkan berdasarkan tanggal
    result_df = df_topic_data[["date", "presence_score"]].sort_values(by="date")
    
    # Pastikan date dalam format string
    result_df["date"] = result_df["date"].astype(str)
    
    return result_df

def get_metrics_and_posts(FILTER_KEYWORD, high_presence_date):
    """
    Mendapatkan aggregate dari sentiment per channel dan sampling data post
    menggunakan satu query Elasticsearch untuk efisiensi.
    
    Parameters:
    -----------
    FILTER_KEYWORD : List[str]
        Daftar keyword untuk filter
    high_presence_date : str
        Tanggal dengan presence tinggi yang akan dianalisis (YYYY-MM-DD)
        
    Returns:
    --------
    pd.DataFrame
        DataFrame gabungan yang berisi metrics dan posts
    """

    
    # Definisikan semua channel dan indeks
    default_channels = ['reddit', 'youtube', 'linkedin', 'twitter', 
                        'tiktok', 'instagram', 'facebook', 'news', 'threads']
    indices = [f"{ch}_data" for ch in default_channels]
    
    # Format tanggal untuk query
    start_datetime = f"{high_presence_date} 00:00:00"
    end_datetime = f"{high_presence_date} 23:59:59"
    
    # Build keyword filter 
    keyword_conditions = []
    for kw in FILTER_KEYWORD:
        keyword_conditions.append({"match": {"post_caption": {"query": kw, "operator": "AND"}}})
        keyword_conditions.append({"match": {"issue": {"query": kw, "operator": "AND"}}})
    
    keyword_filter = {
        "bool": {
            "should": keyword_conditions,
            "minimum_should_match": 1
        }
    }
    
    # === QUERY 1: Metrics Data ===
    # Query untuk mendapatkan aggregate dari sentiment per channel
    metrics_query = {
        "size": 0,
        "query": {
            "bool": {
                "must": [
                    {
                        "range": {
                            "post_created_at": {
                                "gte": start_datetime,
                                "lte": end_datetime
                            }
                        }
                    },
                    keyword_filter
                ]
            }
        },
        "aggs": {
            "sentiment_channel": {
                "terms": {
                    "field": "sentiment",
                    "size": 10  # Jumlah sentiment teratas
                },
                "aggs": {
                    "channels": {
                        "terms": {
                            "field": "channel",
                            "size": 20  # Jumlah channel teratas
                        }
                    }
                }
            }
        }
    }
    
    # === QUERY 2: Posts Data ===
    # Query untuk mendapatkan sampling data post
    posts_query = {
        "size": 100,  # Limit 100 post teratas
        "query": {
            "bool": {
                "must": [
                    {
                        "range": {
                            "post_created_at": {
                                "gte": start_datetime,
                                "lte": end_datetime
                            }
                        }
                    },
                    keyword_filter
                ],
                "must_not": [
                    {
                        "terms": {
                            "issue.keyword": ["not specified", "Not Specified", "NOT SPECIFIED"]
                        }
                    }
                ]
            }
        },
        "_source": [
            "post_caption", "channel", "issue", "sentiment", "reach_score", 
            "viral_score", "likes", "shares", "comments", "favorites", 
            "views", "retweets", "replies", "reposts", "votes", "link_post"
        ],
        "sort": [
            {
                "_script": {
                    "type": "number",
                    "script": {
                        "source": """
                            def reach = doc.containsKey('reach_score') && !doc['reach_score'].empty ? doc['reach_score'].value : 0;
                            def viral = doc.containsKey('viral_score') && !doc['viral_score'].empty ? doc['viral_score'].value : 0;
                            def likes = doc.containsKey('likes') && !doc['likes'].empty ? doc['likes'].value : 0;
                            def shares = doc.containsKey('shares') && !doc['shares'].empty ? doc['shares'].value : 0;
                            def comments = doc.containsKey('comments') && !doc['comments'].empty ? doc['comments'].value : 0;
                            def favorites = doc.containsKey('favorites') && !doc['favorites'].empty ? doc['favorites'].value : 0;
                            def views = doc.containsKey('views') && !doc['views'].empty ? doc['views'].value : 0;
                            def retweets = doc.containsKey('retweets') && !doc['retweets'].empty ? doc['retweets'].value : 0;
                            def replies = doc.containsKey('replies') && !doc['replies'].empty ? doc['replies'].value : 0;
                            def reposts = doc.containsKey('reposts') && !doc['reposts'].empty ? doc['reposts'].value : 0;
                            def votes = doc.containsKey('votes') && !doc['votes'].empty ? doc['votes'].value : 0;
                            
                            def engagement = likes + shares + comments + favorites + views + retweets + replies + reposts + votes;
                            
                            return reach + viral + engagement;
                        """
                    },
                    "order": "desc"
                }
            }
        ]
    }
    
    # Execute kedua query secara terpisah
    metrics_response = es.search(
        index=",".join(indices),
        body=metrics_query
    )
    
    posts_response = es.search(
        index=",".join(indices),
        body=posts_query
    )
    
    # Proses results untuk metrics_data
    metrics_data = []
    sentiment_buckets = metrics_response["aggregations"]["sentiment_channel"]["buckets"]
    
    for sentiment_bucket in sentiment_buckets:
        sentiment = sentiment_bucket["key"]
        channel_buckets = sentiment_bucket["channels"]["buckets"]
        
        for channel_bucket in channel_buckets:
            channel = channel_bucket["key"]
            total_mentions = channel_bucket["doc_count"]
            
            metrics_data.append({
                "data_type": "metrics",
                "sentiment": sentiment,
                "channel": channel,
                "total_mentions": total_mentions,
                "post_caption": None,
                "issue": None,
                "reach_score": None,
                "viral_score": None,
                "engagement": None,
                "link_post": None
            })
    
    # Proses results untuk posts_data
    posts_data = []
    post_hits = posts_response["hits"]["hits"]
    
    for hit in post_hits:
        source = hit["_source"]
        
        # Hitung total engagement
        engagement = sum([
            source.get("likes", 0) or 0,
            source.get("shares", 0) or 0,
            source.get("comments", 0) or 0,
            source.get("favorites", 0) or 0,
            source.get("views", 0) or 0,
            source.get("retweets", 0) or 0,
            source.get("replies", 0) or 0,
            source.get("reposts", 0) or 0,
            source.get("votes", 0) or 0
        ])
        
        posts_data.append({
            "data_type": "posts",
            "sentiment": source.get("sentiment", ""),
            "channel": source.get("channel", ""),
            "total_mentions": None,
            "post_caption": source.get("post_caption", ""),
            "issue": source.get("issue", ""),
            "reach_score": source.get("reach_score", 0),
            "viral_score": source.get("viral_score", 0),
            "engagement": engagement,
            "link_post": source.get("link_post", "")
        })
    
    # Gabungkan kedua hasil
    combined_data = metrics_data + posts_data
    
    # Konversi ke DataFrame
    df = pd.DataFrame(combined_data)
    
    # Urutkan hasil
    df = df.sort_values(
        by=["data_type", "reach_score", "viral_score", "engagement"],
        ascending=[True, False, False, False],
        na_position='last'
    )
    
    return df

def presence_description(TOPIC, FILTER_KEYWORD, high_presence_date,SAVE_PATH):
    
    combined_results = get_metrics_and_posts(
        FILTER_KEYWORD=FILTER_KEYWORD,
        high_presence_date=high_presence_date
    )

    # Pisahkan hasil berdasarkan data_type
    metric_presence = combined_results[combined_results['data_type'] == 'metrics']
    sample_post_presence = combined_results[combined_results['data_type'] == 'posts']

    #summarize
    prompt = f"""
    You are a media analyst assistant. Analyze a spike in presence score related to the topic "{TOPIC}" on {high_presence_date}.

    Here is the supporting data:

    1. **Sentiment Breakdown (total mentions)**  
    {metric_presence.groupby('sentiment').sum().to_dict()['total_mentions']}

    2. **Platform Breakdown (total mentions)**  
    {metric_presence.groupby('channel').sum().to_dict()['total_mentions']}

    3. **Top Posts on {high_presence_date}**  
    {sample_post_presence[['post_caption','channel']].to_dict(orient='records')}

    ---

    **Instruction:**  
    Summarize in **1 paragraph only** what likely caused the spike, which platform contributed the most, what sentiment dominated, and what topic(s) were most discussed — **only if relevant to Topic: "{TOPIC}" **. Use a professional, concise tone.
    """
    summarize = call_gemini(prompt)

    with open(os.path.join(SAVE_PATH,'presence_score_analysis.json'),'w') as f:
        json.dump({'analysis':summarize},f)
   
def generatre_presence_score(TOPIC, KEYWORDS, START_DATE, END_DATE, SAVE_PATH):
    
    presence_score = get_data(KEYWORDS, START_DATE, END_DATE)
    
    plot_donut_score(presence_score['presence_score'].mean(),
                     save_path = os.path.join(SAVE_PATH,'presence_score_donut.png'))

    plot_presence_score_trend(presence_score.to_dict(orient = 'records'),
                              save_path = os.path.join(SAVE_PATH,'presence_trend.png'))
    
    high_presence_date = presence_score.sort_values('presence_score', ascending = False)['date'].to_list()[0]
    
    presence_description(TOPIC, KEYWORDS, high_presence_date, SAVE_PATH)