from chart_generator.functions import *

from dotenv import load_dotenv

load_dotenv()  
BQ = About_BQ(project_id= os.getenv("BQ_PROJECT_ID") ,
         credentials_loc= os.getenv("BQ_CREDS_LOCATION")  )
def plot_donut_score(score, title="How much attention\na topic or figure gets", save_path=None):
    """
    Create a donut chart with score (0-100) in the center.
    
    Parameters:
        score (float): Score between 0 and 100
        title (str): Text shown below the chart
        save_path (str): Optional file path to save the chart
    """
    # Colors
    main_color = '#1a73e8'
    bg_color = '#e0e0e0'

    # Create figure
    fig, ax = plt.subplots(figsize=(3, 3))
    ax.pie([score, 100 - score],
           startangle=90,
           colors=[main_color, bg_color],
           wedgeprops=dict(width=0.42),
           counterclock=False)

    # Center text
    ax.text(0, 0, f"{int(round(score))}", ha='center', va='center', fontsize=40, color='#333333')

    # Title below the donut
    plt.text(0, -1.3, title, ha='center', va='center', fontsize=12, color='#757575')

    # Remove all axes
    ax.set_aspect('equal')
    plt.axis('off')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150, transparent=True)


def plot_presence_score_trend(data, title="Your presence score", save_path=None,
                              show_dots=True, color_theme='#1a73e8'):
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    x = df['date']
    y = df['presence_score'].values

    # Smooth
    def smooth(x, y):
        if len(x) < 4:
            return x, y
        x_numeric = np.arange(len(x))
        spl = make_interp_spline(x_numeric, y, k=3)
        xnew = np.linspace(x_numeric.min(), x_numeric.max(), 300)
        ynew = spl(xnew)
        x_interp = np.interp(xnew, x_numeric, x.astype(np.int64) // 10**9)
        x_interp = pd.to_datetime(x_interp, unit='s')
        return x_interp, ynew

    x_smooth, y_smooth = smooth(x, y)

    # Plot
    fig, ax = plt.subplots(figsize=(12, 4))  # 33.35cm x 9.14cm
    ax.set_facecolor('#ffffff')
    fig.patch.set_facecolor('#ffffff')

    ax.plot(x_smooth, y_smooth, color=color_theme, label=title, linewidth=2)

    if show_dots:
        ax.scatter(x, y, color=color_theme, s=15, zorder=3)

    # Clean styling
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.tick_params(axis='y', colors=color_theme)
    ax.yaxis.label.set_color(color_theme)
    ax.grid(axis='y', linestyle='-', linewidth=0.5, alpha=0.3)

    ax.xaxis.set_major_formatter(DateFormatter('%d %b %Y'))
    plt.xticks(rotation=0)
    ax.xaxis.label.set_color('#5f6368')

    # Annotate peak
    peak_idx = np.argmax(y)
    peak_date = x.iloc[peak_idx]
    peak_value = y[peak_idx]
    label = f"{int(round(peak_value))} on {peak_date.strftime('%d %b %Y')}"
    ax.annotate(label, xy=(peak_date, peak_value), xytext=(peak_date, peak_value + 5),
                ha='center', fontsize=9, color=color_theme,
                arrowprops=dict(arrowstyle='-', color=color_theme, lw=1))

    # Legend
    ax.legend(loc='best', frameon=False)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150, transparent=True)



def get_data(ALL_FILTER):
    query = f"""
    WITH topic_data AS (
        SELECT 
            DATE(post_created_at) AS date,
            COUNT(*) AS total_mentions,
            SUM(reach_score) AS total_reach,
            SUM(COALESCE(likes, 0) + COALESCE(shares, 0) + COALESCE(comments, 0) + COALESCE(favorites, 0)
                    + COALESCE(views, 0) + COALESCE(retweets, 0) + COALESCE(replies, 0) 
                    + COALESCE(reposts, 0) + COALESCE(votes, 0)) AS total_engagement
        FROM medsos.post_analysis a
    where {ALL_FILTER}
        GROUP BY 1
    ),
    max_values AS (
        SELECT 
            MAX(total_mentions) AS max_mentions,
            MAX(total_reach) AS max_reach,
            MAX(total_engagement) AS max_engagement
        FROM topic_data
    ),
    presence_score_calc AS (
        SELECT 
            t.date,
            t.total_mentions,
            t.total_reach,
            t.total_engagement,
            ROUND(
                ((t.total_mentions / NULLIF(m.max_mentions, 0)) * 40) +
                ((t.total_reach / NULLIF(m.max_reach, 0)) * 40) +
                ((t.total_engagement / NULLIF(m.max_engagement, 0)) * 20), 2
            ) AS presence_score
        FROM topic_data t
        CROSS JOIN max_values m
    )
    SELECT 
        date,
        presence_score
    FROM presence_score_calc
    ORDER BY date ASC;

    """
    presence_score = BQ.to_pull_data(query)

    presence_score['date'] = presence_score['date'].astype(str)

    return presence_score

