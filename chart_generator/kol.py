from utils.list_of_mentions import get_filtered_mentions
import pandas as pd
import numpy as np
from utils.gemini import call_gemini
import re, json, os


def create_link_user(df):
    if df['channel'] == 'twitter':
        return f"""https://x.com/{df['username'].strip('@ ')}"""
    if df['channel'] == 'instagram':
        return f"""https://www.instagram.com/{df['username'].strip('@ ')}"""
    if df['channel'] == 'tiktok':
        return f"""https://www.tiktok.com/@{df['username'].strip('@ ')}"""
    if df['channel']=='linkedin':
        return f"""https://www.linkedin.com/in/{df['username'].strip('@ ')}"""
    if df['channel']=='reddit':
        return f"""https://www.reddit.com/{df['username'].strip('@ ')}"""
    
    
    return df['username']
     
def add_negative_driver_flag(df):
    """
    Add is_negative_driver column that is True when sentiment_negative 
    is the dominant sentiment
    
    Args:
        df: DataFrame with sentiment_positive, sentiment_negative, and sentiment_neutral columns
        
    Returns:
        DataFrame with added is_negative_driver column
    """
    # Ensure all sentiment columns exist
    for sentiment in ['positive', 'negative', 'neutral']:
        col_name = f'sentiment_{sentiment}'
        if col_name not in df.columns:
            df[col_name] = 0
    
    # Create a new column that checks if negative sentiment is the highest
    df['is_negative_driver'] = False
    
    # Compare sentiment counts and set flag if negative is highest
    condition = ((df['sentiment_negative'] > df['sentiment_positive']) & 
                 (df['sentiment_negative'] > df['sentiment_neutral']))
    
    df['is_negative_driver'] = condition
    
    return df

def create_uuid(keyword):
    # Gunakan namespace standar (ada juga untuk URL, DNS, dll)
    namespace = uuid.NAMESPACE_DNS

    return uuid.uuid5(namespace, keyword)

def generate_kol(MAIN_TOPIC,KEYWORDS, START_DATE, END_DATE, SAVE_PATH):
    # Mendapatkan mentions dengan filter
    result = get_filtered_mentions(
        keywords=KEYWORDS,
        start_date=START_DATE,
        end_date=END_DATE,
        source=["issue","user_connections","user_followers","user_influence_score",
                     'user_image_url',"engagement_rate",
                 "influence_score","reach_score", "viral_score",
                 "sentiment", "link_post","user_category","username",'channel'],
        sort_type='popular',
        page=1,
        page_size=1000
    )


    kol = pd.DataFrame(result['data'])
    print(kol.shape)

    print('set metrics')
    for i in set(['user_influence_score','user_followers']) - set(kol):
        kol[i] = 0

    if 'user_category' not in kol:
        kol['user_category'] = 'News Account'

    kol[['user_influence_score','user_followers']] = kol[['user_influence_score','user_followers']].fillna(0)
    kol['user_category'] = kol['user_category'].fillna('')

    kol['link_user'] = kol.apply(lambda s: create_link_user(s), axis=1)        

    for i in set(['user_connections','user_followers']) - set(kol):
        kol[i] = 0

    kol['user_followers'] = kol['user_connections']+kol['user_followers']

    # Your groupby with sentiment pivot
    agg_kol = kol.groupby(['link_user']).agg({
        'link_post': 'size',
        'viral_score': 'sum',
        'reach_score': 'sum',
        'channel': 'max',
        'username': 'max',
        'user_image_url':'max',
        'user_followers':'max',
        "engagement_rate":'sum',
        'issue': lambda s: list(set(s)),
        'user_category': 'max',
        'user_influence_score': lambda s: max(s)*100,
        'influence_score':'sum'
    })

    # Get sentiment counts per link_user using crosstab
    sentiment_counts = pd.crosstab(kol['link_user'], kol['sentiment'])

    # Rename columns to add 'sentiment_' prefix
    sentiment_counts = sentiment_counts.add_prefix('total_')

    # Join the sentiment counts with the main result
    final_kol = agg_kol.join(sentiment_counts).rename(columns = {'link_post':'total_post'})

    # If any sentiment category is missing, add it with zeros
    for sentiment in ['positive', 'negative', 'neutral']:
        col_name = f'total_{sentiment}'
        if col_name not in final_kol.columns:
            final_kol[col_name] = 0        


    # Apply the function to final_kol
    final_kol = add_negative_driver_flag(final_kol).reset_index()


    final_kol['most_viral'] = (final_kol['viral_score'] + final_kol['reach_score']) * \
              np.log(final_kol['user_followers'] + 1.1) * np.log(final_kol['total_post'] + 1.1)* \
              (final_kol['user_influence_score'] + 1.1)


    prompt = f"""You are a Social Media Analyst Expert. Your task is to analyze and group similar issues together based on their meaning, then generate a concise and meaningful description based on the provided post captions.

    Topics yang sedang di analisis adalah terkait [{MAIN_TOPIC}]

    ### Instructions:
    1. For each username, analyze their issues and **group similar issues** into multiple **unified issue categories**.
    2. Each username may have MULTIPLE unified issue categories based on the content they post.
    3. Format the output as **valid JSON**.
    4. Remove from analysis if you found that the post is not related to the Topic

    ### Data:
    {final_kol[final_kol['channel']!='news'].sort_values('most_viral', ascending = False)[['username','channel','issue']][:100].to_dict(orient = 'records')}

    ### Output Format (JSON):
    [
      {{
        "username": "@username1",
        "channel":"tiktok",
        "unified_issues": ["First Topic Category","Second Topic Category"]
      }},
      {{
        "username": "@username2",
        "channel":"twitter",
        "unified_issues": ["First Topic Category","Second Topic Category"]
      }}
    ]

    ### Critical Rules:
    1. Group issues into natural, meaningful categories based on their semantic similarity.
    2. Each username should have AT LEAST ONE unified issue category, but MAY HAVE MULTIPLE if their content covers distinct topics.
    3. For usernames with many diverse issues, create appropriate multiple categories rather than forcing all into one.
    4. Before finalizing each list_original_issue, PERFORM AN EXPLICIT DEDUPLICATION check.
    5. VERIFY that NO DUPLICATE ENTRIES appear in any list_original_issue.
    6. First remove exact duplicates, then check for semantic duplicates.
    7. Each original issue must appear in EXACTLY ONE unified issue category per username.
    8. Double-check the final output to ensure no duplicates remain in any list_original_issue.

    """


    prediction = call_gemini(prompt)
    try:
        df_prediction = pd.DataFrame(eval(re.findall(r'\[.*\]',prediction, flags=re.I|re.S)[0]))
    except:

        dp = []
        for i in re.findall(r'\{.*?\}', prediction, flags = re.I|re.S):
            try:
                dp.append(eval(i))
            except:
                pass
        df_prediction = pd.DataFrame(dp)  


    result = final_kol.merge(df_prediction, on = ['username','channel']).sort_values('viral_score')
    
    with open(os.path.join(SAVE_PATH,'kol.json'),'w') as f:
        for i in result.to_dict(orient = 'records'):
            f.write(json.dumps(i)+'\n')