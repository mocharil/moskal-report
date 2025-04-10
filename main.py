import os, re, time, logging
from chart_generator.functions import *
from dotenv import load_dotenv
from typing import Optional
from datetime import datetime
from report_generator.slider import *
from utils.functions import format_range_date, upload_and_get_public_url
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import subprocess
from pathlib import Path
import shutil
from utils.send_email import send_email

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="PPT Generator API")

def create_ppt(prs, topic, RANGE_DATE, SAVE_FILE, SAVE_PATH):
    slide_cover(prs, topic, RANGE_DATE, SAVE_FILE)
    logger.info("Creating slide 2: Summary mentions...")
    slide_summary_mentions(prs, topic, RANGE_DATE, SAVE_FILE, page_number=2, SOURCE=SAVE_PATH)
    logger.info("Creating slide 3: Reach trend...")
    slide_reach_trend(prs, topic, RANGE_DATE, SAVE_FILE, page_number=3, SOURCE=SAVE_PATH)
    logger.info("Creating slide 4: Sentiment trend...")
    slide_sentiment_trend(prs, topic, RANGE_DATE, SAVE_FILE, page_number=4, SOURCE=SAVE_PATH)
    logger.info("Creating slide 5: Topic overview...")
    slide_topic_overview(prs, topic, RANGE_DATE, SAVE_FILE, page_number=5, SOURCE=SAVE_PATH)
    logger.info("Creating slide 6: KOL analysis...")
    slide_kol(prs, topic, RANGE_DATE, SAVE_FILE, page_number=6, SOURCE=SAVE_PATH)
    logger.info("Creating slide 8: Presence score...")
    slide_presence_score(prs, topic, RANGE_DATE, SAVE_FILE, page_number=8, SOURCE=SAVE_PATH)
    logger.info("Creating slide 9: Sentiment analysis...")
    slide_sentiment_analysis(prs, topic, RANGE_DATE, SAVE_FILE, page_number=9, SOURCE=SAVE_PATH)
    logger.info("Creating slide 10: Sentiment context...")
    slide_sentiment_context(prs, topic, RANGE_DATE, SAVE_FILE, page_number=10, SOURCE=SAVE_PATH)
    logger.info("Creating slide 11: Popular mentions...")
    slide_popular_mentions(prs, topic, RANGE_DATE, SAVE_FILE, page_number=11, SOURCE=SAVE_PATH)
    logger.info("Creating slide 12: Recommendations...")
    slide_recommendations(prs, topic, RANGE_DATE, SAVE_FILE, page_number=12, SOURCE=SAVE_PATH)

def generate_filename(topic: str, start_date: str, end_date: str, ext: str = "pptx") -> str:
    # Lowercase dan ganti spasi dengan underscore
    cleaned_topic = topic.strip().lower()
    cleaned_topic = re.sub(r"[^\w\s-]", "", cleaned_topic)  # Hilangkan karakter aneh
    cleaned_topic = re.sub(r"\s+", "_", cleaned_topic)      # Ganti spasi jadi underscore

    filename = f"{cleaned_topic}_{start_date}_to_{end_date}.{ext}"
    return filename

@app.get("/")
def read_root():
    return {"message": "PPT Generator API is running"}

