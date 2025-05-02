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
    logger.info("Creating slide 13: Executive summary...")
    slide_executive_summary(prs, topic, RANGE_DATE, SAVE_FILE, page_number=13, SOURCE=SAVE_PATH)

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
    email_receiver: Optional[str]
):
    try:
        start_time = time.time()
        logger.info(f"Starting report generation for job {job_id}")

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
        from chart_generator.metrics import generate_metrics_chart
        generate_metrics_chart(KEYWORDS, start_date, end_date, prev_start_date, prev_end_date, SAVE_PATH)
        current_step += 1
        update_progress(current_step, total_steps)

        from chart_generator.topics import generate_topic_overview
        generate_topic_overview(topic, KEYWORDS, start_date, end_date, SAVE_PATH)
        current_step += 1
        update_progress(current_step, total_steps)

        from chart_generator.kol import generate_kol
        generate_kol(topic, KEYWORDS, start_date, end_date, SAVE_PATH)
        current_step += 1
        update_progress(current_step, total_steps)

        from chart_generator.presence_score import generatre_presence_score
        generatre_presence_score(topic, KEYWORDS, start_date, end_date, SAVE_PATH)
        current_step += 1
        update_progress(current_step, total_steps)

        from chart_generator.object import generate_object
        generate_object(KEYWORDS, start_date, end_date, limit=10, SAVE_PATH=SAVE_PATH)
        current_step += 1
        update_progress(current_step, total_steps)

        from chart_generator.context import generate_context
        generate_context(KEYWORDS, start_date, end_date, SAVE_PATH)
        current_step += 1
        update_progress(current_step, total_steps)

        from chart_generator.sentiment import generate_sentiment_analysis
        generate_sentiment_analysis(topic, KEYWORDS, start_date, end_date, SAVE_PATH)
        current_step += 1
        update_progress(current_step, total_steps)

        from chart_generator.mentions import generate_popular_mentions
        generate_popular_mentions(KEYWORDS, start_date, end_date, SAVE_PATH)
        current_step += 1
        update_progress(current_step, total_steps)

        from chart_generator.recommendations import generate_recommendations
        generate_recommendations(topic, start_date, end_date, SAVE_PATH)
        current_step += 1
        update_progress(current_step, total_steps)

        from chart_generator.exsum import generate_executive_summary
        summary = generate_executive_summary(topic, start_date, end_date, SAVE_PATH)
        current_step += 1
        update_progress(current_step, total_steps)

        # Generate PowerPoint
        RANGE_DATE = format_range_date(start_date, end_date)
        FILENAME = generate_filename(topic, start_date, end_date, ext="pptx")
        SAVE_FILE = os.path.join(SAVE_PATH, FILENAME)
        prs = Presentation()
        create_ppt(prs, topic, RANGE_DATE, SAVE_FILE, SAVE_PATH)

        # Upload to GCS
        public_url = upload_and_get_public_url(
            local_file_path=SAVE_FILE,
            credentials_json_path=os.getenv("GCS_CREDS_LOCATION"),
            project_id=os.getenv("GCS_PROJECT_ID"),
            bucket_name=os.getenv("GCS_BUCKET_NAME")
        )

        # Send email if requested
        if email_receiver:
            send_email(SAVE_FILE, email_receiver, topic, RANGE_DATE)

        end_time = time.time()
        duration = end_time - start_time

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
        logger.error(f"Error in report generation: {str(e)}")
        # Update job status to failed
        es.update(
            index="moskal-report-jobs",
            id=job_id,
            body={
                "doc": {
                    "status": "failed",
                    "error": str(e)
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
        email_receiver
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

@app.get("/user-reports/{email}")
def get_user_reports(email: str):
    try:
        # Search for completed reports
        completed_result = es.search(
            index="moskal-reports",
            body={
                "query": {
                    "match": {
                        "email_receiver.keyword": email
                    }
                }
            }
        )

        # Search for in-progress reports
        in_progress_result = es.search(
            index="moskal-report-jobs",
            body={
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"email_receiver.keyword": email}},
                            {"bool": {
                                "must_not": [
                                    {"match": {"status": "completed"}}
                                ]
                            }}
                        ]
                    }
                }
            }
        )

        # Process completed reports
        completed_reports = []
        for hit in completed_result["hits"]["hits"]:
            report = hit["_source"]
            completed_reports.append({
                "topic": report["topic"],
                "start_date": report["start_date"],
                "end_date": report["end_date"],
                "filename": report["filename"],
                "url": report["public_url"],
                "created_at": report["created_at"],
                "status": "completed",
                "keywords": report["keywords"],
                "summary": report.get("summary", "Summary not available")
            })

        # Process in-progress reports
        in_progress_reports = []
        for hit in in_progress_result["hits"]["hits"]:
            report = hit["_source"]
            in_progress_reports.append({
                "topic": report["topic"],
                "start_date": report["start_date"],
                "end_date": report["end_date"],
                "created_at": report["created_at"],
                "status": report["status"],
                "progress": report.get("progress", 0),
                "job_id": report["id"],
                "keywords":report["sub_keyword"].split(','),
                "summary": report.get("summary", "Summary not available")
            })

        # Combine all reports
        all_reports = in_progress_reports + completed_reports

        return JSONResponse(
            content={
                "status": "success",
                "data": {
                    "total": len(all_reports),
                    "reports": all_reports
                }
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving reports: {str(e)}")

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
            job_data["email_receiver"]
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
