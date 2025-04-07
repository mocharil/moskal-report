from chart_generator.functions import *

from dotenv import load_dotenv

load_dotenv()  
BQ = About_BQ(project_id= os.getenv("BQ_PROJECT_ID") ,
         credentials_loc= os.getenv("BQ_CREDS_LOCATION")  )


############### METRICS ###############    
def get_time_series(FILTER_KEYWORD, START_DATE, END_DATE, prev_start_date, prev_end_date):
    diff_date = range_date_count(START_DATE, END_DATE)
    query = f"""WITH 
        -- Define the date ranges
        date_ranges AS (
            SELECT 
                DATE('{START_DATE}') AS current_start_date,
                DATE('{END_DATE}') AS current_end_date,
                DATE('{prev_start_date}') AS previous_start_date,
                DATE('{prev_end_date}') AS previous_end_date
        ),

        -- Time series data for mentions - CURRENT PERIOD
        mentions_time_series AS (
            SELECT 
                DATE(a.post_created_at) as date,
                COUNT(*) as value,
                'current' as period
            FROM `medsos.post_analysis` a
            JOIN `medsos.post_category` c
            ON a.link_post = c.link_post
            CROSS JOIN date_ranges d
            WHERE DATE(a.post_created_at) BETWEEN d.current_start_date AND d.current_end_date
            AND {FILTER_KEYWORD}
            GROUP BY date
            ORDER BY date
        ),

        -- Time series data for mentions - PREVIOUS PERIOD
        mentions_time_series_prev AS (
            SELECT 
                DATE_ADD(DATE(a.post_created_at), INTERVAL {diff_date} DAY) as date, -- Shift dates to align with current period
                COUNT(*) as value,
                'previous' as period
            FROM `medsos.post_analysis` a
            JOIN `medsos.post_category` c
            ON a.link_post = c.link_post
            CROSS JOIN date_ranges d
            WHERE DATE(a.post_created_at) BETWEEN d.previous_start_date AND d.previous_end_date
            AND {FILTER_KEYWORD}
            GROUP BY date
            ORDER BY date
        ),

        -- Social reach time series - CURRENT PERIOD
        social_reach_time_series AS (
            SELECT 
                DATE(a.post_created_at) as date,
                SUM(a.reach_score) as value,
                'current' as period
            FROM `medsos.post_analysis` a
            JOIN `medsos.post_category` c
            ON a.link_post = c.link_post
            CROSS JOIN date_ranges d
            WHERE DATE(a.post_created_at) BETWEEN d.current_start_date AND d.current_end_date
            AND {FILTER_KEYWORD}
            AND a.channel != 'news'
            GROUP BY date
            ORDER BY date
        ),

        -- Social reach time series - PREVIOUS PERIOD
        social_reach_time_series_prev AS (
            SELECT 
                DATE_ADD(DATE(a.post_created_at), INTERVAL {diff_date} DAY) as date,
                SUM(a.reach_score) as value,
                'previous' as period
            FROM `medsos.post_analysis` a
            JOIN `medsos.post_category` c
            ON a.link_post = c.link_post
            CROSS JOIN date_ranges d
            WHERE DATE(a.post_created_at) BETWEEN d.previous_start_date AND d.previous_end_date
            AND {FILTER_KEYWORD}
            AND a.channel != 'news'
            GROUP BY date
            ORDER BY date
        ),

        -- Non-social reach time series - CURRENT PERIOD
        non_social_reach_time_series AS (
            SELECT 
                DATE(a.post_created_at) as date,
                SUM(a.reach_score) as value,
                'current' as period
            FROM `medsos.post_analysis` a
            JOIN `medsos.post_category` c
            ON a.link_post = c.link_post
            CROSS JOIN date_ranges d
            WHERE DATE(a.post_created_at) BETWEEN d.current_start_date AND d.current_end_date
            AND {FILTER_KEYWORD}
            AND a.channel = 'news'
            GROUP BY date
            ORDER BY date
        ),

        -- Non-social reach time series - PREVIOUS PERIOD
        non_social_reach_time_series_prev AS (
            SELECT 
                DATE_ADD(DATE(a.post_created_at), INTERVAL {diff_date} DAY) as date,
                SUM(a.reach_score) as value,
                'previous' as period
            FROM `medsos.post_analysis` a
            JOIN `medsos.post_category` c
            ON a.link_post = c.link_post
            CROSS JOIN date_ranges d
            WHERE DATE(a.post_created_at) BETWEEN d.previous_start_date AND d.previous_end_date
            AND {FILTER_KEYWORD}
            AND a.channel = 'news'
            GROUP BY date
            ORDER BY date
        ),

        -- Positive sentiment time series - CURRENT PERIOD
        positive_time_series AS (
            SELECT 
                DATE(a.post_created_at) as date,
                COUNT(*) as value,
                'current' as period
            FROM `medsos.post_analysis` a
            JOIN `medsos.post_category` c
            ON a.link_post = c.link_post
            CROSS JOIN date_ranges d
            WHERE DATE(a.post_created_at) BETWEEN d.current_start_date AND d.current_end_date
            AND {FILTER_KEYWORD}
            AND c.sentiment = 'positive'
            GROUP BY date
            ORDER BY date
        ),

        -- Positive sentiment time series - PREVIOUS PERIOD
        positive_time_series_prev AS (
            SELECT 
                DATE_ADD(DATE(a.post_created_at), INTERVAL {diff_date} DAY) as date,
                COUNT(*) as value,
                'previous' as period
            FROM `medsos.post_analysis` a
            JOIN `medsos.post_category` c
            ON a.link_post = c.link_post
            CROSS JOIN date_ranges d
            WHERE DATE(a.post_created_at) BETWEEN d.previous_start_date AND d.previous_end_date
            AND {FILTER_KEYWORD}
            AND c.sentiment = 'positive'
            GROUP BY date
            ORDER BY date
        ),

        -- Negative sentiment time series - CURRENT PERIOD
        negative_time_series AS (
            SELECT 
                DATE(a.post_created_at) as date,
                COUNT(*) as value,
                'current' as period
            FROM `medsos.post_analysis` a
            JOIN `medsos.post_category` c
            ON a.link_post = c.link_post
            CROSS JOIN date_ranges d
            WHERE DATE(a.post_created_at) BETWEEN d.current_start_date AND d.current_end_date
            AND {FILTER_KEYWORD}
            AND c.sentiment = 'negative'
            GROUP BY date
            ORDER BY date
        ),

        -- Negative sentiment time series - PREVIOUS PERIOD
        negative_time_series_prev AS (
            SELECT 
                DATE_ADD(DATE(a.post_created_at), INTERVAL {diff_date} DAY) as date,
                COUNT(*) as value,
                'previous' as period
            FROM `medsos.post_analysis` a
            JOIN `medsos.post_category` c
            ON a.link_post = c.link_post
            CROSS JOIN date_ranges d
            WHERE DATE(a.post_created_at) BETWEEN d.previous_start_date AND d.previous_end_date
            AND {FILTER_KEYWORD}
            AND c.sentiment = 'negative'
            GROUP BY date
            ORDER BY date
        ),

        -- Combine current and previous for each metric
        mentions_combined AS (
            SELECT * FROM mentions_time_series
            UNION ALL
            SELECT * FROM mentions_time_series_prev
        ),

        social_reach_combined AS (
            SELECT * FROM social_reach_time_series
            UNION ALL
            SELECT * FROM social_reach_time_series_prev
        ),

        non_social_reach_combined AS (
            SELECT * FROM non_social_reach_time_series
            UNION ALL
            SELECT * FROM non_social_reach_time_series_prev
        ),

        positive_combined AS (
            SELECT * FROM positive_time_series
            UNION ALL
            SELECT * FROM positive_time_series_prev
        ),

        negative_combined AS (
            SELECT * FROM negative_time_series
            UNION ALL
            SELECT * FROM negative_time_series_prev
        )

    SELECT
        (SELECT ARRAY_AGG(STRUCT(date, value, period)) FROM mentions_combined) as mentions_time_series,
        (SELECT ARRAY_AGG(STRUCT(date, value, period)) FROM social_reach_combined) as social_reach_time_series,
        (SELECT ARRAY_AGG(STRUCT(date, value, period)) FROM non_social_reach_combined) as non_social_reach_time_series,
        (SELECT ARRAY_AGG(STRUCT(date, value, period)) FROM positive_combined) as positive_time_series,
        (SELECT ARRAY_AGG(STRUCT(date, value, period)) FROM negative_combined) as negative_time_series"""

    return BQ.to_pull_data(query)

