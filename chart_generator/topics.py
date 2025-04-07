from chart_generator.functions import *
from dotenv import load_dotenv

load_dotenv()  
BQ = About_BQ(project_id= os.getenv("BQ_PROJECT_ID") ,
         credentials_loc= os.getenv("BQ_CREDS_LOCATION")  )
def join_issues_with_metrics(data, df_prediction):
    """
    Join the metrics data with the prediction data based on issue mapping.
    
    Args:
        data (list/DataFrame): List of dictionaries or DataFrame containing metrics data
        df_prediction (list/DataFrame): List of dictionaries or DataFrame containing prediction data
        
    Returns:
        DataFrame: Joined and aggregated DataFrame
    """
    # Convert to DataFrames if they're lists
    if isinstance(data, list):
        data_df = pd.DataFrame(data)
    else:
        data_df = data.copy()
        
    if isinstance(df_prediction, list):
        pred_df = pd.DataFrame(df_prediction)
    else:
        pred_df = df_prediction.copy()
    
    # Create an empty results DataFrame to store our joined data
    results = []
    
    # Iterate through each unified issue
    for _, row in pred_df.iterrows():
        unified_issue = row['unified_issue']
        list_issues = row['list_original_issue']
        description = row['description']
        
        # Find all matching issues in data_df
        matching_issues = data_df[data_df['issue'].isin(list_issues)]
        
        if len(matching_issues) > 0:
            # Aggregate the metrics
            total_issue = matching_issues['total_issue'].sum()
            total_reach_score = matching_issues['total_reach_score'].sum()
            total_viral_score = matching_issues['total_viral_score'].sum()
            
            # Calculate weighted averages for percentages
            weighted_neg = np.average(
                matching_issues['percentage_negative'], 
                weights=matching_issues['total_issue']
            ) if len(matching_issues) > 0 else 0
            
            weighted_pos = np.average(
                matching_issues['percentage_positive'], 
                weights=matching_issues['total_issue']
            ) if len(matching_issues) > 0 else 0
            
            weighted_neutral = np.average(
                matching_issues['percentage_neutral'], 
                weights=matching_issues['total_issue']
            ) if len(matching_issues) > 0 else 0
            
            # Add to results
            results.append({
                'unified_issue': unified_issue,
                'description': description,
                'total_issue': total_issue,
                'total_viral_score': total_viral_score,
                'total_reach_score':total_reach_score,
                'percentage_negative': round(weighted_neg, 2),
                'percentage_positive': round(weighted_pos, 2),
                'percentage_neutral': round(weighted_neutral, 2),
                'list_issue': list_issues
            })
        else:
            # If no matching issues were found, still include the unified issue
            # but with zero values for metrics
            results.append({
                'unified_issue': unified_issue,
                'description': description,
                'total_issue': 0,
                'total_viral_score': 0,
                'total_reach_score':0,
                'percentage_negative': 0,
                'percentage_positive': 0,
                'percentage_neutral': 0,
                'list_issue': list_issues
            })
    
    # Convert results to DataFrame
    results_df = pd.DataFrame(results)
    results_df['share_of_voice'] = results_df['total_issue']/results_df['total_issue'].sum()
    return results_df

def get_references(rf):
    # Hitung jumlah unique channel
    unique_channels = rf['channel'].nunique()

    # Tentukan jumlah top posts per channel berdasarkan jumlah unique channel
    if unique_channels <= 2:
        # Jika channel <= 2, ambil top 3 untuk setiap channel
        n_per_channel = 3
    elif unique_channels == 3:
        # Jika channel = 3, ambil top 2 untuk setiap channel
        n_per_channel = 2
    else:
        # Jika channel >= 4, ambil top 1 untuk setiap channel
        n_per_channel = 1
        # Batasi pada 6 channel teratas jika terlalu banyak channel
        if unique_channels > 6:
            # Dapatkan 6 channel dengan rata-rata reach_score tertinggi
            top_channels = rf.groupby('channel')['reach_score'].mean().nlargest(6).index.tolist()
            # Filter rf hanya untuk channel-channel tersebut
            rf_filtered = rf[rf['channel'].isin(top_channels)]
        else:
            rf_filtered = rf

    # Ambil top n_per_channel posts untuk setiap channel
    if unique_channels > 6:
        # Jika sudah difilter ke 6 channel teratas
        top_posts = rf_filtered.groupby('channel').apply(
            lambda x: x.nlargest(n_per_channel, 'reach_score')
        ).reset_index(drop=True)
    else:
        # Jika jumlah channel <= 6
        top_posts = rf.groupby('channel').apply(
            lambda x: x.nlargest(n_per_channel, 'reach_score')
        ).reset_index(drop=True)

    # Tampilkan hasil
    print(f"Total posts: {len(top_posts)}")
    return (top_posts[['channel', 'link_post']])

