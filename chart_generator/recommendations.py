from chart_generator.functions import *
import concurrent.futures
import json
import os
import re
import pandas as pd
import numpy as np
import time

from dotenv import load_dotenv

load_dotenv()  
BQ = About_BQ(project_id= os.getenv("BQ_PROJECT_ID") ,
         credentials_loc= os.getenv("BQ_CREDS_LOCATION")  )
         
def get_top_platforms(ALL_FILTER, platforms=None, top_n=5):
    """
    Mengidentifikasi top N platform berdasarkan jumlah post dan engagement
    """
    if platforms is None:
        platforms = ['tiktok', 'instagram', 'twitter', 'news', 'reddit', 'linkedin', 'youtube']
    
    # Query untuk mendapatkan jumlah post dan engagement per platform
    query = f"""
    SELECT 
        a.channel,
        COUNT(*) as post_count
        
    FROM medsos.post_analysis a
    WHERE {ALL_FILTER}
    AND a.channel IN ({', '.join([f"'{p}'" for p in platforms])})
    GROUP BY 1
    ORDER BY post_count DESC
    LIMIT {top_n}
    """
    
    platform_stats = BQ.to_pull_data(query)
    
    if platform_stats.empty:
        return platforms[:top_n]  # Default to first top_n platforms if no data
    
    top_platforms = platform_stats['channel'].tolist()
    print(f"Top {top_n} platforms: {top_platforms}")
    return top_platforms

def get_social_data(ALL_FILTER, max_posts=50, platforms=None):
    """
    Mengambil data dari platform yang ditentukan dalam satu query
    """
    start_time = time.time()
    
    if platforms is None or len(platforms) == 0:
        platforms = ['tiktok', 'instagram', 'twitter','news']
    
    # Query untuk platform yang dipilih sekaligus
    query = f"""
    WITH DATA AS (
      SELECT 
        a.post_caption, 
        a.channel, 
        a.likes, 
        a.comments,
        a.shares,
        a.favorites,
        a.views,
        a.retweets,
        a.replies,
        a.votes,
        a.reposts,
        c.sentiment, 
        c.intent, 
        c.emotions, 
        c.region, 
        u.category,
        COALESCE(a.viral_score, 0) * 0.2 + 
        COALESCE(a.reach_score, 0) * 0.2 + 
        COALESCE(a.influence_score, 0) * 0.2 +
        CASE
          WHEN a.channel = 'youtube' THEN 
            COALESCE(a.likes, 0)*0.4 + COALESCE(a.views, 0)*0.3 + COALESCE(a.comments, 0)*0.3
          WHEN a.channel = 'twitter' THEN 
            COALESCE(a.likes, 0)*0.3 + COALESCE(a.views, 0)*0.2 + COALESCE(a.shares, 0)*0.3 + COALESCE(a.favorites, 0)*0.2
          WHEN a.channel = 'tiktok' THEN 
            COALESCE(a.likes, 0)*0.3 + COALESCE(a.views, 0)*0.3 + COALESCE(a.comments, 0)*0.2 + COALESCE(a.shares, 0)*0.2
          WHEN a.channel = 'instagram' THEN 
            COALESCE(a.likes, 0)*0.4 + COALESCE(a.views, 0)*0.3 + COALESCE(a.comments, 0)*0.3
          WHEN a.channel = 'linkedin' THEN 
            COALESCE(a.likes, 0)*0.4 + COALESCE(a.views, 0)*0.2 + COALESCE(a.comments, 0)*0.2 + COALESCE(a.shares, 0)*0.2
          WHEN a.channel = 'reddit' THEN 
            COALESCE(a.votes, 0)*0.7 + COALESCE(a.comments, 0)*0.3
          ELSE
            COALESCE(a.likes, 0)*0.25 + COALESCE(a.views, 0)*0.15 + 
            COALESCE(a.comments, 0)*0.15 + COALESCE(a.shares, 0)*0.15 + 
            COALESCE(a.reposts, 0)*0.1 + COALESCE(a.replies, 0)*0.1 + 
            COALESCE(a.votes, 0)*0.05 + COALESCE(a.favorites, 0)*0.05
        END AS enhanced_raw_score

      FROM medsos.post_analysis a
      JOIN medsos.post_category c ON a.link_post = c.link_post
      LEFT JOIN medsos.user_category u ON u.username = a.username AND u.channel = a.channel
      WHERE {ALL_FILTER}
      AND a.channel IN ({', '.join([f"'{p}'" for p in platforms])})
    ),
    RANKED_DATA AS (
      SELECT *,
        ROW_NUMBER() OVER (PARTITION BY channel ORDER BY enhanced_raw_score DESC) as rank
      FROM DATA
    )
    
    SELECT * EXCEPT(enhanced_raw_score, rank)
    FROM RANKED_DATA
    WHERE rank <= {max_posts}
    ORDER BY channel, rank
    """
    
    data = BQ.to_pull_data(query)
    
    # Membersihkan data dan mengelompokkan berdasarkan platform
    platform_data = {}
    for platform in platforms:
        platform_rows = data[data['channel'] == platform]
        
        clean_rows = []
        for _, row in platform_rows.iterrows():
            row_dict = row.to_dict()
            # Filter dictionary dan simpan hanya nilai yang valid
            clean_dict = {k: v for k, v in row_dict.items() if pd.notna(v) and v not in ('<NA>', 'Not Specified', None)}
            if clean_dict:
                clean_rows.append(clean_dict)
        
        platform_data[platform] = clean_rows
    
    print(f"Data retrieval completed in {time.time() - start_time:.2f} seconds")
    return platform_data

