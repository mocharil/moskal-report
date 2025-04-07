from chart_generator.functions import *

from dotenv import load_dotenv

load_dotenv()  
BQ = About_BQ(project_id= os.getenv("BQ_PROJECT_ID") ,
         credentials_loc= os.getenv("BQ_CREDS_LOCATION")  )
def create_sentiment_distribution_chart(df, title="Sentiment Distribution by Entity", figsize=(20, 15)):

    # Convert to DataFrame and sort by total mentions
    df = df.sort_values('total_mentions')
    
    # Create figure with two subplots (left for labels, right for chart)
    fig, (ax_labels, ax) = plt.subplots(1, 2, figsize=figsize, 
                                        gridspec_kw={'width_ratios': [1, 4]})
    
    # Set background color to white
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    ax_labels.set_facecolor('white')
    
    # Create horizontal bars in the right subplot
    y_pos = np.arange(len(df))
    bar_height = 0.6  # Thinner bars
    
    # Plot negative mentions (left side)
    negative_bars = ax.barh(y_pos, -df['negative_mentions'], height=bar_height, 
                           align='center', color='#FF9999', zorder=3)
    
    # Plot positive mentions (right side)
    positive_bars = ax.barh(y_pos, df['positive_mentions'], height=bar_height, 
                           align='center', color='#8fdfa8', zorder=3)
    
    # Add entity labels in the left subplot
    for i, entity in enumerate(df['object_item']):
        # Add light gray background for entity names
        entity_bg = patches.Rectangle((0, i-0.3), 1, 0.6, 
                                     facecolor='#f0f0f0', 
                                     edgecolor=None,
                                     zorder=1)
        ax_labels.add_patch(entity_bg)
        
        # Add entity name
        ax_labels.text(0.05, i, entity, va='center', fontsize=16, zorder=4)
    
    # Add value labels to the main chart
    for i, (pos, neg) in enumerate(zip(df['positive_mentions'], df['negative_mentions'])):
        if pos > 0:
            ax.text(pos + 3, i, f"{int(pos)} ({df['positive_percentage'].iloc[i]:.1f}%)", 
                    va='center', color='#228B22', fontsize=16, zorder=4)
        if neg > 0:
            ax.text(-neg - 3, i, f"{int(neg)} ({df['negative_percentage'].iloc[i]:.1f}%)", 
                    va='center', ha='right', color='#B22222', fontsize=16, zorder=4)
        elif neg == 0:
            ax.text(-3, i, f"{int(neg)} ({df['negative_percentage'].iloc[i]:.1f}%)", 
                    va='center', ha='right', color='#B22222', fontsize=16, zorder=4)
    
    # Create symmetrical x-axis for the main chart
    max_value = max(df['positive_mentions'].max(), df['negative_mentions'].max())
    buffer = max_value * 0.15  # Add some buffer space
    ax.set_xlim(-max_value - buffer, max_value + buffer)
    
    # Format x-axis with custom tick locations
    ticks = [tick for tick in range(-350, 351, 50) if tick != 0]
    ax.set_xticks(ticks)
    ax.set_xticklabels([str(abs(tick)) for tick in ticks])
    
    # Remove ticks from both subplots
    ax.set_yticks([])
    ax_labels.set_yticks([])
    ax_labels.set_xticks([])
    
    # Set limits for the labels subplot
    ax_labels.set_xlim(0, 1)
    ax_labels.set_ylim(-0.5, len(df) - 0.5)
    
    # Add a center line to the main chart
    ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8, zorder=2)
    
    # Remove all spines
    for spine in ax.spines.values():
        spine.set_visible(False)
    for spine in ax_labels.spines.values():
        spine.set_visible(False)
    
    # Labels for the main chart
    ax.set_xlabel('Number of mentions', fontsize=16, labelpad=10)
    
    # Add labels for the sides
    fig.text(0.35, 0.062, 'Negative mentions', ha='center', color='#B22222', fontsize=16)
    fig.text(0.75, 0.062, 'Positive mentions', ha='center', color='#228B22', fontsize=16)
    
    # Ensure no space between subplots
    plt.subplots_adjust(wspace=0)
    
    # Adjust layout and add more padding at the bottom
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    
    return fig, ax_labels, ax

def generate_object(ALL_FILTER, SAVE_PATH):
    query = f"""WITH split_objects AS (
      SELECT 
        TRIM(LOWER(object_item)) AS object_item,
        c.sentiment
      FROM 
        medsos.post_category c
      JOIN
        medsos.post_analysis a
      ON 
        c.link_post = a.link_post
      CROSS JOIN
        UNNEST(SPLIT(c.object, ',')) AS object_item
      WHERE 
    {ALL_FILTER}
        AND c.object IS NOT NULL
        AND c.channel not in ('news')
    )
    SELECT
      object_item,
      COUNT(*) AS total_mentions,
      COUNTIF(sentiment = 'positive') AS positive_mentions,
      COUNTIF(sentiment = 'negative') AS negative_mentions,
      COUNTIF(sentiment = 'neutral') AS neutral_mentions,
      ROUND(COUNTIF(sentiment = 'positive') / COUNT(*) * 100, 1) AS positive_percentage,
      ROUND(COUNTIF(sentiment = 'negative') / COUNT(*) * 100, 1) AS negative_percentage,
      ROUND(COUNTIF(sentiment = 'neutral') / COUNT(*) * 100, 1) AS neutral_percentage
    FROM 
      split_objects
    WHERE 
      LENGTH(TRIM(object_item)) > 0
    GROUP BY 
      object_item
    ORDER BY 
      total_mentions DESC
    LIMIT 
      10
    """
    df = BQ.to_pull_data(query)
    fig, ax_labels, ax  = create_sentiment_distribution_chart(df)
    save_file = os.path.join(SAVE_PATH, 'sentiment_distribution_by_entity.png')
    plt.savefig(save_file, dpi=300, bbox_inches='tight', transparent=True)
