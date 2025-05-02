import json, os
import pandas as pd
from datetime import datetime
from typing import Dict, List, Literal, Optional, Union
    
from chart_generator.functions import *
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
load_dotenv()  

es = Elasticsearch(os.getenv('ES_HOST',"http://34.101.178.71:9200/"),
    basic_auth=(os.getenv("ES_USERNAME","elastic"),os.getenv('ES_PASSWORD',"elasticpassword"))  # Sesuaikan dengan kredensial Anda
        )


def get_context_data(
    keywords: List[str],
    start_date: str,
    end_date: str,
    limit=50,
    kind="word" #word or hashtags
) -> pd.DataFrame:
    # Buat koneksi Elasticsearch
    if kind == 'word':
        field = 'list_word'
    else:
        field = 'post_hashtags'
        
    
    if not es:
        return pd.DataFrame(columns=["word", "total_mentions", "dominant_sentiment", "dominant_sentiment_count", "dominant_sentiment_percentage"])
    
    # Definisikan semua channel yang mungkin
    default_channels = ['reddit', 'youtube', 'linkedin', 'twitter', 
                        'tiktok', 'instagram', 'facebook', 'news', 'threads']
    
    # Dapatkan indeks yang akan di-query
    indices = [f"{ch}_data" for ch in default_channels]
    
    if not indices:
        print("Error: No valid indices")
        return pd.DataFrame(columns=["word", "total_mentions", "dominant_sentiment", "dominant_sentiment_count", "dominant_sentiment_percentage"])
    
    # Bangun query untuk mendapatkan trending hashtags
    must_conditions = [
        {
            "range": {
                "post_created_at": {
                    "gte": start_date,
                    "lte": end_date
                }
            }
        },
        {
            "exists": {
                "field": field
            }
        }
    ]
    
    # Tambahkan filter keywords jika ada
    if keywords:
        # Konversi keywords ke list jika belum
        keyword_list = keywords if isinstance(keywords, list) else [keywords]
        keyword_should_conditions = []
        
        # Tentukan field yang akan digunakan (tidak case sensitive)
        caption_field = "post_caption"
        issue_field = "issue"
        
        # Gunakan match dengan operator OR untuk mencari salah satu keyword
        for kw in keyword_list:
            keyword_should_conditions.append({"match": {caption_field: {"query": kw, "operator": "AND"}}})
            keyword_should_conditions.append({"match": {issue_field: {"query": kw, "operator": "AND"}}})
        
        keyword_condition = {
            "bool": {
                "should": keyword_should_conditions,
                "minimum_should_match": 1
            }
        }
        must_conditions.append(keyword_condition)
    
    # Query untuk mendapatkan wordcloud data
    query = {
        "size": 0,
        "query": {
            "bool": {
                "must": must_conditions
            }
        },
        "aggs": {
            "words": {
                "terms": {
                    "field": field,
                    "size": limit
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
    
    try:
        # Execute query
        response = es.search(
            index=",".join(indices),
            body=query
        )
        
        # Process results
        word_buckets = response["aggregations"]["words"]["buckets"]
        
        # Kumpulkan data word
        word_data = []
        
        for word_bucket in word_buckets:
            word = word_bucket["key"]
            mentions = word_bucket["doc_count"]
            
            # Analisis sentimen untuk word
            sentiment_buckets = word_bucket["sentiment_breakdown"]["buckets"]
            
            # Initialize sentiment counts
            sentiment_counts = {
                "positive": 0,
                "negative": 0,
                "neutral": 0
            }
            
            # Count by sentiment
            for sentiment_bucket in sentiment_buckets:
                sentiment = sentiment_bucket["key"].lower()
                count = sentiment_bucket["doc_count"]
                if sentiment in sentiment_counts:
                    sentiment_counts[sentiment] = count
            
            # Determine dominant sentiment
            dominant_sentiment = max(sentiment_counts, key=sentiment_counts.get)
            dominant_sentiment_count = sentiment_counts[dominant_sentiment]
            
            # Calculate percentage for dominant sentiment
            dominant_sentiment_percentage = (dominant_sentiment_count / mentions) * 100 if mentions > 0 else 0
            
            word_data.append({
                kind: word,
                "total_mentions": mentions,
                "dominant_sentiment": dominant_sentiment,
                "dominant_sentiment_count": dominant_sentiment_count,
                "dominant_sentiment_percentage": round(dominant_sentiment_percentage, 1)
            })
        
        # Reorder based on sort_by parameter if needed
        word_data.sort(key=lambda x: x["total_mentions"], reverse=True)
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(word_data)
        return df
        
    except Exception as e:
        print(f"Query failed: {e}")
        return pd.DataFrame(columns=["word", "total_mentions", "dominant_sentiment", "dominant_sentiment_count", "dominant_sentiment_percentage"])

def create_sentiment_wordcloud(data, width=600, height=350, background_color='white', 
                              max_words=100, figsize=(8, 5), title="Hashtag Word Cloud by Sentiment", word='hashtag'):

    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Create a frequency dictionary for the word cloud
    freq_dict = {row[word]: row['total_mentions'] for _, row in df.iterrows()}
    
    # Create a color function based on sentiment
    sentiment_color_map = {
        'positive': '#2ca02c',  # Darker Green
        'negative': '#e63939',  # Bright Red
        'neutral': '#7f7f7f'    # Blue
    }
    

    # Create a mapping of words to their sentiment colors
    word_to_color = {row[word]: sentiment_color_map[row['dominant_sentiment']] 
                    for _, row in df.iterrows()}
    
    # Define color function
    def color_func(word, **kwargs):
        return word_to_color.get(word, '#000000')  # Default to black if word not found
    
    # Create a mask to make the word cloud more compact (oval shape)
    x, y = np.ogrid[:height, :width]
    mask = (x - height/2) ** 2 / (height/2) ** 2 + (y - width/2) ** 2 / (width/2) ** 2 > 1
    mask = 255 * mask.astype(int)
    
    # Configure WordCloud with improved parameters
    wc = WordCloud(
        max_words=max_words,
        width=width,
        height=height,
        background_color=background_color,
        prefer_horizontal=1.0,  # Force horizontal text only
        relative_scaling=0.5,  # Higher value gives more weight to frequency
        collocations=False,
        color_func=color_func,
        min_font_size=10,
        max_font_size=80,
        font_step=1,
        random_state=42
    ).generate_from_frequencies(freq_dict)
    
    # Create figure and display the word cloud
    fig, ax = plt.subplots(figsize=figsize)
    ax.imshow(wc, interpolation='bilinear')
    ax.set_axis_off()
    
    plt.tight_layout(pad=0)
    return fig, ax

def context( KEYWORDS, START_DATE, END_DATE, SAVE_PATH ):

    word = get_context_data(
                keywords=KEYWORDS,
                start_date=START_DATE,
                end_date=END_DATE,
                limit=200,
                kind = 'word'
            )


    list_stopword = []
    if os.path.isfile('utils/stopwords.txt'):
         with open('utils/stopwords.txt') as f:
              list_stopword = f.read().split()
    else:
         print('TIDAK ADA FILE STOPSOWRDS')
         print(os.getcwd())

    word = word[~word['word'].isin(list_stopword)][:50]

    fig, ax = create_sentiment_wordcloud(word.to_dict(orient = 'records'), word = 'word')
    save_file = os.path.join(SAVE_PATH, 'word_sentiment_wordcloud.png')
    plt.savefig(save_file, dpi=500, bbox_inches='tight', transparent=True)


def hashtags( KEYWORDS, START_DATE, END_DATE, SAVE_PATH ):

    hashtags = get_context_data(
                keywords=KEYWORDS,
                start_date=START_DATE,
                end_date=END_DATE,
                limit=50,
                kind = 'hashtag'
            )

    fig, ax = create_sentiment_wordcloud(hashtags.to_dict(orient = 'records'), word = 'hashtag')
    save_file = os.path.join(SAVE_PATH,'hashtag_sentiment_wordcloud.png')
    plt.savefig(save_file, dpi=500, bbox_inches='tight', transparent=True)

    
def generate_context( KEYWORDS, START_DATE, END_DATE, SAVE_PATH):
    import time
    start_time = time.time()
    print('word')
    context(KEYWORDS, START_DATE, END_DATE, SAVE_PATH)
    end_time = time.time()
    elapsed = end_time - start_time
    print('finish',elapsed)
    start_time = time.time()
    print('hashtags')
    hashtags(KEYWORDS, START_DATE, END_DATE, SAVE_PATH)
    end_time = time.time()
    elapsed = end_time - start_time
    print('finish',elapsed)