import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from airas.services.web_api.models.job import JobStatus, JobStatusResponse

logger = logging.getLogger(__name__)


class JobManager:
    """ジョブ管理システム"""

    def __init__(self, data_dir: str = "/workspaces/airas/data"):
        self.data_dir = Path(data_dir)
        self.jobs_dir = self.data_dir / "jobs"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"JobManager initialized with data directory: {self.data_dir}")

    def create_job(self, job_data: Dict[str, Any]) -> str:
        """新しいジョブを作成"""
        job_id = str(uuid.uuid4())
        job_info = {
            "job_id": job_id,
            "status": JobStatus.PENDING,
            "created_at": datetime.now().isoformat(),
            "data": job_data,
            "progress": 0.0,
            "current_step": None,
            "result": None,
            "error": None,
        }

        job_file = self.jobs_dir / f"{job_id}.json"
        with open(job_file, "w", encoding="utf-8") as f:
            json.dump(job_info, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Created job {job_id} with status: {JobStatus.PENDING}")
        return job_id

    def get_job(self, job_id: str) -> Optional[JobStatusResponse]:
        """ジョブ情報を取得"""
        job_file = self.jobs_dir / f"{job_id}.json"
        if not job_file.exists():
            logger.warning(f"Job {job_id} not found")
            return None

        try:
            with open(job_file, "r", encoding="utf-8") as f:
                job_info = json.load(f)

            return JobStatusResponse(
                job_id=job_info["job_id"],
                status=JobStatus(job_info["status"]),
                created_at=datetime.fromisoformat(job_info["created_at"]),
                started_at=datetime.fromisoformat(job_info["started_at"])
                if job_info.get("started_at")
                else None,
                completed_at=datetime.fromisoformat(job_info["completed_at"])
                if job_info.get("completed_at")
                else None,
                current_step=job_info.get("current_step"),
                progress=job_info.get("progress", 0.0),
                result=job_info.get("result"),
                error=job_info.get("error"),
                github_repository=job_info.get("github_repository"),
                branch_name=job_info.get("branch_name"),
            )
        except Exception as e:
            logger.error(f"Error loading job {job_id}: {e}")
            return None

    def update_job_status(self, job_id: str, status: JobStatus, **kwargs) -> bool:
        """ジョブの状態を更新"""
        job_file = self.jobs_dir / f"{job_id}.json"
        if not job_file.exists():
            logger.warning(f"Job {job_id} not found for status update")
            return False

        try:
            with open(job_file, "r", encoding="utf-8") as f:
                job_info = json.load(f)

            job_info["status"] = status

            # タイムスタンプの更新
            if status == JobStatus.RUNNING and not job_info.get("started_at"):
                job_info["started_at"] = datetime.now().isoformat()
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                job_info["completed_at"] = datetime.now().isoformat()

            # 追加の更新項目
            for key, value in kwargs.items():
                job_info[key] = value

            with open(job_file, "w", encoding="utf-8") as f:
                json.dump(job_info, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"Updated job {job_id} status to {status}")
            return True

        except Exception as e:
            logger.error(f"Error updating job {job_id} status: {e}")
            return False

    def list_jobs(self, limit: int = 100) -> List[JobStatusResponse]:
        """ジョブ一覧を取得"""
        jobs: List[JobStatusResponse] = []

        try:
            # ファイルの更新時刻でソート（新しい順）
            job_files = sorted(
                self.jobs_dir.glob("*.json"),
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            )

            for job_file in job_files:
                if len(jobs) >= limit:
                    break

                try:
                    with open(job_file, "r", encoding="utf-8") as f:
                        job_info = json.load(f)

                    job_response = JobStatusResponse(
                        job_id=job_info["job_id"],
                        status=JobStatus(job_info["status"]),
                        created_at=datetime.fromisoformat(job_info["created_at"]),
                        started_at=datetime.fromisoformat(job_info["started_at"])
                        if job_info.get("started_at")
                        else None,
                        completed_at=datetime.fromisoformat(job_info["completed_at"])
                        if job_info.get("completed_at")
                        else None,
                        current_step=job_info.get("current_step"),
                        progress=job_info.get("progress", 0.0),
                        result=job_info.get("result"),
                        error=job_info.get("error"),
                        github_repository=job_info.get("github_repository"),
                        branch_name=job_info.get("branch_name"),
                    )
                    jobs.append(job_response)

                except Exception as e:
                    logger.error(f"Error loading job file {job_file}: {e}")
                    continue

            logger.info(f"Retrieved {len(jobs)} jobs")
            return jobs

        except Exception as e:
            logger.error(f"Error listing jobs: {e}")
            return []

    def delete_job(self, job_id: str) -> bool:
        """ジョブを削除"""
        job_file = self.jobs_dir / f"{job_id}.json"
        if job_file.exists():
            try:
                job_file.unlink()
                logger.info(f"Deleted job {job_id}")
                return True
            except Exception as e:
                logger.error(f"Error deleting job {job_id}: {e}")
                return False
        else:
            logger.warning(f"Job {job_id} not found for deletion")
            return False

    def get_job_data(self, job_id: str) -> Optional[Dict[str, Any]]:
        """ジョブの詳細データを取得"""
        job_file = self.jobs_dir / f"{job_id}.json"
        if not job_file.exists():
            return None

        try:
            with open(job_file, "r", encoding="utf-8") as f:
                job_info = json.load(f)
            return job_info.get("data")
        except Exception as e:
            logger.error(f"Error loading job data for {job_id}: {e}")
            return None

    def cleanup_old_jobs(self, days: int = 30) -> int:
        """古いジョブを削除"""
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        deleted_count = 0

        try:
            for job_file in self.jobs_dir.glob("*.json"):
                if job_file.stat().st_mtime < cutoff_time:
                    try:
                        job_file.unlink()
                        deleted_count += 1
                        logger.info(f"Cleaned up old job file: {job_file.name}")
                    except Exception as e:
                        logger.error(f"Error deleting old job file {job_file}: {e}")

            logger.info(f"Cleaned up {deleted_count} old job files")
            return deleted_count

        except Exception as e:
            logger.error(f"Error during job cleanup: {e}")
            return 0

    def get_job_statistics(self) -> Dict[str, Any]:
        """ジョブの統計情報を取得"""
        try:
            jobs = self.list_jobs(limit=1000)  # より多くのジョブを取得

            status_counts: Dict[str, int] = {}
            total_jobs = len(jobs)

            for job in jobs:
                status = job.status.value
                status_counts[status] = status_counts.get(status, 0) + 1

            # 平均実行時間を計算
            completed_jobs = [job for job in jobs if job.status == JobStatus.COMPLETED]
            avg_duration = None
            if completed_jobs:
                durations = []
                for job in completed_jobs:
                    if job.started_at and job.completed_at:
                        duration = (job.completed_at - job.started_at).total_seconds()
                        durations.append(duration)

                if durations:
                    avg_duration = sum(durations) / len(durations)

            return {
                "total_jobs": total_jobs,
                "status_counts": status_counts,
                "average_duration_seconds": avg_duration,
                "completed_jobs": len(completed_jobs),
            }

        except Exception as e:
            logger.error(f"Error getting job statistics: {e}")
            return {
                "total_jobs": 0,
                "status_counts": {},
                "average_duration_seconds": None,
                "completed_jobs": 0,
            }
