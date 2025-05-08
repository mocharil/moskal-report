import os, re, time, logging
from chart_generator.functions import *
from dotenv import load_dotenv
from typing import Optional
from datetime import datetime
from elasticsearch import Elasticsearch
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from report_generator.slider import *
from utils.functions import format_range_date, upload_and_get_public_url
from utils.send_email import send_email
from pptx import Presentation
from chart_generator.metrics import generate_metrics_chart
from chart_generator.topics import generate_topic_overview
from chart_generator.kol import generate_kol
from chart_generator.presence_score import generatre_presence_score
from chart_generator.mentions import generate_popular_mentions
from chart_generator.object import generate_object
from chart_generator.context import generate_context
from chart_generator.sentiment import generate_sentiment_analysis
from chart_generator.recommendations import generate_recommendations
from chart_generator.exsum import generate_executive_summary
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

load_dotenv()

# Configure Elasticsearch
es = Elasticsearch(
    os.getenv('ES_HOST', 'http://localhost:9200'),
    basic_auth=(
        os.getenv('ES_USER', 'elastic'),
        os.getenv('ES_PASSWORD', '')
    )
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="PPT Generator API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def create_ppt(prs, topic, RANGE_DATE, SAVE_FILE, SAVE_PATH):
    start_time = time.time()
    last_step_time = start_time

    def log_slide_time(slide_name: str):
        nonlocal last_step_time
        current_time = time.time()
        step_duration = current_time - last_step_time
        total_duration = current_time - start_time
        logger.info(f"Slide {slide_name}: took {step_duration:.2f}s, total time: {total_duration:.2f}s")
        last_step_time = current_time

    slide_cover(prs, topic, RANGE_DATE, SAVE_FILE)
    log_slide_time("1: Cover")

    slide_summary_mentions(prs, topic, RANGE_DATE, SAVE_FILE, page_number=2, SOURCE=SAVE_PATH)
    log_slide_time("2: Summary mentions")

    slide_reach_trend(prs, topic, RANGE_DATE, SAVE_FILE, page_number=3, SOURCE=SAVE_PATH)
    log_slide_time("3: Reach trend")

    slide_sentiment_trend(prs, topic, RANGE_DATE, SAVE_FILE, page_number=4, SOURCE=SAVE_PATH)
    log_slide_time("4: Sentiment trend")

    slide_topic_overview(prs, topic, RANGE_DATE, SAVE_FILE, page_number=5, SOURCE=SAVE_PATH)
    log_slide_time("5: Topic overview")

    slide_kol(prs, topic, RANGE_DATE, SAVE_FILE, page_number=6, SOURCE=SAVE_PATH)
    log_slide_time("6: KOL analysis")

    slide_presence_score(prs, topic, RANGE_DATE, SAVE_FILE, page_number=8, SOURCE=SAVE_PATH)
    log_slide_time("8: Presence score")

    slide_sentiment_analysis(prs, topic, RANGE_DATE, SAVE_FILE, page_number=9, SOURCE=SAVE_PATH)
    log_slide_time("9: Sentiment analysis")

    slide_sentiment_context(prs, topic, RANGE_DATE, SAVE_FILE, page_number=10, SOURCE=SAVE_PATH)
    log_slide_time("10: Sentiment context")

    slide_popular_mentions(prs, topic, RANGE_DATE, SAVE_FILE, page_number=11, SOURCE=SAVE_PATH)
    log_slide_time("11: Popular mentions")

    slide_recommendations(prs, topic, RANGE_DATE, SAVE_FILE, page_number=12, SOURCE=SAVE_PATH)
    log_slide_time("12: Recommendations")

    slide_executive_summary(prs, topic, RANGE_DATE, SAVE_FILE, page_number=13, SOURCE=SAVE_PATH)
    log_slide_time("13: Executive summary")

def generate_filename(topic: str, start_date: str, end_date: str, ext: str = "pptx") -> str:
    cleaned_topic = topic.strip().lower()
    cleaned_topic = re.sub(r"[^\w\s-]", "", cleaned_topic)
    cleaned_topic = re.sub(r"\s+", "_", cleaned_topic)
    filename = f"{cleaned_topic}_{start_date}_to_{end_date}_{str(time.time()).replace('.','')}.{ext}"
    return filename

def process_report_generation(
    job_id: str,
    topic: str,
    start_date: str,
    end_date: str,
    sub_keyword: str,
    email_receiver: Optional[str],
    background_tasks: BackgroundTasks
):
    try:
        total_start_time = time.time()
        last_step_time = total_start_time
        logger.info(f"Starting report generation for job {job_id}")

        def log_step_time(step_name: str):
            nonlocal last_step_time
            current_time = time.time()
            step_duration = current_time - last_step_time
            total_duration = current_time - total_start_time
            logger.info(f"{step_name}: took {step_duration:.2f}s, total time: {total_duration:.2f}s")
            last_step_time = current_time

        # Update job status to processing
        es.update(
            index="moskal-report-jobs",
            id=job_id,
            body={
                "doc": {
                    "status": "processing",
                    "progress": 0
                }
            }
        )

        diff_date = range_date_count(start_date, end_date)
        prev_start_date = kurangi_tanggal(start_date, diff_date+1)
        prev_end_date = kurangi_tanggal(end_date, diff_date+1)
        
        SAVE_PATH = os.path.join('REPORT', topic, f"{start_date} - {end_date}", str(time.time()).replace('.',''))
        if not os.path.isdir(SAVE_PATH):
            os.makedirs(SAVE_PATH)

        KEYWORDS = [k.strip() for k in sub_keyword.split(",") if k.strip()] if sub_keyword else []
        KEYWORDS.append(topic)

        FILTER_KEYWORD = []
        for key in KEYWORDS:
            keyword = re.sub(f"[^a-z0-9\s]", " ", key.lower().strip(" -"))
            FILTER_KEYWORD.append(f"""SEARCH(lower(a.post_caption), '{keyword}')""")
        FILTER_KEYWORD = '(' + ' OR '.join(FILTER_KEYWORD) + ')'
        FILTER_KEYWORD = FILTER_KEYWORD.replace('\u2060', '')

        FILTER_DATE = f"""a.post_created_at BETWEEN '{start_date}' AND '{end_date}'"""
        ALL_FILTER = f"{FILTER_DATE} AND {FILTER_KEYWORD}"

        # Generate charts with progress updates
        total_steps = 10
        current_step = 0

        def update_progress(step: int, total: int):
            progress = int((step / total) * 100)
            es.update(
                index="moskal-report-jobs",
                id=job_id,
                body={
                    "doc": {
                        "progress": progress
                    }
                }
            )

        # Generate all charts
        generate_metrics_chart(KEYWORDS, start_date, end_date, prev_start_date, prev_end_date, SAVE_PATH)
        current_step += 1
        update_progress(current_step, total_steps)
        log_step_time("Metrics chart generation")

        
        generate_topic_overview(topic, KEYWORDS, start_date, end_date, SAVE_PATH)
        current_step += 1
        update_progress(current_step, total_steps)
        log_step_time("Topic overview generation")

        
        generate_kol(topic, KEYWORDS, start_date, end_date, SAVE_PATH)
        current_step += 1
        update_progress(current_step, total_steps)
        log_step_time("KOL analysis generation")

        
        generatre_presence_score(topic, KEYWORDS, start_date, end_date, SAVE_PATH)
        current_step += 1
        update_progress(current_step, total_steps)
        log_step_time("Presence score generation")

        
        generate_object(KEYWORDS, start_date, end_date, limit=10, SAVE_PATH=SAVE_PATH)
        current_step += 1
        update_progress(current_step, total_steps)
        log_step_time("Object analysis generation")

        
        generate_context(KEYWORDS, start_date, end_date, SAVE_PATH)
        current_step += 1
        update_progress(current_step, total_steps)
        log_step_time("Context analysis generation")

        
        generate_sentiment_analysis(topic, KEYWORDS, start_date, end_date, SAVE_PATH)
        current_step += 1
        update_progress(current_step, total_steps)
        log_step_time("Sentiment analysis generation")

        
        generate_popular_mentions(topic,KEYWORDS, start_date, end_date, SAVE_PATH)
        current_step += 1
        update_progress(current_step, total_steps)
        log_step_time("Popular mentions generation")

        
        generate_recommendations(topic, start_date, end_date, SAVE_PATH)
        current_step += 1
        update_progress(current_step, total_steps)
        log_step_time("Recommendations generation")

        
        summary = generate_executive_summary(topic, start_date, end_date, SAVE_PATH)
        current_step += 1
        update_progress(current_step, total_steps)
        log_step_time("Executive summary generation")

        # Generate PowerPoint
        RANGE_DATE = format_range_date(start_date, end_date)
        FILENAME = generate_filename(topic, start_date, end_date, ext="pptx")
        SAVE_FILE = os.path.join(SAVE_PATH, FILENAME)
        prs = Presentation()
        create_ppt(prs, topic, RANGE_DATE, SAVE_FILE, SAVE_PATH)
        log_step_time("PowerPoint generation")

        # Upload to GCS
        public_url = upload_and_get_public_url(
            local_file_path=SAVE_FILE,
            credentials_json_path=os.getenv("GCS_CREDS_LOCATION"),
            project_id=os.getenv("GCS_PROJECT_ID"),
            bucket_name=os.getenv("GCS_BUCKET_NAME")
        )

        # Start background task for email sending if requested
        if email_receiver:
            background_tasks.add_task(
                send_email,
                SAVE_FILE,
                email_receiver,
                topic,
                RANGE_DATE
            )

        end_time = time.time()
        duration = end_time - total_start_time

        log_step_time("GCS upload")

        # Store final report data
        report_data = {
            "topic": topic,
            "start_date": start_date,
            "end_date": end_date,
            "duration_seconds": duration,
            "filename": FILENAME,
            "public_url": public_url["signed_url"],
            "keywords": KEYWORDS,
            "email_receiver": email_receiver,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summary": summary or "Summary not available"
        }

        es.index(index="moskal-reports", document=report_data)

        # Update job status to completed
        es.update(
            index="moskal-report-jobs",
            id=job_id,
            body={
                "doc": {
                    "status": "completed",
                    "progress": 100,
                    "result": {
                        "report_path": SAVE_FILE,
                        "url": public_url["signed_url"]
                    }
                }
            }
        )

    except Exception as e:
        import traceback
        error_info = traceback.format_exc()
        error_location = error_info.split('\n')[-2] if error_info else 'Unknown location'
        
        # Determine which step was being executed when error occurred
        current_step_name = "Unknown step"
        if 'generate_metrics_chart' in error_info:
            current_step_name = "Generating metrics chart"
        elif 'generate_topic_overview' in error_info:
            current_step_name = "Generating topic overview"
        elif 'generate_kol' in error_info:
            current_step_name = "Generating KOL analysis"
        elif 'generatre_presence_score' in error_info:
            current_step_name = "Generating presence score"
        elif 'generate_object' in error_info:
            current_step_name = "Generating object analysis"
        elif 'generate_context' in error_info:
            current_step_name = "Generating context analysis"
        elif 'generate_sentiment_analysis' in error_info:
            current_step_name = "Generating sentiment analysis"
        elif 'generate_popular_mentions' in error_info:
            current_step_name = "Generating popular mentions"
        elif 'generate_recommendations' in error_info:
            current_step_name = "Generating recommendations"
        elif 'generate_executive_summary' in error_info:
            current_step_name = "Generating executive summary"
        elif 'create_ppt' in error_info:
            current_step_name = "Creating PowerPoint presentation"
        elif 'upload_and_get_public_url' in error_info:
            current_step_name = "Uploading to cloud storage"
        elif 'send_email' in error_info:
            current_step_name = "Sending email notification"

        error_message = f"""
Error occurred during: {current_step_name}
Location: {error_location}
Error details: {str(e)}
Full traceback:
{error_info}
"""
        logger.error(error_message)
        
        # Update job status to failed with detailed error information
        es.update(
            index="moskal-report-jobs",
            id=job_id,
            body={
                "doc": {
                    "status": "failed",
                    "error": error_message,
                    "error_step": current_step_name,
                    "error_location": error_location
                }
            }
        )

@app.post("/generate-report")
def generate_report(
    background_tasks: BackgroundTasks,
    topic: str,
    start_date: str,
    end_date: str,
    sub_keyword: Optional[str] = "",
    email_receiver: Optional[str] = None
):
    # Create a job record
    job_id = f"{topic}_{int(time.time())}"
    job_data = {
        "id": job_id,
        "topic": topic,
        "start_date": start_date,
        "end_date": end_date,
        "sub_keyword": sub_keyword,
        "email_receiver": email_receiver,
        "status": "pending",
        "progress": 0,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # Store job in Elasticsearch
    es.index(
        index="moskal-report-jobs",
        id=job_id,
        document=job_data
    )

    # Start background processing
    background_tasks.add_task(
        process_report_generation,
        job_id,
        topic,
        start_date,
        end_date,
        sub_keyword,
        email_receiver,
        background_tasks
    )

    return JSONResponse(
        content={
            "status": "success",
            "message": "Report generation started",
            "data": {
                "job_id": job_id
            }
        },
        status_code=202
    )

@app.get("/report-status/{job_id}")
def get_report_status(job_id: str):
    try:
        result = es.get(index="moskal-report-jobs", id=job_id)
        return JSONResponse(
            content={
                "status": "success",
                "data": result["_source"]
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Job not found: {str(e)}")

@app.post("/regenerate-report")
async def regenerate_report(
    background_tasks: BackgroundTasks,
    job_id: str,
    email: Optional[str] = None
):
    try:
        # Get the original job data
        original_job = es.get(index="moskal-report-jobs", id=job_id)
        job_data = original_job["_source"]

        # Check if the job was failed
        if job_data["status"] != "failed":
            raise HTTPException(
                status_code=400,
                detail="Only failed reports can be regenerated"
            )

        # Update email if provided
        if email:
            job_data["email_receiver"] = email

        # Reset job status
        job_data["status"] = "pending"
        job_data["progress"] = 0
        job_data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Update job in Elasticsearch
        es.index(
            index="moskal-report-jobs",
            id=job_id,
            document=job_data
        )

        # Start background processing
        background_tasks.add_task(
            process_report_generation,
            job_id,
            job_data["topic"],
            job_data["start_date"],
            job_data["end_date"],
            job_data["sub_keyword"],
            job_data["email_receiver"],
            background_tasks
        )

        return JSONResponse(
            content={
                "status": "success",
                "message": "Report regeneration started",
                "data": {
                    "job_id": job_id
                }
            },
            status_code=202
        )

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"Error regenerating report: {str(e)}"
        )

@app.post("/generate-sub-keywords")
def generate_keyword(topic: str = None):
    if not topic:
        raise HTTPException(status_code=400, detail="Topic parameter is required")
    KEYWORDS = generate_keywords(topic)
    return JSONResponse(
        content={
            "status": "success",
            "message": "Keywords generated successfully",
            "main_keyword": topic,
            "sub_keyword": KEYWORDS
        },
        status_code=200
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
