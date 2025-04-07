import time
start_time = time.time()
from chart_generator.functions import *
from dotenv import load_dotenv

load_dotenv()  
print('-----------------------------------')
print(os.getenv("BQ_PROJECT_ID") )
print(os.getenv("BQ_CREDS_LOCATION"))
print('-----------------------------------')
BQ = About_BQ(project_id="inlaid-sentinel-444404-f8", credentials_loc='inlaid-sentinel-444404-f8-be06a73c1031.json')

BQ = About_BQ(project_id= os.getenv("BQ_PROJECT_ID") ,  credentials_loc= os.getenv("BQ_CREDS_LOCATION") )

###############################################################################################
# =========================================== INPUT ===========================================
###############################################################################################
TOPIC = "anies"
START_DATE = "2025-01-01"
END_DATE = "2025-03-01"

###############################################################################################
# ===================================== KEYWORD GENERATOR =====================================
###############################################################################################

diff_date = range_date_count(START_DATE, END_DATE)
prev_start_date = kurangi_tanggal(START_DATE, diff_date+1)
prev_end_date = kurangi_tanggal(END_DATE, diff_date+1)

SAVE_PATH = os.path.join('REPORT',TOPIC,f"{START_DATE} - {END_DATE}")
if not os.path.isdir(SAVE_PATH):
    print('create new folder', SAVE_PATH)
    os.makedirs(SAVE_PATH)
    
KEYWORDS = generate_keywords(TOPIC, f"{START_DATE} - {END_DATE}")

FILTER_KEYWORD = []
for key in KEYWORDS:
    keyword = re.sub(f"[^a-z0-9\s]"," ",key.lower().strip(" -"))
    FILTER_KEYWORD.append(f"""SEARCH(lower(a.post_caption), '{keyword}')""")
FILTER_KEYWORD = '('+' OR '.join(FILTER_KEYWORD)+')'
FILTER_KEYWORD = FILTER_KEYWORD.replace('\u2060','')

FILTER_DATE = f"""a.post_created_at BETWEEN '{START_DATE}' AND '{END_DATE}'"""
ALL_FILTER = f"{FILTER_DATE} AND {FILTER_KEYWORD}"
print(KEYWORDS)


###############################################################################################
# ======================================= CHART GENERATOR =====================================
###############################################################################################

from chart_generator.metrics import generate_metrics_chart
generate_metrics_chart(ALL_FILTER, FILTER_KEYWORD, FILTER_DATE,
                       START_DATE, END_DATE, prev_start_date, prev_end_date, SAVE_PATH)

from chart_generator.topics import generate_topic_overview
generate_topic_overview(ALL_FILTER, TOPIC, SAVE_PATH)

from chart_generator.kol import generate_kol
generate_kol(TOPIC,ALL_FILTER, SAVE_PATH)

from chart_generator.presence_score import generatre_presence_score
generatre_presence_score(TOPIC, ALL_FILTER, FILTER_KEYWORD, SAVE_PATH)

from chart_generator.object import generate_object
generate_object(ALL_FILTER, SAVE_PATH)

from chart_generator.context import generate_context
generate_context(ALL_FILTER, SAVE_PATH)

from chart_generator.sentiment import generate_sentiment_analysis
generate_sentiment_analysis(TOPIC, ALL_FILTER, SAVE_PATH)

from chart_generator.mentions import generate_popular_mentions
generate_popular_mentions(ALL_FILTER, SAVE_PATH)

from chart_generator.recommendations import generate_recommendations
generate_recommendations(TOPIC, START_DATE, END_DATE, ALL_FILTER, SAVE_PATH)

###############################################################################################
# ===================================== PPT GENERATOR =========================================
###############################################################################################
from report_generator.slider import *
from utils.functions import format_range_date

RANGE_DATE = format_range_date(START_DATE, END_DATE)
SAVE_FILE = os.path.join(SAVE_PATH,"report.pptx")
prs = Presentation()

slide_cover(prs, TOPIC, RANGE_DATE, SAVE_FILE)
slide_summary_mentions(prs, TOPIC, RANGE_DATE, SAVE_FILE, page_number = 2, SOURCE = SAVE_PATH)
slide_reach_trend(prs, TOPIC, RANGE_DATE, SAVE_FILE, page_number = 3, SOURCE = SAVE_PATH)
slide_sentiment_trend(prs, TOPIC, RANGE_DATE, SAVE_FILE, page_number = 4, SOURCE = SAVE_PATH)
slide_topic_overview(prs, TOPIC, RANGE_DATE, SAVE_FILE, page_number = 5, SOURCE = SAVE_PATH)
slide_kol(prs, TOPIC, RANGE_DATE, SAVE_FILE, page_number = 6, SOURCE = SAVE_PATH)
slide_presence_score(prs, TOPIC, RANGE_DATE, SAVE_FILE, page_number = 8, SOURCE = SAVE_PATH)
slide_sentiment_analysis(prs, TOPIC, RANGE_DATE, SAVE_FILE, page_number = 9, SOURCE = SAVE_PATH)
slide_sentiment_context(prs, TOPIC, RANGE_DATE, SAVE_FILE, page_number = 10, SOURCE = SAVE_PATH)
slide_popular_mentions(prs, TOPIC, RANGE_DATE, SAVE_FILE, page_number = 11, SOURCE = SAVE_PATH)
slide_recommendations(prs, TOPIC, RANGE_DATE, SAVE_FILE, page_number = 12, SOURCE = SAVE_PATH)

end_time = time.time()
duration = end_time - start_time

print(f"Durasi eksekusi: {duration:.4f} detik")