def analyze_platform_parallel(platform_data, TOPIC, START_DATE, END_DATE):
    """
    Menganalisis data platform secara paralel untuk meningkatkan kecepatan
    """
    start_time = time.time()
    
    def analyze_single_platform(platform, data):
        if not data:
            return {'channel': platform, 'summarize': "No data available for analysis."}
        
        prompt = f"""
        I'm analyzing social media conversation data about [{TOPIC}] from [{START_DATE}] to [{END_DATE}].

        My data includes posts from {platform} with engagement metrics, sentiment analysis, 
        detected intent, emotions, regional distribution, and user categories.

        Based on the following sample data (up to 50 posts), create a concise 2-paragraph 
        summary of hot issues, sentiment trends, user intent, and key insights:

        {data[:min(50, len(data))]}
        """
        
        # Implementasi retry untuk call_gemini
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                summarize = call_gemini(prompt)
                return {'channel': platform, 'summarize': summarize}
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    return {'channel': platform, 'summarize': f"Error in analysis: {str(e)}"}
                time.sleep(2 ** retry_count)  # Exponential backoff
    
    # Gunakan ThreadPoolExecutor untuk paralelisme
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_to_platform = {
            executor.submit(analyze_single_platform, platform, data): platform
            for platform, data in platform_data.items() if data
        }
        
        for future in concurrent.futures.as_completed(future_to_platform):
            platform = future_to_platform[future]
            try:
                result = future.result()
                results.append(result)
                print(f"Completed analysis for {platform}")
            except Exception as e:
                print(f"Error analyzing {platform}: {e}")
                results.append({'channel': platform, 'summarize': f"Error in analysis: {str(e)}"})
    
    print(f"Platform analysis completed in {time.time() - start_time:.2f} seconds")
    return results

def generate_recommendations(TOPIC, START_DATE, END_DATE, ALL_FILTER, SAVE_PATH, top_n=4):
    """
    Fungsi utama yang dioptimasi untuk menghasilkan rekomendasi hanya dari top N platform
    """
    overall_start = time.time()
    
    # Step 1: Identifikasi top N platform berdasarkan aktivitas dan engagement
    top_platforms = get_top_platforms(ALL_FILTER, top_n=top_n)
    
    # Step 2: Ambil data dari top platform saja
    platform_data = get_social_data(ALL_FILTER, max_posts=50, platforms=top_platforms)
    
    # Step 3: Analisis data untuk setiap platform secara paralel
    platform_analyses = analyze_platform_parallel(platform_data, TOPIC, START_DATE, END_DATE)
    
    # Step 4: Hasilkan rekomendasi berdasarkan analisis platform
    prompt = f"""
    As a communications and media strategy expert, analyze these [{TOPIC}] reports from the top {top_n} social media platforms ({', '.join(top_platforms)}) for the period [{START_DATE}] to [{END_DATE}] and provide strategic recommendations:

    {platform_analyses}

    Format your response as a JSON array with maximum 4 recommendation categories, each with:
    - "title": Clear category description focusing on communication strategy
    - "actions": Array of 2-3 specific, actionable steps

    Example format:
    [
      {{
        "title": "Proactive Reputation Management",
        "actions": ["action 1", "action 2","action 3"]
      }}
    ]

    Focus only on relevant information to {TOPIC} and ensure all recommendations are concrete and implementable.
    """
    
    try:
        recommendations_text = call_gemini(prompt)
        
        # Ekstrak JSON dari respons
        try:
            json_string = re.findall(r'\[\s*\{.*?\}\s*\]', recommendations_text, re.DOTALL)
            if json_string:
                recommendations = json.loads(json_string[0])
            else:
                # Fallback jika regex tidak berhasil
                recommendations = json.loads(recommendations_text)
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            # Fallback parsing sederhana
            recommendations = []
            for match in re.finditer(r'\{\s*"title":\s*"([^"]+)",\s*"actions":\s*\[(.*?)\]\s*\}', recommendations_text, re.DOTALL):
                title = match.group(1)
                actions_text = match.group(2)
                actions = re.findall(r'"([^"]+)"', actions_text)
                recommendations.append({"title": title, "actions": actions})
        
        # Simpan hasil ke file
        with open(os.path.join(SAVE_PATH, 'recommendations.json'), 'w') as f:
            json.dump(recommendations, f, indent=2)
        
        print(f"Total processing time: {time.time() - overall_start:.2f} seconds")
        print(f"Generated recommendations from top {top_n} platforms: {top_platforms}")
        return recommendations
    
    except Exception as e:
        print(f"Error generating recommendations: {e}")
        return []
