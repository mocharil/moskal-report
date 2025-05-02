import json
from typing import Dict, List, Optional, Union
import re, os

from dotenv import load_dotenv
from elasticsearch import Elasticsearch
load_dotenv()  

es = Elasticsearch(os.getenv('ES_HOST',"http://34.101.178.71:9200/"),
    basic_auth=(os.getenv("ES_USERNAME","elastic"),os.getenv('ES_PASSWORD',"elasticpassword"))  # Sesuaikan dengan kredensial Anda
        )



def get_filtered_mentions(
    keywords: List[str],
    start_date: str,
    end_date: str,
    source: List[str] = None,
    sort_type: str = 'popular',
    channels=None,
    page=1,
    page_size=10,
    search_exact_phrases=False,
    case_sensitive=False
) -> Dict:

    default_channels = ['reddit', 'youtube', 'linkedin', 'twitter', 
                       'tiktok', 'instagram', 'facebook', 'news', 'threads']
    indices = [f"{ch}_data" for ch in default_channels]
    
    if not indices:
        print("Error: Tidak ada indeks yang valid")
        return {
            'data': [], 
            'pagination': {
                'page': page, 
                'page_size': page_size, 
                'total_pages': 0, 
                'total_posts': 0
            }
        }
    
    # Konversi sort_type ke field sort yang sesuai
    sort_field = "viral_score"  # Default untuk 'popular'
    sort_order = "desc"
    
    # Bangun query dasar
    query = {
        "size": page_size,
        "from": (page - 1) * page_size,
        "query": {
            "bool": {
                "must": [
                    {
                        "range": {
                            "post_created_at": {
                                "gte": start_date,
                                "lte": end_date
                            }
                        }
                    }
                ],
                "filter": []
            }
        },
        "sort": [
            {sort_field: {"order": sort_order}}
        ]
    }
    
    # Tambahkan filter untuk viral_score dan sentiment
    filter_exists = {
        "bool": {
            "must": [
                {
                    "exists": {
                        "field": "viral_score"
                    }
                },
                {
                    "exists": {
                        "field": "sentiment"
                    }
                }
            ]
        }
    }
    query["query"]["bool"]["filter"].append(filter_exists)
    
    # Tambahkan filter keywords
    if keywords:
        # Konversi keywords ke list jika belum
        keyword_list = keywords if isinstance(keywords, list) else [keywords]
        keyword_should_conditions = []
        
        # Tentukan field yang akan digunakan berdasarkan case_sensitive
        caption_field = "post_caption.keyword" if case_sensitive else "post_caption"
        issue_field = "issue.keyword" if case_sensitive else "issue"
        
        if search_exact_phrases:
            # Gunakan match_phrase untuk exact matching
            for kw in keyword_list:
                keyword_should_conditions.append({"match_phrase": {caption_field: kw}})
                keyword_should_conditions.append({"match_phrase": {issue_field: kw}})
        else:
            # Gunakan match dengan operator AND
            for kw in keyword_list:
                keyword_should_conditions.append({"match": {caption_field: {"query": kw, "operator": "AND"}}})
                keyword_should_conditions.append({"match": {issue_field: {"query": kw, "operator": "AND"}}})
        
        keyword_condition = {
            "bool": {
                "should": keyword_should_conditions,
                "minimum_should_match": 1
            }
        }
        query["query"]["bool"]["must"].append(keyword_condition)
    
    # Tambahkan source parameter ke query jika disediakan
    if source is not None:
        query["_source"] = source
    
    # Jalankan query
    try:
        response = es.search(
            index=",".join(indices),
            body=query
        )
        
        # Dapatkan mentions
        mentions = [hit["_source"] for hit in response["hits"]["hits"]]

        # Tambahkan username dan user_image_url untuk channel news jika tidak ada
        for mention in mentions:
            if mention.get('channel') == 'news':
                if 'username' not in mention:
                    try:
                        username = re.findall(r'https?://(.*?)(?:/|$)', mention['link_post'])[0].replace('www.', '')
                        mention.update({'username': username})
                    except (IndexError, KeyError):
                        mention.update({'username': 'unknown'})

                if 'user_image_url' not in mention:
                    mention.update({"user_image_url": f"https://logo.clearbit.com/{mention.get('username', 'unknown')}"})
        
        # Dapatkan total mentions
        total_mentions = response["hits"]["total"]["value"]
        
        # Hitung total halaman
        total_pages = (total_mentions + page_size - 1) // page_size  # Ceiling division
        
        # Siapkan informasi pagination
        pagination = {
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'total_posts': total_mentions
        }
        
        return {
            'data': mentions,
            'pagination': pagination
        }
        
    except Exception as e:
        print(f"Error querying Elasticsearch: {e}")
        return {
            'data': [], 
            'pagination': {
                'page': page, 
                'page_size': page_size, 
                'total_pages': 0, 
                'total_posts': 0
            }
        }