def presence_description(TOPIC, FILTER_KEYWORD, high_presence_date,SAVE_PATH):
    
    query = f"""
    WITH 
    metric_data AS (
        SELECT 
            sentiment, 
            a.channel, 
            COUNT(*) AS total_mentions
        FROM medsos.post_analysis a
        JOIN medsos.post_category c
        ON a.link_post = c.link_post
        WHERE {FILTER_KEYWORD}
        AND a.post_created_at BETWEEN '{high_presence_date} 00:00:00' AND '{high_presence_date} 29:59:59'
        GROUP BY 1, 2
    ),
    post_data AS (
        SELECT * from (select
            a.post_caption, 
            a.channel, 
            c.issue, 
            sentiment,
            reach_score, 
            viral_score, 
            (COALESCE(likes, 0) + COALESCE(shares, 0) + COALESCE(comments, 0) + COALESCE(favorites, 0)
             + COALESCE(views, 0) + COALESCE(retweets, 0) + COALESCE(replies, 0) 
             + COALESCE(reposts, 0) + COALESCE(votes, 0)) AS engagement,
            a.link_post
        FROM medsos.post_analysis a
        JOIN medsos.post_category c
        ON a.link_post = c.link_post
        WHERE {FILTER_KEYWORD}
        AND a.post_created_at BETWEEN '{high_presence_date} 00:00:00' AND '{high_presence_date} 29:59:59'
        AND LOWER(c.issue) NOT IN ('not specified'))
        order by (reach_score + viral_score + engagement) desc
        limit 100
    )
    -- Gabungkan hasil dari kedua CTE dengan UNION ALL
    SELECT 
        'metrics' AS data_type,
        sentiment,
        channel,
        total_mentions,
        NULL AS post_caption,
        NULL AS issue,
        NULL AS reach_score,
        NULL AS viral_score,
        NULL AS engagement,
        NULL AS link_post
    FROM metric_data

    UNION ALL

    SELECT 
        'posts' AS data_type,
        sentiment,
        channel,
        NULL AS total_mentions,
        post_caption,
        issue,
        reach_score,
        viral_score,
        engagement,
        link_post
    FROM post_data
    ORDER BY data_type, 
        CASE WHEN data_type = 'posts' THEN (reach_score + viral_score + engagement) END DESC
    """

    # Eksekusi query gabungan
    combined_results = BQ.to_pull_data(query)

    # Pisahkan hasil berdasarkan data_type
    metric_presence = combined_results[combined_results['data_type'] == 'metrics']
    sample_post_presence = combined_results[combined_results['data_type'] == 'posts']

    #summarize
    prompt = f"""
    You are a media analyst assistant. Analyze a spike in presence score related to the topic [{TOPIC}] on {high_presence_date}.

    Here is the supporting data:

    1. **Sentiment Breakdown (total mentions)**  
    {metric_presence.groupby('sentiment').sum().to_dict()['total_mentions']}

    2. **Platform Breakdown (total mentions)**  
    {metric_presence.groupby('channel').sum().to_dict()['total_mentions']}

    3. **Top Posts on {high_presence_date}**  
    {sample_post_presence[['post_caption','channel']].to_dict(orient='records')}

    ---

    **Instruction:**  
    Summarize in **1 paragraph only** what likely caused the spike, which platform contributed the most, what sentiment dominated, and what topic(s) were most discussed — **only if relevant to [{TOPIC}]**. Use a professional, concise tone.
    """
    summarize = call_gemini(prompt)

    with open(os.path.join(SAVE_PATH,'presence_score_analysis.json'),'w') as f:
        json.dump({'analysis':summarize},f)
        
def generatre_presence_score(TOPIC, ALL_FILTER, FILTER_KEYWORD, SAVE_PATH):
    
    presence_score = get_data(ALL_FILTER)
    
    plot_donut_score(presence_score['presence_score'].mean(),
                     save_path = os.path.join(SAVE_PATH,'presence_score_donut.png'))

    plot_presence_score_trend(presence_score.to_dict(orient = 'records'),
                              save_path = os.path.join(SAVE_PATH,'presence_trend.png'))
    
    high_presence_date = presence_score.sort_values('presence_score', ascending = False)['date'].to_list()[0]
    
    presence_description(TOPIC, FILTER_KEYWORD, high_presence_date, SAVE_PATH)