from chart_generator.functions import *
from dotenv import load_dotenv

load_dotenv()  
BQ = About_BQ(project_id= os.getenv("BQ_PROJECT_ID") ,
         credentials_loc= os.getenv("BQ_CREDS_LOCATION")  )
def get_new_name(username):
    news = (username.replace('https://','').replace('www.',''))
    new_name = re.findall(r'[a-zA-Z0-9\-]+\.(?:co|id|news|info|net)[\.idm]*', news)
    if new_name:
        return new_name[0]
    return news
    
def generate_popular_mentions(ALL_FILTER, SAVE_PATH):
    query = f"""WITH post_metrics AS (
      SELECT 
        a.channel, 
        case when a.channel='news' then CONCAT(SPLIT(a.link_post, '/')[OFFSET(0)], '//', SPLIT(a.link_post, '/')[SAFE_OFFSET(2)])
        else username end username, 
        a.link_post, 
        post_created_at,
        likes, 
        views, 
        shares, 
        reposts, 
        comments, 
        replies,
        votes, 
        favorites,
        a.post_caption,
        CASE
          WHEN a.channel = 'youtube' THEN 
            COALESCE(likes, 0)*0.4 + COALESCE(views, 0)*0.3 + COALESCE(comments, 0)*0.3
          WHEN a.channel = 'twitter' THEN 
            COALESCE(likes, 0)*0.3 + COALESCE(views, 0)*0.2 + COALESCE(shares, 0)*0.3 + COALESCE(favorites, 0)*0.2
          WHEN a.channel = 'tiktok' THEN 
            COALESCE(likes, 0)*0.3 + COALESCE(views, 0)*0.3 + COALESCE(comments, 0)*0.2 + COALESCE(shares, 0)*0.2
          WHEN a.channel = 'instagram' THEN 
            COALESCE(likes, 0)*0.4 + COALESCE(views, 0)*0.3 + COALESCE(comments, 0)*0.3
          WHEN a.channel = 'linkedin' THEN 
            COALESCE(likes, 0)*0.4 + COALESCE(views, 0)*0.2 + COALESCE(comments, 0)*0.2 + COALESCE(shares, 0)*0.2
          WHEN a.channel = 'reddit' THEN 
            COALESCE(votes, 0)*0.7 + COALESCE(comments, 0)*0.3
          ELSE
            COALESCE(likes, 0)*0.25 + COALESCE(views, 0)*0.15 + 
            COALESCE(comments, 0)*0.15 + COALESCE(shares, 0)*0.15 + 
            COALESCE(reposts, 0)*0.1 + COALESCE(replies, 0)*0.1 + 
            COALESCE(votes, 0)*0.05 + COALESCE(favorites, 0)*0.05
        END AS raw_score
      FROM 
        medsos.post_analysis a


        where {ALL_FILTER}
        ),
        channel_stats AS (
          SELECT
            channel,
            MAX(raw_score) AS max_score,
            MIN(raw_score) AS min_score
          FROM
            post_metrics
          GROUP BY
            channel
        )
        SELECT 
          p.channel, 
          p.username, 
          p.link_post, 
          p.post_created_at,
          p.likes, 
          p.views, 
          p.shares, 
          p.reposts, 
          p.comments, 
          p.replies,
          p.votes, 
          p.favorites,
          post_caption,
          CASE
            -- If max_score equals min_score (all posts have same engagement), assign 50
            WHEN c.max_score = c.min_score THEN 50
            -- Otherwise normalize to 0-100 scale
            ELSE ROUND(100 * (p.raw_score - c.min_score) / NULLIF((c.max_score - c.min_score), 0))
          END AS engagement_score
        FROM 
          post_metrics p
        JOIN
          channel_stats c
        ON
          p.channel = c.channel
        ORDER BY 
          engagement_score DESC

        limit 50

        """
    popular_mentions = BQ.to_pull_data(query).sort_values(['engagement_score', 'post_created_at'], ascending = [False,False])

    popular_mentions['username'] = popular_mentions.apply(lambda s: get_new_name(s['username']) if s['channel']=='news' else s['username'], axis=1)
    
    popular_mentions.to_csv(os.path.join(SAVE_PATH,'popular_mentions.csv'),index = False)