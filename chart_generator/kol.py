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

def weight_of_influence(df):
    # Pilih kolom metrik yang akan dinormalisasi
    metrics = ['viral_score', 'reach_score', 'influence_score', 'total_post']
    scaler = MinMaxScaler()

    # Buat copy DataFrame untuk menghindari warning
    df_normalized = df.copy()
    df_normalized[metrics] = scaler.fit_transform(df[metrics])

    # 2. Tentukan bobot untuk masing-masing metrik berdasarkan kepentingannya
    # Misalnya, jika influence_score dianggap lebih penting, beri bobot lebih tinggi
    weights = {
        'viral_score': 0.25,
        'reach_score': 0.20,
        'influence_score': 0.25,
        'total_post': 0.30
    }

    # Pastikan total bobot = 1
    assert sum(weights.values()) == 1.0, "Total bobot harus 1.0"

    # 3. Hitung skor pengaruh berdasarkan bobot
    df_normalized['weighted_influence'] = (
        df_normalized['viral_score'] * weights['viral_score'] +
        df_normalized['reach_score'] * weights['reach_score'] +
        df_normalized['influence_score'] * weights['influence_score'] +
        df_normalized['total_post'] * weights['total_post']
    )

    # 4. Tambahkan skor terbobot ke DataFrame asli
    df['weighted_influence'] = df_normalized['weighted_influence']

    # 5. Urutkan berdasarkan skor pengaruh terbobot (dari tertinggi ke terendah)
    top_influencers = df.sort_values('weighted_influence', ascending=False)
    return top_influencers

def generate_kol(TOPIC,ALL_FILTER, SAVE_PATH = 'PPT'):
    query = f"""SELECT 
         a.channel,
        case when a.channel='news' then CONCAT(SPLIT(a.link_post, '/')[OFFSET(0)], '//', SPLIT(a.link_post, '/')[SAFE_OFFSET(2)])
        else coalesce(username,REGEXP_EXTRACT(c.link_post, r'(@[^/]+)')) end AS username,
        c.link_post,  -- Tambahkan identifier untuk post
        c.issue,
        a.post_created_at,  -- Tambahkan untuk pengurutan
        sum(a.viral_score) viral_score,  -- Tambahkan untuk pengurutan
        sum(a.reach_score) reach_score,
        sum(a.influence_score) influence_score,
        COUNT(*) AS total_post,
        ROUND(100 * SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) / COUNT(*), 2) AS percentage_negative,
        ROUND(100 * SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) / COUNT(*), 2) AS percentage_positive,
        ROUND(100 * SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) / COUNT(*), 2) AS percentage_neutral,
        SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) AS total_negative,  -- Total negative sentiment
        SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) AS total_positive,  -- Total positive sentiment
        SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) AS total_neutral  -- Total neutral sentiment
      FROM 
        medsos.post_category c 
      JOIN 
        medsos.post_analysis a
      ON 
        c.link_post = a.link_post
      WHERE 
         {ALL_FILTER}
        AND LOWER(issue) NOT IN ('not specified','no caption','n/a','no caption provided')
      GROUP BY 
        1, 2, 3, 4 ,5
        """

    data = BQ.to_pull_data(query)

    data['username'] = data.apply(lambda s: get_new_name(s['username']) if s['channel']=='news' else s['username'], axis=1)

    data_agg = data.groupby(['channel','username']).agg({"viral_score":"sum",'reach_score':'sum',
                                                         'influence_score':'mean',
                                              'total_post':'sum','total_negative':'sum',
                                              'total_positive':'sum','total_neutral':'sum',
                                             'issue':lambda s: list(set(s))}).reset_index()

    data_popular = weight_of_influence(data_agg)


    prompt = f"""You are a Social Media Analyst Expert. Your task is to analyze and group similar issues together based on their meaning, then generate a concise and meaningful description based on the provided post captions.

    Topics yang sedang di analisis adalah terkait [{TOPIC}]

    ### Instructions:
    1. For each username, analyze their issues and **group similar issues** into multiple **unified issue categories**.
    2. Each username may have MULTIPLE unified issue categories based on the content they post.
    3. Format the output as **valid JSON**.
    4. Remove from analysis if you found that the post is not related to the Topic

    ### Data:
    {data_popular[data_popular['channel']!='news'][['username','channel','issue']][:100].to_dict(orient = 'records')}

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
    
    
    
    result = data_agg.merge(df_prediction, on = ['username','channel']).sort_values('viral_score')

    query = f"""select a.username, a.channel,  coalesce(followings,0) followings, 
    user_image_url,
    case when a.channel = 'linkedin' then connections else
    coalesce(followers,followers_last) end followers,
    coalesce(c.category,'-') user_category

    from medsos.user_analysis a
    left join medsos.user_category c
    on a.link_user = c.link_user
    where a.username in {tuple(result['username'].to_list())}
    """
    user = BQ.to_pull_data(query)

    kol_sosmed = result.merge(user, on = ['username','channel'], how='left')

    kol_sosmed[['followings','followers']] = kol_sosmed[['followings','followers']].fillna(0)
    kol_sosmed = kol_sosmed.fillna('')

    with open(os.path.join(SAVE_PATH,'kol.json'),'w') as f:
        for i in kol_sosmed.to_dict(orient = 'records'):
            f.write(json.dumps(i)+'\n')