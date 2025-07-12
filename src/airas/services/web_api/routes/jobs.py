from fastapi import APIRouter, BackgroundTasks, HTTPException

from airas.services.web_api.models.job import (
    JobCancelResponse,
    JobDeleteResponse,
    JobListResponse,
    JobRequest,
    JobResponse,
    JobResultResponse,
    JobStatus,
    JobStatusResponse,
)
from airas.services.web_api.services.e2e_executor import E2EExecutor
from airas.services.web_api.services.job_manager import JobManager

router = APIRouter()
job_manager = JobManager()
e2e_executor = E2EExecutor()


@router.post("/", response_model=JobResponse)
async def create_job(request: JobRequest, background_tasks: BackgroundTasks):
    """新しいE2Eジョブを作成"""
    from datetime import datetime

    try:
        # ジョブデータの準備
        job_data = {
            "github_repository": request.github_repository,
            "branch_name": request.branch_name,
            "base_queries": request.base_queries,
            "save_dir": request.save_dir or datetime.now().strftime("%Y%m%d_%H%M%S"),
            "file_path": request.file_path,
            "llm_name": request.llm_name,
            "scrape_urls": request.scrape_urls,
        }

        # ジョブを作成
        job_id = job_manager.create_job(job_data)

        # バックグラウンドでE2E処理を実行
        background_tasks.add_task(
            e2e_executor.run_e2e_async,
            job_id=job_id,
            github_repository=request.github_repository,
            branch_name=request.branch_name,
            save_dir=job_data["save_dir"],
            file_path=request.file_path,
            base_queries=request.base_queries,
            job_manager=job_manager,
        )

        return JobResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            message="Job created successfully",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job(job_id: str):
    """ジョブの状態を取得"""
    try:
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/", response_model=JobListResponse)
async def list_jobs(limit: int = 100):
    """ジョブ一覧を取得（軽量版）"""
    try:
        jobs = job_manager.list_jobs(limit=limit)

        # 軽量なジョブ概要リストを作成
        job_summaries = []
        for job in jobs:
            # resultフィールドを除外して軽量化
            job_summary = JobStatusResponse(
                job_id=job.job_id,
                status=job.status,
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
                current_step=job.current_step,
                progress=job.progress,
                result=None,
                error=job.error,
            )
            job_summaries.append(job_summary)

        return JobListResponse(jobs=job_summaries, total=len(job_summaries))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/summary", response_model=JobListResponse)
async def list_jobs_summary(limit: int = 100):
    """ジョブ一覧を取得（超軽量版 - 結果データなし）"""
    try:
        jobs = job_manager.list_jobs(limit=limit)

        # 最小限のジョブ概要リストを作成
        job_summaries = []
        for job in jobs:
            job_summary = JobStatusResponse(
                job_id=job.job_id,
                status=job.status,
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
                current_step=job.current_step,
                progress=job.progress,
                result=None,
                error=job.error,
            )
            job_summaries.append(job_summary)

        return JobListResponse(jobs=job_summaries, total=len(job_summaries))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/{job_id}", response_model=JobDeleteResponse)
async def delete_job(job_id: str):
    """ジョブを削除"""
    try:
        success = job_manager.delete_job(job_id)
        if not success:
            raise HTTPException(status_code=404, detail="Job not found")

        return JobDeleteResponse(
            message="Job deleted successfully",
            job_id=job_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/{job_id}/cancel", response_model=JobCancelResponse)
async def cancel_job(job_id: str):
    """ジョブをキャンセル"""
    try:
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            raise HTTPException(status_code=400, detail="Job cannot be cancelled")

        success = job_manager.update_job_status(job_id, JobStatus.CANCELLED)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to cancel job")

        return JobCancelResponse(
            message="Job cancelled successfully",
            job_id=job_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{job_id}/result", response_model=JobResultResponse)
async def get_job_result(job_id: str):
    """ジョブの結果を取得"""
    try:
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job.status != JobStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Job is not completed")

        if not job.result:
            raise HTTPException(status_code=404, detail="Job result not found")

        return JobResultResponse(
            job_id=job_id,
            result=job.result,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
