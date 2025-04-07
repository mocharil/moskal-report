from chart_generator.functions import *
from dotenv import load_dotenv

load_dotenv()  
BQ = About_BQ(project_id= os.getenv("BQ_PROJECT_ID") ,
         credentials_loc= os.getenv("BQ_CREDS_LOCATION")  )

def create_sentiment_wordcloud(data, width=600, height=350, background_color='white', 
                              max_words=100, figsize=(8, 5), title="Hashtag Word Cloud by Sentiment", word='hashtag'):

    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Create a frequency dictionary for the word cloud
    freq_dict = {row[word]: row['total_mentions'] for _, row in df.iterrows()}
    
    # Create a color function based on sentiment
    sentiment_color_map = {
        'positive': '#2ca02c',  # Darker Green
        'negative': '#e63939',  # Bright Red
        'neutral': '#7f7f7f'    # Blue
    }
    

    # Create a mapping of words to their sentiment colors
    word_to_color = {row[word]: sentiment_color_map[row['dominant_sentiment']] 
                    for _, row in df.iterrows()}
    
    # Define color function
    def color_func(word, **kwargs):
        return word_to_color.get(word, '#000000')  # Default to black if word not found
    
    # Create a mask to make the word cloud more compact (oval shape)
    x, y = np.ogrid[:height, :width]
    mask = (x - height/2) ** 2 / (height/2) ** 2 + (y - width/2) ** 2 / (width/2) ** 2 > 1
    mask = 255 * mask.astype(int)
    
    # Configure WordCloud with improved parameters
    wc = WordCloud(
        max_words=max_words,
        width=width,
        height=height,
        background_color=background_color,
        prefer_horizontal=1.0,  # Force horizontal text only
        relative_scaling=0.5,  # Higher value gives more weight to frequency
        collocations=False,
        color_func=color_func,
        min_font_size=10,
        max_font_size=80,
        font_step=1,
        random_state=42,
        font_path='arial.ttf'
    ).generate_from_frequencies(freq_dict)
    
    # Create figure and display the word cloud
    fig, ax = plt.subplots(figsize=figsize)
    ax.imshow(wc, interpolation='bilinear')
    ax.set_axis_off()
    
    plt.tight_layout(pad=0)
    return fig, ax

def context(ALL_FILTER, SAVE_PATH):
    query = f"""WITH posts_with_sentiment AS (
            SELECT 
                a.post_caption,
                c.sentiment
            FROM 
                medsos.post_analysis a
            JOIN
                medsos.post_category c
            ON 
                a.link_post = c.link_post
            WHERE 
                {ALL_FILTER}
                AND c.sentiment IS NOT NULL
        ),
        extracted_hashtags AS (
            SELECT 
                REGEXP_EXTRACT_ALL(LOWER(post_caption), r'\w+') AS hashtags,

                sentiment
            FROM posts_with_sentiment
        ),
        hashtag_sentiments AS (
            SELECT 
                hashtag,
                sentiment, 
                COUNT(*) AS sentiment_count
            FROM 
                extracted_hashtags,
                UNNEST(hashtags) AS hashtag
            GROUP BY 
                hashtag, sentiment
        ),
        hashtag_totals AS (
            SELECT 
                hashtag,
                SUM(sentiment_count) AS total_mentions
            FROM 
                hashtag_sentiments
            GROUP BY 
                hashtag
        ),
        sentiment_percentages AS (
            SELECT 
                h.hashtag,
                h.sentiment,
                h.sentiment_count,
                t.total_mentions,
                ROUND(h.sentiment_count / t.total_mentions * 100, 1) AS percentage
            FROM 
                hashtag_sentiments h
            JOIN 
                hashtag_totals t
            ON 
                h.hashtag = t.hashtag
        ),
        dominant_sentiments AS (
            SELECT 
                hashtag,
                total_mentions,
                ARRAY_AGG(STRUCT(sentiment, sentiment_count, percentage)
                          ORDER BY sentiment_count DESC 
                          LIMIT 1)[OFFSET(0)].sentiment AS dominant_sentiment,
                ARRAY_AGG(STRUCT(sentiment, sentiment_count, percentage)
                          ORDER BY sentiment_count DESC 
                          LIMIT 1)[OFFSET(0)].sentiment_count AS dominant_sentiment_count,
                ARRAY_AGG(STRUCT(sentiment, sentiment_count, percentage)
                          ORDER BY sentiment_count DESC 
                          LIMIT 1)[OFFSET(0)].percentage AS dominant_sentiment_percentage
            FROM 
                sentiment_percentages
            GROUP BY 
                hashtag, total_mentions
        )
        SELECT 
            hashtag word, 
            total_mentions,
            dominant_sentiment,
            dominant_sentiment_count,
            dominant_sentiment_percentage
        FROM 
            dominant_sentiments
        WHERE LENGTH(hashtag) > 2 
        ORDER BY 
            total_mentions DESC
        LIMIT 700;"""

    word = BQ.to_pull_data(query)

    with open('utils/stopwords.txt') as f:
        list_stopword = f.read().split()

    word = word[~word['word'].isin(list_stopword)]

    fig, ax = create_sentiment_wordcloud(word.to_dict(orient = 'records'), word = 'word')
    save_file = os.path.join(SAVE_PATH, 'word_sentiment_wordcloud.png')
    plt.savefig(save_file, dpi=500, bbox_inches='tight', transparent=True)