def generate_mentions_chart(title,data, current_mentions, previous_mentions, mentions_percent_change, SAVE_PATH = 'PPT'):
    # Extract date and values
    dates = [datetime.strptime(d['date'], '%Y-%m-%d') for d in data]
    values = [d['value'] for d in data]

    # Convert datetime to numeric for interpolation
    x = np.arange(len(dates))
    y = np.array(values)

    # Smoothing using B-spline
    x_smooth = np.linspace(x.min(), x.max(), 300)
    spline = make_interp_spline(x, y, k=3)
    y_smooth = spline(x_smooth)

    # Convert x_smooth back to datetime scale
    date_smooth = np.interp(x_smooth, x, [d.timestamp() for d in dates])
    date_smooth = [datetime.fromtimestamp(ts) for ts in date_smooth]

    # Figure setup
    fig, ax = plt.subplots(figsize=(5, 5), dpi=100)

    # Plot the smooth line
    color='#1a73e8'
    color_fill = '#b9cdeb'
    if title =='Positive':
        color = 'green'
        color_fill = '#cbf5d4'
    elif title == 'Negative':
        color='red'
        color_fill = '#f5cccb'

    ax.plot(date_smooth, y_smooth, color=color, linewidth=2, zorder=2)

    # Gradient fill
    ax.fill_between(date_smooth, y_smooth, [min(y)]*len(y_smooth),
                    color=color_fill, alpha=0.1, zorder=1)

    # Clean styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.tick_params(left=False, bottom=False)
    ax.set_xticks([])
    ax.set_yticks([])

    # Delta calculation
    delta = current_mentions - previous_mentions
    is_positive = delta >= 0
    delta_color = 'green' if is_positive else 'red'
    delta_sign = '+' if is_positive else ''

    # Text info
    ax.text(0.03, -0.2, title, transform=ax.transAxes,
            fontsize=26, color='#5f6368')
    ax.text(0.03, -0.39, f"{current_mentions:,}", transform=ax.transAxes,
            fontsize=25, color='#202124', weight = 'bold')
    ax.text(0.03, -0.55, f"{delta_sign}{delta:,} ({delta_sign}{round(mentions_percent_change)}%)",
            transform=ax.transAxes, fontsize=18, color=delta_color, weight = 'bold')

    plt.tight_layout()
    
    save_file = os.path.join(SAVE_PATH, f"{title.lower().replace(' ', '_')}.png")
    
    plt.savefig(save_file, bbox_inches='tight', dpi=150, transparent=True)

