from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """ジョブの状態を表す列挙型"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobRequest(BaseModel):
    """ジョブ実行リクエストのモデル"""

    github_repository: str = Field(..., description="GitHubリポジトリ名")
    branch_name: str = Field(..., description="ブランチ名")
    base_queries: List[str] = Field(
        default=["diffusion model"], description="基本クエリリスト"
    )
    save_dir: Optional[str] = Field(
        None, description="保存ディレクトリ名（指定しない場合は自動生成）"
    )
    file_path: Optional[str] = Field(None, description="開始するステートファイルのパス")
    llm_name: str = Field(default="gemini-2.0-flash-001", description="使用するLLM名")
    scrape_urls: List[str] = Field(
        default=["https://icml.cc/virtual/2024/papers.html?filter=title"],
        description="スクレイピング対象URLリスト",
    )


class JobResponse(BaseModel):
    """ジョブ作成レスポンスのモデル"""

    job_id: str = Field(..., description="ジョブID")
    status: JobStatus = Field(..., description="ジョブの状態")
    message: str = Field(..., description="メッセージ")


class JobStatusResponse(BaseModel):
    """ジョブ状態レスポンスのモデル"""

    job_id: str = Field(..., description="ジョブID")
    status: JobStatus = Field(..., description="ジョブの状態")
    created_at: datetime = Field(..., description="作成日時")
    started_at: Optional[datetime] = Field(None, description="開始日時")
    completed_at: Optional[datetime] = Field(None, description="完了日時")
    current_step: Optional[str] = Field(None, description="現在実行中のステップ")
    progress: float = Field(default=0.0, description="進捗率（0.0-1.0）")
    result: Optional[Dict[str, Any]] = Field(None, description="実行結果")
    error: Optional[str] = Field(None, description="エラーメッセージ")


class JobListResponse(BaseModel):
    """ジョブ一覧レスポンスのモデル"""

    jobs: List[JobStatusResponse] = Field(..., description="ジョブリスト")
    total: int = Field(..., description="総ジョブ数")


class JobCancelResponse(BaseModel):
    """ジョブキャンセルレスポンスのモデル"""

    message: str = Field(..., description="メッセージ")
    job_id: str = Field(..., description="ジョブID")


class JobDeleteResponse(BaseModel):
    """ジョブ削除レスポンスのモデル"""

    message: str = Field(..., description="メッセージ")
    job_id: str = Field(..., description="ジョブID")


class JobResultResponse(BaseModel):
    """ジョブ結果レスポンスのモデル"""

    job_id: str = Field(..., description="ジョブID")
    result: Dict[str, Any] = Field(..., description="実行結果")


class JobStatisticsResponse(BaseModel):
    """ジョブ統計レスポンスのモデル"""

    total_jobs: int = Field(..., description="総ジョブ数")
    status_counts: Dict[str, int] = Field(..., description="状態別ジョブ数")
    average_duration_seconds: Optional[float] = Field(
        None, description="平均実行時間（秒）"
    )
    completed_jobs: int = Field(..., description="完了したジョブ数")