def hashtags(ALL_FILTER, SAVE_PATH):
    query = f"""WITH posts_with_sentiment AS (
            SELECT 
                a.post_caption,
                c.sentiment
            FROM 
                medsos.post_analysis a
            JOIN
                medsos.post_category c
            ON 
                a.link_post = c.link_post
            WHERE 
                {ALL_FILTER}
                AND c.sentiment IS NOT NULL
        ),
        extracted_hashtags AS (
            SELECT 
                REGEXP_EXTRACT_ALL(LOWER(post_caption), r'#\w+') AS hashtags,
                sentiment
            FROM posts_with_sentiment
        ),
        hashtag_sentiments AS (
            SELECT 
                hashtag,
                sentiment, 
                COUNT(*) AS sentiment_count
            FROM 
                extracted_hashtags,
                UNNEST(hashtags) AS hashtag
            GROUP BY 
                hashtag, sentiment
        ),
        hashtag_totals AS (
            SELECT 
                hashtag,
                SUM(sentiment_count) AS total_mentions
            FROM 
                hashtag_sentiments
            GROUP BY 
                hashtag
        ),
        sentiment_percentages AS (
            SELECT 
                h.hashtag,
                h.sentiment,
                h.sentiment_count,
                t.total_mentions,
                ROUND(h.sentiment_count / t.total_mentions * 100, 1) AS percentage
            FROM 
                hashtag_sentiments h
            JOIN 
                hashtag_totals t
            ON 
                h.hashtag = t.hashtag
        ),
        dominant_sentiments AS (
            SELECT 
                hashtag,
                total_mentions,
                ARRAY_AGG(STRUCT(sentiment, sentiment_count, percentage)
                          ORDER BY sentiment_count DESC 
                          LIMIT 1)[OFFSET(0)].sentiment AS dominant_sentiment,
                ARRAY_AGG(STRUCT(sentiment, sentiment_count, percentage)
                          ORDER BY sentiment_count DESC 
                          LIMIT 1)[OFFSET(0)].sentiment_count AS dominant_sentiment_count,
                ARRAY_AGG(STRUCT(sentiment, sentiment_count, percentage)
                          ORDER BY sentiment_count DESC 
                          LIMIT 1)[OFFSET(0)].percentage AS dominant_sentiment_percentage
            FROM 
                sentiment_percentages
            GROUP BY 
                hashtag, total_mentions
        )
        SELECT 
            hashtag, 
            total_mentions,
            dominant_sentiment,
            dominant_sentiment_count,
            dominant_sentiment_percentage
        FROM 
            dominant_sentiments
        ORDER BY 
            total_mentions DESC
        LIMIT 50;"""

    hashtags = BQ.to_pull_data(query)

    fig, ax = create_sentiment_wordcloud(hashtags.to_dict(orient = 'records'), word = 'hashtag')
    save_file = os.path.join(SAVE_PATH,'hashtag_sentiment_wordcloud.png')
    plt.savefig(save_file, dpi=500, bbox_inches='tight', transparent=True)

    
def generate_context(ALL_FILTER, SAVE_PATH):
    context(ALL_FILTER, SAVE_PATH)
    hashtags(ALL_FILTER, SAVE_PATH)