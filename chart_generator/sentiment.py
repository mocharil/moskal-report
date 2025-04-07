from chart_generator.functions import *
from dotenv import load_dotenv

load_dotenv()  
BQ = About_BQ(project_id= os.getenv("BQ_PROJECT_ID") ,
         credentials_loc= os.getenv("BQ_CREDS_LOCATION")  )
def plot_half_donut_sentiment(sentiment_counts, colors=None, title=None, save_path = None):
    """
    Buat half-donut gauge chart dari distribusi sentimen.
    """
    labels = list(sentiment_counts.keys())
    values = list(sentiment_counts.values())
    total = sum(values)
    angles = [v / total * 180 for v in values]

    # Default colors
    if colors is None:
        colors = {
            'Positive': '#53b06c',  # green
            'Neutral': '#f5f5f5',   # gray
            'Negative': '#de5242'   # red
        }

    fig, ax = plt.subplots(figsize=(8, 5), subplot_kw={'projection': 'polar'})
    ax.set_theta_direction(-1)
    ax.set_theta_offset(np.pi)
    ax.set_axis_off()

    current_angle = 0
    for label, angle in zip(labels, angles):
        ax.bar(
            x=np.radians(current_angle + angle / 2),
            height=0.4,                 # donut thickness
            width=np.radians(angle),
            bottom=0.7,                 # offset from center (creates hole)
            color=colors.get(label, 'gray'),
            edgecolor='white',
            linewidth=2
        )
        current_angle += angle

    # Legend
    import matplotlib.lines as mlines

    # Legend Labels & Color-Coded Dots
    legend_labels = [f"{label} ({sentiment_counts[label]})" for label in labels]
    handles = [
        mlines.Line2D(
            [], [], color=colors[label], marker='o', linestyle='None',
            markersize=14, label=legend_labels[i]
        )
        for i, label in enumerate(labels)
    ]

    ax.legend(
        handles,
        legend_labels,
        loc='lower center',
        bbox_to_anchor=(0.5, 0.35),
        ncol=len(labels),
        frameon=False
    )
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight',transparent=True)
 
def plot_sentiment_by_channel(df, title="Sentiment Breakdown per Channel", save_path=None):
    df = df.sort_values(by='total_mentions', ascending=False).reset_index(drop=True)
    labels = df['channel']
    pos = df['Positive']
    neu = df['Neutral']
    neg = df['Negative']
    totals = pos + neu + neg
    pos_pct = pos / totals * 100
    neu_pct = neu / totals * 100
    neg_pct = neg / totals * 100
    x = np.arange(len(labels))
    width = 0.6
    fig, ax = plt.subplots(figsize=(8, 4))
    colors = {
        'Positive': '#53b06c',
        'Neutral': '#f5f5f5',
        'Negative': '#de5242'
    }
    p1 = ax.bar(x, pos, width, label='Positive', color=colors['Positive'])
    p2 = ax.bar(x, neu, width, bottom=pos, label='Neutral', color=colors['Neutral'])
    p3 = ax.bar(x, neg, width, bottom=pos+neu, label='Negative', color=colors['Negative'])
    # Tambahkan label persentase dengan background box
    for i in range(len(x)):
        if pos[i] > 0:
            ax.text(
                x[i], pos[i] / 2,
                f"{pos_pct[i]:.1f}%",
                ha='center', va='center',
                fontsize=9, color='white',
                bbox=dict(boxstyle='round,pad=0.2', facecolor=colors['Positive'], edgecolor='none')
            )
        if neu[i] > 0:
            ax.text(
                x[i], pos[i] + neu[i] / 2,
                f"{neu_pct[i]:.1f}%",
                ha='center', va='center',
                fontsize=9, color='black',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='none')
            )
        if neg[i] > 0:
            ax.text(
                x[i], pos[i] + neu[i] + neg[i] / 2,
                f"{neg_pct[i]:.1f}%",
                ha='center', va='center',
                fontsize=9, color='white',
                bbox=dict(boxstyle='round,pad=0.2', facecolor=colors['Negative'], edgecolor='none')
            )
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    # Add this:
    ax.tick_params(axis='x', colors='#757575')
    ax.tick_params(axis='y', colors='#757575')
    ax.set_ylim(0, df[['Positive', 'Neutral', 'Negative']].sum(axis=1).max() * 1.2)
    # Remove all spines
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    # Menghapus baris yang error - tidak ada ax_labels yang didefinisikan
    # for spine in ax_labels.spines.values():
    #     spine.set_visible(False)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight', transparent=True)
    
