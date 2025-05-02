from utils.list_of_mentions import get_filtered_mentions
import pandas as pd
import os

def generate_popular_mentions(KEYWORDS,START_DATE,END_DATE, SAVE_PATH = 'REPORT'):
    # Mendapatkan mentions dengan filter
    result = get_filtered_mentions(
        keywords=KEYWORDS,
        start_date=START_DATE,
        end_date=END_DATE,
        source=['channel', 'username', 'link_post', 'post_created_at', 'likes', 'views',
               'shares', 'reposts', 'comments', 'replies', 'votes', 'favorites',
               'post_caption', 'engagement_rate'],
        sort_type='popular',
        page=1,
        page_size=1000
    )

    popular_mentions = pd.DataFrame(result['data'])
    
    popular_mentions.to_csv(os.path.join(SAVE_PATH,'popular_mentions.csv'),index = False)
  