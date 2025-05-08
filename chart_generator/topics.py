import requests
from utils.list_of_mentions import get_filtered_mentions
import pandas as pd
import os, json
from dotenv import load_dotenv
load_dotenv()


def generate_topic_overview(TOPIC, KEYWORDS, START_DATE, END_DATE, SAVE_PATH):
    url = f"{os.getenv('BASE_URL_API')}/api/v2/topics-overview"

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "keywords": KEYWORDS,
        "sentiment": ["positive", "negative", "neutral"],
        "date_filter": "custom",
        "custom_start_date": START_DATE,
        "custom_end_date": END_DATE,
        "owner_id": "5",
        "project_name": TOPIC
    }

    for i in range(5):
        try:
            response = requests.post(url, headers=headers, json=payload)
            df_topics = pd.DataFrame(response.json())
            break
        except:
            pass

    df_topics = df_topics.rename(columns = {'viral_score':'total_viral_score',
                            'reach_score':'total_reach_score',
                            'total_posts':'total_issue'})

    df_topics['percentage_negative'] = round(df_topics['negative']/df_topics['total_issue']*100)
    df_topics['percentage_positive'] = round(df_topics['positive']/df_topics['total_issue']*100)
    df_topics['percentage_neutral'] = round(df_topics['neutral']/df_topics['total_issue']*100)


    df_top_final = df_topics[:5]
    list_references = []
    for list_issue in df_top_final['list_issue']:
        references = get_filtered_mentions(
            keywords=list_issue,
            start_date=START_DATE,
            end_date=END_DATE,
            source=["channel",'link_post'],
            sort_type='popular',
            page=1,
            page_size=5
        ) 
        list_references.append(references['data'])
    df_top_final['references'] = list_references

    with open(os.path.join(SAVE_PATH,'topic_overview.json'),'w') as f:
        for i in df_top_final.to_dict(orient = 'records'):
            f.write(json.dumps(i)+'\n')