def plot_current_vs_previous_period(data, title="Current vs Previous Period", save_path=None, show_dots=True):
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    
    
    color_theme = '#1a73e8'
    
    if 'negative' in title.lower():
        color_theme = 'red'
    if 'positive' in title.lower():
        color_theme = 'green'

    # Pivot table
    pivot_df = df.pivot_table(index='date', columns='period', values='value', aggfunc='sum').sort_index().fillna(0)

    # Raw data
    x_current = pivot_df.index
    y_current = pivot_df['current'].values
    x_previous = pivot_df.index
    y_previous = pivot_df['previous'].values

    # Smoothing only for plotting
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

    x_smooth_current, y_smooth_current = smooth(x_current, y_current)
    x_smooth_previous, y_smooth_previous = smooth(x_previous, y_previous)

    fig, ax = plt.subplots(figsize=(13.13, 3.60))  # 33.35cm x 9.14cm

    # Chart styling
    ax.set_facecolor('#fcfdff')
    fig.patch.set_facecolor('#ffffff')

    # Plot smooth lines
    ax.plot(x_smooth_current, y_smooth_current, color=color_theme, label='Current period', linewidth=2)
    ax.plot(x_smooth_previous, y_smooth_previous, color=color_theme, linestyle='--', label='Previous period', alpha=0.6, linewidth=1.5)

    # Plot dots for real data points (optional)
    if show_dots:
        ax.scatter(x_current, y_current, color=color_theme, s=15, zorder=3)
        ax.scatter(x_previous, y_previous, color=color_theme, s=15, alpha=0.5, zorder=3)
        
    # Remove box frame
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Axis styling
    ax.tick_params(axis='y', colors=color_theme)
    ax.yaxis.label.set_color(color_theme)
    ax.grid(axis='y', linestyle='-', linewidth=0.5, alpha=0.3)

    ax.xaxis.set_major_formatter(DateFormatter('%d %b'))
    plt.xticks(rotation=0)
    ax.xaxis.label.set_color('#5f6368')

    # Annotate peaks from raw values
    def annotate_peak(x_vals, y_vals, kind='current'):
        idx = np.argmax(y_vals)
        peak_x = x_vals[idx]
        peak_y = y_vals[idx]
        if kind == 'previous':
            label = f"{int(round(peak_y))} mentions on {(peak_x - timedelta(days=len(pivot_df))).strftime('%d %b %Y')}"
        else:
            label = f"{int(round(peak_y))} mentions on {peak_x.strftime('%d %b %Y')}"
        ax.annotate(label, xy=(peak_x, peak_y), xytext=(peak_x, peak_y + 2),
                    ha='center', fontsize=9, color=color_theme,
                    arrowprops=dict(arrowstyle='-', color=color_theme, lw=1))

    annotate_peak(x_current, y_current)
    annotate_peak(x_previous, y_previous, kind='previous')

    # Legend below chart
    ax.legend(
        loc='upper center',
        bbox_to_anchor=(0.1, -0.3),
        ncol=2,
        frameon=False
    )

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150, transparent=True)