@app.post("/generate-report")
async def generate_report(topic: str, start_date: str, end_date: str, email_receiver: Optional[str] = None):
    start_time = time.time()
    logger.info(f"Starting report generation for topic: {topic}")
    # try:
    logger.info("Validating dates...")
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    logger.info("Loading environment variables...")
    load_dotenv()

    logger.info("Initializing BigQuery client...")
    BQ = About_BQ(
        project_id=os.getenv("BQ_PROJECT_ID"),
        credentials_loc=os.getenv("BQ_CREDS_LOCATION")
    )

    logger.info("Calculating date ranges...")
    diff_date = range_date_count(start_date, end_date)
    prev_start_date = kurangi_tanggal(start_date, diff_date+1)
    prev_end_date = kurangi_tanggal(end_date, diff_date+1)

    logger.info("Setting up save path...")
    
    SAVE_PATH = os.path.join('REPORT', topic, f"{start_date} - {end_date}")
    if not os.path.isdir(SAVE_PATH):
        os.makedirs(SAVE_PATH)

    logger.info("Generating keywords and filters...")
    KEYWORDS = generate_keywords(topic, f"{start_date} - {end_date}")
    print(KEYWORDS)
    FILTER_KEYWORD = []
    for key in KEYWORDS:
        keyword = re.sub(f"[^a-z0-9\s]", " ", key.lower().strip(" -"))
        FILTER_KEYWORD.append(f"""SEARCH(lower(a.post_caption), '{keyword}')""")
    FILTER_KEYWORD = '(' + ' OR '.join(FILTER_KEYWORD) + ')'
    FILTER_KEYWORD = FILTER_KEYWORD.replace('\u2060', '')

    FILTER_DATE = f"""a.post_created_at BETWEEN '{start_date}' AND '{end_date}'"""
    ALL_FILTER = f"{FILTER_DATE} AND {FILTER_KEYWORD}"

    # Generate all charts
    logger.info("Starting chart generation process...")
    
    logger.info("1/9: Generating metrics chart...")
    from chart_generator.metrics import generate_metrics_chart
    generate_metrics_chart(ALL_FILTER, FILTER_KEYWORD, FILTER_DATE,
                        start_date, end_date, prev_start_date, prev_end_date, SAVE_PATH)

    logger.info("2/9: Generating topic overview...")
    from chart_generator.topics import generate_topic_overview
    generate_topic_overview(ALL_FILTER, topic, SAVE_PATH)

    logger.info("3/9: Generating KOL analysis...")
    from chart_generator.kol import generate_kol
    generate_kol(topic, ALL_FILTER, SAVE_PATH)

    logger.info("4/9: Generating presence score...")
    from chart_generator.presence_score import generatre_presence_score
    generatre_presence_score(topic, ALL_FILTER, FILTER_KEYWORD, SAVE_PATH)

    logger.info("5/9: Generating object analysis...")
    from chart_generator.object import generate_object
    generate_object(ALL_FILTER, SAVE_PATH)

    logger.info("6/9: Generating context analysis...")
    from chart_generator.context import generate_context
    generate_context(ALL_FILTER, SAVE_PATH)

    logger.info("7/9: Generating sentiment analysis...")
    from chart_generator.sentiment import generate_sentiment_analysis
    generate_sentiment_analysis(topic, ALL_FILTER, SAVE_PATH)

    logger.info("8/9: Generating popular mentions...")
    from chart_generator.mentions import generate_popular_mentions
    generate_popular_mentions(ALL_FILTER, SAVE_PATH)

    logger.info("9/9: Generating recommendations...")
    from chart_generator.recommendations import generate_recommendations
    generate_recommendations(topic, start_date, end_date, ALL_FILTER, SAVE_PATH)

    logger.info("Starting PowerPoint generation...")
    RANGE_DATE = format_range_date(start_date, end_date)

    FILENAME = generate_filename(topic, start_date, end_date, ext = "pptx")
    SAVE_FILE = os.path.join(SAVE_PATH, FILENAME)
    


    prs = Presentation()

    logger.info("Creating slide 1: Cover...")
    create_ppt(prs, topic, RANGE_DATE, SAVE_FILE, SAVE_PATH)
    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"Report generation completed in {duration:.2f} seconds")


    logger.info(f"Uplaod to GCS auto-report")

    # Path ke file kredensial JSON
    json_credentials = 'inlaid-sentinel-444404-f8-be06a73c1031.json' # Ganti dengan path kredensial Anda
    # Upload file dan jadikan publik
    public_url = upload_and_get_public_url(
                                    local_file_path = SAVE_FILE,
                                    credentials_json_path = os.getenv("GCS_CREDS_LOCATION"),
                                    project_id= os.getenv("GCS_PROJECT_ID"),
                                    bucket_name = os.getenv("GCS_BUCKET_NAME")
                                )
    print(f"File dapat diakses publik di: {public_url}")

    if email_receiver:
        logger.info(f"Send Email...")
        
        send_email(SAVE_FILE, email_receiver, topic, RANGE_DATE)

        logger.info(f"Send Email Success")

    logger.info(f"Upload Success")

    return JSONResponse(
        content={
            "status": "success",
            "message": "Report generated successfully",
            "data": {
                "report_path": SAVE_FILE,
                "topic": topic,
                "start_date": start_date,
                "end_date": end_date,
                "url":public_url["signed_url"]
            }
        },
        status_code=200
    )

    # except Exception as e:
    #     logger.error(f"Error during report generation: {str(e)}")
    #     raise HTTPException(status_code=500, detail=str(e))


@app.post("/test")
async def teste(topic: str, start_date: str, end_date: str):

        SAVE_FILE = "C://Users//Aril Indra Permana//Moskal Project//report//REPORT//megawati//2025-01-01 - 2025-03-01//report.pptx"
        FILE_PDF = SAVE_FILE.replace(".pptx", ".pdf")
        print(convert_to_pdf(SAVE_FILE, FILE_PDF))

        return JSONResponse(
            content={
                "status": "success",
                "message": "Report generated successfully",
                "data": {
                    "report_path": SAVE_FILE,
                    "topic": topic,
                    "start_date": start_date,
                    "end_date": end_date,
                    "pdf_file":FILE_PDF
                }
            },
            status_code=200
        )           


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
