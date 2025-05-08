import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from chart_generator.functions import *
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
load_dotenv()  

es = Elasticsearch(os.getenv('ES_HOST',"http://34.101.178.71:9200/"),
    basic_auth=(os.getenv("ES_USERNAME","elastic"),os.getenv('ES_PASSWORD',"elasticpassword"))  # Sesuaikan dengan kredensial Anda
        )


def generate_date_range(start_date: str, end_date: str) -> List[str]:
    """
    Menghasilkan daftar tanggal dari start_date hingga end_date.
    
    Parameters:
    -----------
    start_date : str
        Tanggal awal dalam format 'YYYY-MM-DD'
    end_date : str
        Tanggal akhir dalam format 'YYYY-MM-DD'
        
        Tanggal akhir dalam format 'YYYY-MM-DD'
    --------
    List[str]
        Daftar tanggal dari start_date hingga end_date dalam format 'YYYY-MM-DD'
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    date_range = []
    
    current = start
    while current <= end:
        date_range.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    
    return date_range

def build_keyword_filter(keywords: List[str]) -> Dict:
    """
    Membangun filter Elasticsearch untuk list keywords.
    
    Parameters:
    -----------
    keywords : List[str]
        Daftar keyword yang akan difilter
        
    Returns:
    --------
    Dict
        Filter Elasticsearch untuk keyword
    """
    keyword_should_conditions = []
    
    for kw in keywords:
        keyword_should_conditions.append({"match": {"post_caption": {"query": kw, "operator": "AND"}}})
        keyword_should_conditions.append({"match": {"issue": {"query": kw, "operator": "AND"}}})
    
    return {
        "bool": {
            "should": keyword_should_conditions,
            "minimum_should_match": 1
        }
    }

def generate_mentions_chart(title,data, current_mentions, previous_mentions, mentions_percent_change, SAVE_PATH = 'PPT'):
    # Extract date and values
    dates = [datetime.strptime(d['date'], '%Y-%m-%d') for d in data]
    values = [d['value'] for d in data]

    # Convert datetime to numeric for interpolation
    x = np.arange(len(dates))
    y = np.array(values)

    # Smoothing using B-spline with adaptive degree
    x_smooth = np.linspace(x.min(), x.max(), 300)
    
    # Choose spline degree based on number of points
    if len(x) >= 4:
        k = 3  # cubic spline
    elif len(x) == 3:
        k = 2  # quadratic spline
    elif len(x) == 2:
        k = 1  # linear interpolation
    else:
        # If only one point, create a simple point plot
        fig, ax = plt.subplots(figsize=(5, 5), dpi=100)
        ax.plot([dates[0]], [values[0]], marker='o', color=color)
        
        # Clean styling
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.tick_params(left=False, bottom=False)
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Text info
        ax.text(0.03, -0.2, title, transform=ax.transAxes,
                fontsize=26, color='#5f6368')
        ax.text(0.03, -0.39, f"{current_mentions:,}", transform=ax.transAxes,
                fontsize=25, color='#202124', weight='bold')
        ax.text(0.03, -0.55, f"{delta_sign}{delta:,} ({delta_sign}{round(mentions_percent_change)}%)",
                transform=ax.transAxes, fontsize=18, color=delta_color, weight='bold')
        
        plt.tight_layout()
        plt.savefig(save_file, bbox_inches='tight', dpi=50, transparent=True)
        return
    
    spline = make_interp_spline(x, y, k=k)
    y_smooth = spline(x_smooth)

    # Convert x_smooth back to datetime scale
    date_smooth = np.interp(x_smooth, x, [d.timestamp() for d in dates])
    date_smooth = [datetime.fromtimestamp(ts) for ts in date_smooth]

    # Figure setup
    fig, ax = plt.subplots(figsize=(5, 5), dpi=100)

    # Plot the smooth line
    color='#1a73e8'
    color_fill = '#b9cdeb'
    if title =='Positive':
        color = 'green'
        color_fill = '#cbf5d4'
    elif title == 'Negative':
        color='red'
        color_fill = '#f5cccb'

    ax.plot(date_smooth, y_smooth, color=color, linewidth=2, zorder=2)

    # Gradient fill
    ax.fill_between(date_smooth, y_smooth, [min(y)]*len(y_smooth),
                    color=color_fill, alpha=0.1, zorder=1)

    # Clean styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.tick_params(left=False, bottom=False)
    ax.set_xticks([])
    ax.set_yticks([])

    # Delta calculation
    delta = current_mentions - previous_mentions
    is_positive = delta >= 0
    delta_color = 'green' if is_positive else 'red'
    delta_sign = '+' if is_positive else ''

    # Text info
    ax.text(0.03, -0.2, title, transform=ax.transAxes,
            fontsize=26, color='#5f6368')
    ax.text(0.03, -0.39, f"{current_mentions:,}", transform=ax.transAxes,
            fontsize=25, color='#202124', weight = 'bold')
    ax.text(0.03, -0.55, f"{delta_sign}{delta:,} ({delta_sign}{round(mentions_percent_change)}%)",
            transform=ax.transAxes, fontsize=18, color=delta_color, weight = 'bold')

    plt.tight_layout()
    
    save_file = os.path.join(SAVE_PATH, f"{title.lower().replace(' ', '_')}.png")
    
    plt.savefig(save_file, bbox_inches='tight', dpi=75, transparent=True)

def plot_current_vs_previous_period(data, title="Current vs Previous Period", save_path=None, show_dots=True):
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    
    
    color_theme = '#1a73e8'
    
    if 'negative' in title.lower():
        color_theme = 'red'
    if 'positive' in title.lower():
        color_theme = 'green'

    # Pivot table
    pivot_df = df.pivot_table(index='date', columns='period', values='value', aggfunc='sum').sort_index().fillna(0)

    # Raw data
    x_current = pivot_df.index
    y_current = pivot_df['current'].values
    x_previous = pivot_df.index
    y_previous = pivot_df['previous'].values

    # Smoothing only for plotting
    def smooth(x, y):
        if len(x) < 2:  # If only one point, return as is
            return x, y
            
        x_numeric = np.arange(len(x))
        xnew = np.linspace(x_numeric.min(), x_numeric.max(), 300)
        
        # Choose spline degree based on number of points
        if len(x) >= 4:
            k = 3  # cubic spline
        elif len(x) == 3:
            k = 2  # quadratic spline
        else:
            k = 1  # linear interpolation
            
        spl = make_interp_spline(x_numeric, y, k=k)
        ynew = spl(xnew)
        x_interp = np.interp(xnew, x_numeric, x.astype(np.int64) // 10**9)
        x_interp = pd.to_datetime(x_interp, unit='s')
        return x_interp, ynew

    x_smooth_current, y_smooth_current = smooth(x_current, y_current)
    x_smooth_previous, y_smooth_previous = smooth(x_previous, y_previous)

    fig, ax = plt.subplots(figsize=(13.13, 3.60))  # 33.35cm x 9.14cm

    # Chart styling
    ax.set_facecolor('#fcfdff')
    fig.patch.set_facecolor('#ffffff')

    # Plot smooth lines
    ax.plot(x_smooth_current, y_smooth_current, color=color_theme, label='Current period', linewidth=2)
    ax.plot(x_smooth_previous, y_smooth_previous, color=color_theme, linestyle='--', label='Previous period', alpha=0.6, linewidth=1.5)

    # Plot dots for real data points (optional)
    if show_dots:
        ax.scatter(x_current, y_current, color=color_theme, s=15, zorder=3)
        ax.scatter(x_previous, y_previous, color=color_theme, s=15, alpha=0.5, zorder=3)
        
    # Remove box frame
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Axis styling
    ax.tick_params(axis='y', colors=color_theme)
    ax.yaxis.label.set_color(color_theme)
    ax.grid(axis='y', linestyle='-', linewidth=0.5, alpha=0.3)

    ax.xaxis.set_major_formatter(DateFormatter('%d %b'))
    plt.xticks(rotation=0)
    ax.xaxis.label.set_color('#5f6368')

    # Annotate peaks from raw values
    def annotate_peak(x_vals, y_vals, kind='current'):
        idx = np.argmax(y_vals)
        peak_x = x_vals[idx]
        peak_y = y_vals[idx]
        if kind == 'previous':
            label = f"{int(round(peak_y))} mentions on {(peak_x - timedelta(days=len(pivot_df))).strftime('%d %b %Y')}"
        else:
            label = f"{int(round(peak_y))} mentions on {peak_x.strftime('%d %b %Y')}"
        ax.annotate(label, xy=(peak_x, peak_y), xytext=(peak_x, peak_y + 2),
                    ha='center', fontsize=9, color=color_theme,
                    arrowprops=dict(arrowstyle='-', color=color_theme, lw=1))

    annotate_peak(x_current, y_current)
    annotate_peak(x_previous, y_previous, kind='previous')

    # Legend below chart
    ax.legend(
        loc='upper center',
        bbox_to_anchor=(0.1, -0.3),
        ncol=2,
        frameon=False
    )

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=75, transparent=True)
       
def get_time_series(FILTER_KEYWORD, START_DATE, END_DATE, prev_start_date=None, prev_end_date=None):
    """
    Mengambil data time series dari Elasticsearch dengan parameter yang sama 
    seperti fungsi SQL original, tetapi menggunakan pendekatan aggregasi.
    
    Parameters:
    -----------
    FILTER_KEYWORD : List[str]
        Daftar keyword untuk filter
    START_DATE : str
        Tanggal awal periode saat ini (YYYY-MM-DD)
    END_DATE : str
        Tanggal akhir periode saat ini (YYYY-MM-DD)
    prev_start_date : str, optional
        Tanggal awal periode sebelumnya (YYYY-MM-DD)
    prev_end_date : str, optional
        Tanggal akhir periode sebelumnya (YYYY-MM-DD)
        
    Returns:
    --------
    Dict
        Dictionary dengan struktur yang sama dengan output SQL:
        {
            "mentions_time_series": [...],
            "social_reach_time_series": [...],
            "non_social_reach_time_series": [...],
            "positive_time_series": [...],
            "negative_time_series": [...]
        }
    """
    # Buat koneksi Elasticsearch
    # Sesuaikan dengan detail koneksi Anda

    
    # Definisikan semua channel dan indeks
    default_channels = ['reddit', 'youtube', 'linkedin', 'twitter', 
                        'tiktok', 'instagram', 'facebook', 'news', 'threads']
    indices = [f"{ch}_data" for ch in default_channels]
    
    # Hitung tanggal untuk periode sebelumnya jika tidak disediakan
    diff_date = range_date_count(START_DATE, END_DATE)
    if prev_start_date is None:
        prev_start_date = kurangi_tanggal(START_DATE, diff_date + 1)
    if prev_end_date is None:
        prev_end_date = kurangi_tanggal(END_DATE, diff_date + 1)
    
    # Siapkan struktur output
    result = {
        "mentions_time_series": [],
        "social_reach_time_series": [],
        "non_social_reach_time_series": [],
        "positive_time_series": [],
        "negative_time_series": []
    }
    
    # Build keyword filter
    keyword_filter = build_keyword_filter(FILTER_KEYWORD)
    
    # === PROSES PERIODE SAAT INI DENGAN AGGREGASI ===
    # 1. Membuat query dengan date_histogram aggregation
    current_aggs_query = {
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
            "mentions_per_day": {
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
                    "social_reach": {
                        "filter": {
                            "bool": {
                                "must_not": [
                                    {
                                        "term": {
                                            "channel": "news"
                                        }
                                    }
                                ]
                            }
                        },
                        "aggs": {
                            "total": {
                                "sum": {
                                    "field": "reach_score"
                                }
                            }
                        }
                    },
                    "non_social_reach": {
                        "filter": {
                            "term": {
                                "channel": "news"
                            }
                        },
                        "aggs": {
                            "total": {
                                "sum": {
                                    "field": "reach_score"
                                }
                            }
                        }
                    },
                    "positive_sentiment": {
                        "filter": {
                            "term": {
                                "sentiment": "positive"
                            }
                        }
                    },
                    "negative_sentiment": {
                        "filter": {
                            "term": {
                                "sentiment": "negative"
                            }
                        }
                    }
                }
            }
        }
    }
    
    # Execute query untuk periode saat ini
    current_response = es.search(
        index=",".join(indices),
        body=current_aggs_query
    )
    
    # Proses hasil untuk periode saat ini
    current_buckets = current_response["aggregations"]["mentions_per_day"]["buckets"]
    
    for bucket in current_buckets:
        date = bucket["key_as_string"]
        
        # Mentions time series
        result["mentions_time_series"].append({
            "date": date,
            "value": bucket["doc_count"],
            "period": "current"
        })
        
        # Social reach time series
        result["social_reach_time_series"].append({
            "date": date,
            "value": bucket["social_reach"]["total"]["value"] if "total" in bucket["social_reach"] else 0,
            "period": "current"
        })
        
        # Non-social reach time series
        result["non_social_reach_time_series"].append({
            "date": date,
            "value": bucket["non_social_reach"]["total"]["value"] if "total" in bucket["non_social_reach"] else 0,
            "period": "current"
        })
        
        # Positive sentiment time series
        result["positive_time_series"].append({
            "date": date,
            "value": bucket["positive_sentiment"]["doc_count"],
            "period": "current"
        })
        
        # Negative sentiment time series
        result["negative_time_series"].append({
            "date": date,
            "value": bucket["negative_sentiment"]["doc_count"],
            "period": "current"
        })
    
    # === PROSES PERIODE SEBELUMNYA DENGAN AGGREGASI ===
    # 1. Membuat query dengan date_histogram aggregation
    previous_aggs_query = {
        "size": 0,
        "query": {
            "bool": {
                "must": [
                    {
                        "range": {
                            "post_created_at": {
                                "gte": prev_start_date,
                                "lte": prev_end_date
                            }
                        }
                    },
                    keyword_filter
                ]
            }
        },
        "aggs": {
            "mentions_per_day": {
                "date_histogram": {
                    "field": "post_created_at",
                    "calendar_interval": "day",
                    "format": "yyyy-MM-dd",
                    "min_doc_count": 0,
                    "extended_bounds": {
                        "min": prev_start_date,
                        "max": prev_end_date
                    }
                },
                "aggs": {
                    "social_reach": {
                        "filter": {
                            "bool": {
                                "must_not": [
                                    {
                                        "term": {
                                            "channel": "news"
                                        }
                                    }
                                ]
                            }
                        },
                        "aggs": {
                            "total": {
                                "sum": {
                                    "field": "reach_score"
                                }
                            }
                        }
                    },
                    "non_social_reach": {
                        "filter": {
                            "term": {
                                "channel": "news"
                            }
                        },
                        "aggs": {
                            "total": {
                                "sum": {
                                    "field": "reach_score"
                                }
                            }
                        }
                    },
                    "positive_sentiment": {
                        "filter": {
                            "term": {
                                "sentiment": "positive"
                            }
                        }
                    },
                    "negative_sentiment": {
                        "filter": {
                            "term": {
                                "sentiment": "negative"
                            }
                        }
                    }
                }
            }
        }
    }
    
    # Execute query untuk periode sebelumnya
    previous_response = es.search(
        index=",".join(indices),
        body=previous_aggs_query
    )
    
    # Proses hasil untuk periode sebelumnya
    previous_buckets = previous_response["aggregations"]["mentions_per_day"]["buckets"]
    
    # Dapatkan list tanggal periode saat ini untuk "menggeser" tanggal periode sebelumnya
    current_dates = [bucket["key_as_string"] for bucket in current_buckets]
    
    # Proses hanya jika ada data di kedua periode yang sebanding
    if len(previous_buckets) > 0 and len(current_dates) > 0:
        # Terbatas pada jumlah hari yang sama dengan periode saat ini
        max_days = min(len(previous_buckets), len(current_dates))
        
        for i in range(max_days):
            previous_bucket = previous_buckets[i]
            display_date = current_dates[i] if i < len(current_dates) else None
            
            if display_date is None:
                continue
            
            # Mentions time series
            result["mentions_time_series"].append({
                "date": display_date,
                "value": previous_bucket["doc_count"],
                "period": "previous"
            })
            
            # Social reach time series
            result["social_reach_time_series"].append({
                "date": display_date,
                "value": previous_bucket["social_reach"]["total"]["value"] if "total" in previous_bucket["social_reach"] else 0,
                "period": "previous"
            })
            
            # Non-social reach time series
            result["non_social_reach_time_series"].append({
                "date": display_date,
                "value": previous_bucket["non_social_reach"]["total"]["value"] if "total" in previous_bucket["non_social_reach"] else 0,
                "period": "previous"
            })
            
            # Positive sentiment time series
            result["positive_time_series"].append({
                "date": display_date,
                "value": previous_bucket["positive_sentiment"]["doc_count"],
                "period": "previous"
            })
            
            # Negative sentiment time series
            result["negative_time_series"].append({
                "date": display_date,
                "value": previous_bucket["negative_sentiment"]["doc_count"],
                "period": "previous"
            })
    
    return result

def generate_metrics_chart(KEYWORDS, START_DATE, 
                           END_DATE, prev_start_date, prev_end_date, SAVE_PATH = 'PPT'):
    
    metrics_chart_config = {
        'mentions': ('Volume of mentions','mentions_time_series', 'current_mentions', 'previous_mentions', 'mentions_percent_change'),
        'social_reach': ('Social media reach','social_reach_time_series', 'current_social_reach', 'previous_social_reach', 'social_reach_percent_change'),
        'non_social_reach': ('Non social media reach','non_social_reach_time_series', 'current_non_social_reach', 'previous_non_social_reach', 'non_social_reach_percent_change'),
        'positive': ('Positive','positive_time_series', 'current_positive', 'previous_positive', 'positive_percent_change'),
        'negative': ('Negative','negative_time_series', 'current_negative', 'previous_negative', 'negative_percent_change'),
    }

    # Mendapatkan data time series
    time_series_data = get_time_series(
        FILTER_KEYWORD=KEYWORDS,
        START_DATE=START_DATE,
        END_DATE=END_DATE,
        prev_start_date=prev_start_date,
        prev_end_date=prev_end_date
    )
    
    for metric, (title,ts_col, current_key, prev_key, change_key) in metrics_chart_config.items():

        time_series = time_series_data[ts_col]
        time_series = pd.DataFrame(time_series)

        values = time_series[time_series['period']=='current']
        current_val = values['value'].sum()
        previous_val = time_series[time_series['period']=='previous']['value'].sum()

        if previous_val != 0:
            percent_change = ((current_val - previous_val) / previous_val) * 100
        else:
            percent_change = 0

        # Ubah NaN menjadi 0 jika masih ada kemungkinan NaN
        if pd.isna(percent_change):
            percent_change = 0

        generate_mentions_chart(title,
                                values[['date','value']].sort_values('date').to_dict(orient = 'records'),
                                current_mentions = int(current_val),
                                previous_mentions = int(previous_val),
                                mentions_percent_change = percent_change,
                               SAVE_PATH = SAVE_PATH)

        save_file = os.path.join(SAVE_PATH,f"{title}_trend.png")
        plot_current_vs_previous_period(time_series, title=f"{title} Trend", save_path=save_file)