def generate_metrics_chart(ALL_FILTER, FILTER_KEYWORD,FILTER_DATE, START_DATE, 
                           END_DATE, prev_start_date, prev_end_date, SAVE_PATH = 'PPT'):
    
    metrics_data_time_series = get_time_series(FILTER_KEYWORD, START_DATE, END_DATE, prev_start_date, prev_end_date)

    metrics_chart_config = {
        'mentions': ('Volume of mentions','mentions_time_series', 'current_mentions', 'previous_mentions', 'mentions_percent_change'),
        'social_reach': ('Social media reach','social_reach_time_series', 'current_social_reach', 'previous_social_reach', 'social_reach_percent_change'),
        'non_social_reach': ('Non social media reach','non_social_reach_time_series', 'current_non_social_reach', 'previous_non_social_reach', 'non_social_reach_percent_change'),
        'positive': ('Positive','positive_time_series', 'current_positive', 'previous_positive', 'positive_percent_change'),
        'negative': ('Negative','negative_time_series', 'current_negative', 'previous_negative', 'negative_percent_change'),
    }

    # Generate all charts
        
    for metric, (title,ts_col, current_key, prev_key, change_key) in metrics_chart_config.items():

        time_series = metrics_data_time_series[ts_col].tolist()
        time_series = pd.DataFrame([j for i in time_series for j in i])
        time_series['date'] = time_series['date'].astype(str)

        values = time_series[time_series['period']=='current']
        current_val = values['value'].sum()
        previous_val = time_series[time_series['period']=='previous']['value'].sum()
        percent_change = ((current_val - previous_val) / previous_val) * 100

        generate_mentions_chart(title,
                                values[['date','value']].sort_values('date').to_dict(orient = 'records'),
                                current_mentions = int(current_val),
                                previous_mentions = int(previous_val),
                                mentions_percent_change = percent_change,
                               SAVE_PATH = SAVE_PATH)

        save_file = os.path.join(SAVE_PATH,f"{title}_trend.png")
        plot_current_vs_previous_period(time_series, title=f"{title} Trend", save_path=save_file)        
        
        
        
        
        
        
        
        
        
        
        
        
        
  