def get_data(ALL_FILTER):
    
    query = f"""select lower(sentiment) sentiment, a.channel, count(*) total_mentions from medsos.post_analysis a
    join medsos.post_category c
    on a.link_post = c.link_post
    where {ALL_FILTER}

    and LOWER(sentiment) in ('positive','negative','neutral')
    group by 1,2
    """
    

    sentiment_data = BQ.to_pull_data(query)
    
    sentiment_data['sentiment'] = sentiment_data['sentiment'].str.title()

    sentiment_counts = sentiment_data.groupby('sentiment').sum().to_dict()['total_mentions']
    
    pivot_sentiment = pd.pivot(sentiment_data, index=['channel'],columns = ['sentiment'],values = ['total_mentions']).reset_index()
    pivot_sentiment.columns = [''.join(i).replace('total_mentions',''.strip()) for i in pivot_sentiment.columns]
    pivot_sentiment['total_mentions'] = pivot_sentiment[[i for i in pivot_sentiment.columns if i!='channel']].sum(axis=1)

    
    return sentiment_data,sentiment_counts, pivot_sentiment
    
def summarize(TOPIC,ALL_FILTER,sentiment_counts,pivot_sentiment, SAVE_PATH):
    
    query = f"""
    with data as (
    SELECT a.post_caption, a.channel, sentiment, 
    (COALESCE(likes, 0) + COALESCE(shares, 0) + COALESCE(comments, 0) + COALESCE(favorites, 0)
                    + COALESCE(views, 0) + COALESCE(retweets, 0) + COALESCE(replies, 0) 
                    + COALESCE(reposts, 0) + COALESCE(votes, 0)+ reach_score + viral_score) engagement,
    a.link_post
    FROM medsos.post_analysis a
    JOIN medsos.post_category c
    ON a.link_post = c.link_post
    where {ALL_FILTER}
    and LOWER(sentiment) in ('positive','negative')
    ),
    pos as(
    select * from data
    where sentiment = 'positive'
    order by engagement desc
    limit 50),
    neg as (
    select * from data
    where sentiment = 'negative'
    order by engagement desc
    limit 50)

    select * from pos
    UNION ALL
    select * from neg
    """
    sentiment_post = BQ.to_pull_data(query)

    prompt = f"""
    You are a media analyst assistant. the TOPICS is about [{TOPIC}].

    Here is the supporting data:

    1. **Sentiment Breakdown (total mentions)**  
    {sentiment_counts}

    2. **Platform Breakdown (total mentions)**  
    {pivot_sentiment.to_dict(orient = 'records')}

    3. **Top Posts based on engagement**  
    {sentiment_post[['post_caption','channel','sentiment']].to_dict(orient='records')}

    ---

    **Instruction:**  
    - summarize the topic for Positive and Negative Topics
    - Summarize in **1 paragraph only** what likely caused the spike, which platform contributed the most, what sentiment dominated, and what topic(s) were most discussed — **only if relevant to [{TOPIC}]**. 
    - Use a professional, concise tone.
    - output in JSON format


    ** Sample Output **
    {{
    "positive_summarize":<summarize for sentiment positive no more than 50 words>,
    "negative_summarize":<summarize for sentiment negative no more than 50 words>
    }}


    """
    summarize_sentiment = call_gemini(prompt)


    with open(os.path.join(SAVE_PATH,'sentiment_analysis.json'),'w') as f:

        json.dump(eval(re.findall(r'\{.*\}', summarize_sentiment, flags = re.I|re.S)[0]), f)
                
def generate_sentiment_analysis(TOPIC,ALL_FILTER, SAVE_PATH):
    sentiment_data, sentiment_counts, pivot_sentiment = get_data(ALL_FILTER)
    
    #breakdown
    plot_half_donut_sentiment(sentiment_counts, title='Sentiment Distribution',
                              save_path = os.path.join(SAVE_PATH,'sentiment_breakdown.png'))

    #per platform
    plot_sentiment_by_channel(pivot_sentiment, save_path = os.path.join(SAVE_PATH,'sentiment_by_categories.png'))

    #summarize
    summarize(TOPIC,ALL_FILTER,sentiment_counts,pivot_sentiment, SAVE_PATH)