def generate_topic_overview(ALL_FILTER, TOPIC, SAVE_PATH = 'PPT'):
    # GET DATA
    query = f"""
        WITH filtered_posts AS (
            SELECT
                c.issue,
                a.viral_score,
                c.sentiment,
                a.post_caption,
                a.reach_score
            FROM medsos.post_analysis a
            JOIN medsos.post_category c
                ON a.link_post = c.link_post
            WHERE
                {ALL_FILTER}
                AND lower(issue) NOT IN ('not specified')
        )

        SELECT
            issue,
            COUNT(issue) AS total_issue,
            SUM(viral_score) AS total_viral_score,
            SUM(reach_score) AS total_reach_score,
            ROUND(100 * SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) / COUNT(*), 2) AS percentage_negative,
            ROUND(100 * SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) / COUNT(*), 2) AS percentage_positive,
            ROUND(100 * SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) / COUNT(*), 2) AS percentage_neutral,
            ARRAY_AGG(post_caption ORDER BY viral_score DESC LIMIT 3) AS top_post_captions
        FROM filtered_posts
        GROUP BY issue
        ORDER BY total_issue DESC, total_viral_score DESC
        LIMIT 40;"""
    data = BQ.to_pull_data(query)

    # Summarize Topics
    prompt = f"""
    You are a Social Media Analyst Expert. This is the topic about [{TOPIC}]
    Your task is to analyze and group similar issues together based on their meaning, then generate a concise and meaningful description based on the provided post captions.

    ### Instructions:
    1. Identify and **group similar issues** under a single **unified issue name** that best represents the grouped topics.
    2. For each unified issue:
       - Create a **list_original_issue** containing ONLY the unique original issue names grouped under this unified issue.
       - IMPORTANT: After collecting all original issues, REMOVE ALL DUPLICATES before finalizing the list_original_issue.
       - Process each string to ensure exact duplicates (including case and spacing) are removed.
       - Check for and eliminate semantic duplicates (same meaning but slightly different wording).
    3. Use the **top_post_captions** from each issue group to generate a **short and insightful description** summarizing the key discussions.
    4. Remove from analysis if you found that the post is not related to the Topic
    5. Format the output as **valid JSON**.

    ### Data:
    {data[['issue', 'top_post_captions']].to_dict(orient='records')}

    ### Output Format (JSON):
    [
      {{
        "unified_issue": "<Unified issue name>",
        "list_original_issue": ["<issue 1>", "<issue 2>", "<issue 3>"],
        "description": "<A short yet meaningful analysis considering key discussion points from the captions, jangan gunakan tanda kutip \" tapi gunakan \`>"
      }}
    ]

    ### Critical Rules for list_original_issue:
    - Before finalizing each list_original_issue, PERFORM AN EXPLICIT DEDUPLICATION check.
    - VERIFY that NO DUPLICATE ENTRIES appear in any list_original_issue.
    - First remove exact duplicates, then check for semantic duplicates (like "Student protests against government" vs "Student protests against government policies").
    - Each original issue must appear in EXACTLY ONE unified group.
    - Double-check the final output to ensure no duplicates remain in any list_original_issue.
    """

    
    prediction = call_gemini(prompt)
    df_prediction = pd.DataFrame(eval(re.findall(r'\[.*\]',prediction, flags=re.I|re.S)[0]))

    result_df = join_issues_with_metrics(data, df_prediction)

    # Get References
    query = f"""
    select c.link_post, c.issue,  reach_score, a.channel from medsos.post_category  c
    JOIN medsos.post_analysis a
    ON a.link_post = c.link_post
    where c.issue in {tuple([j for i in result_df.head(5)['list_issue'] for j in i])}
    order by viral_score desc 

    """
    list_berita = BQ.to_pull_data(query)
    #reach_score,viral_score, influence_score,
    references = []
    for issues in result_df['list_issue']:
        rf = list_berita[list_berita['issue'].isin(issues)]
        channels = rf['channel'].nunique()
        references.append(get_references(rf).to_dict(orient = 'records'))

    result_df['references'] = references

    with open(os.path.join(SAVE_PATH,'topic_overview.json'),'w') as f:
        for i in result_df.to_dict(orient = 'records'):
            f.write(json.dumps(i)+'\n')
        