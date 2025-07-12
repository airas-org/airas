import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from airas.services.web_api.models.job import JobStatisticsResponse
from airas.services.web_api.routes.jobs import router as jobs_router
from airas.services.web_api.services.job_manager import JobManager

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPIアプリケーションの作成
app = FastAPI(
    title="Airas E2E API",
    description="Airas E2E処理を実行するためのAPI",
    version="1.0.0",
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# サービスの初期化
job_manager = JobManager()

# ルーターの登録
app.include_router(jobs_router, prefix="/jobs", tags=["jobs"])


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {"message": "Airas E2E API", "version": "1.0.0"}


@app.get("/statistics", response_model=JobStatisticsResponse)
async def get_statistics():
    """ジョブ統計を取得"""
    try:
        stats = job_manager.get_job_statistics()
        return JobStatisticsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/cleanup")
async def cleanup_old_jobs(days: int = 30):
    """古いジョブを削除"""
    try:
        deleted_count = job_manager.cleanup_old_jobs(days=days)
        return {
            "message": f"Cleaned up {deleted_count} old jobs",
            "deleted_count": deleted_count,
        }
    except Exception as e:
        logger.error(f"Error cleaning up old jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    try:
        import uvicorn

        uvicorn.run(app, host="0.0.0.0", port=8000)
    except ImportError:
        print("uvicorn is not installed. Please install it with: pip install uvicorn")
