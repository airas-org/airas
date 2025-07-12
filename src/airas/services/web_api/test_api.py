#!/usr/bin/env python3
"""
Airas E2E API テストスクリプト
"""

import json
import time
from typing import Any, Dict

import requests


class AirasAPIClient:
    """Airas E2E API クライアント"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def create_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """ジョブを作成"""
        response = requests.post(f"{self.base_url}/jobs/", json=job_data)
        response.raise_for_status()
        return response.json()

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """ジョブの状態を取得"""
        response = requests.get(f"{self.base_url}/jobs/{job_id}")
        response.raise_for_status()
        return response.json()

    def list_jobs(self, limit: int = 10) -> Dict[str, Any]:
        """ジョブ一覧を取得"""
        response = requests.get(f"{self.base_url}/jobs/", params={"limit": limit})
        response.raise_for_status()
        return response.json()

    def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """ジョブをキャンセル"""
        response = requests.post(f"{self.base_url}/jobs/{job_id}/cancel")
        response.raise_for_status()
        return response.json()

    def get_job_result(self, job_id: str) -> Dict[str, Any]:
        """ジョブの結果を取得"""
        response = requests.get(f"{self.base_url}/jobs/{job_id}/result")
        response.raise_for_status()
        return response.json()

    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        response = requests.get(f"{self.base_url}/statistics")
        response.raise_for_status()
        return response.json()

    def cleanup_old_jobs(self, days: int = 30) -> Dict[str, Any]:
        """古いジョブを削除"""
        response = requests.post(f"{self.base_url}/cleanup", params={"days": days})
        response.raise_for_status()
        return response.json()


def test_api():
    """APIテスト"""
    client = AirasAPIClient()

    print("=== Airas E2E API テスト ===")

    # 1. 統計情報の取得
    print("\n1. 統計情報の取得")
    try:
        stats = client.get_statistics()
        print(f"統計情報: {json.dumps(stats, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"統計情報取得エラー: {e}")

    # 2. ジョブ一覧の取得
    print("\n2. ジョブ一覧の取得")
    try:
        jobs = client.list_jobs(limit=5)
        print(f"ジョブ数: {jobs['total']}")
        for job in jobs["jobs"][:3]:  # 最新3件を表示
            print(f"  - {job['job_id']}: {job['status']} ({job['created_at']})")
    except Exception as e:
        print(f"ジョブ一覧取得エラー: {e}")

    # 3. 新しいジョブの作成（テスト用）
    print("\n3. 新しいジョブの作成")
    try:
        job_data = {
            "github_repository": "auto-res2/onda",
            "branch_name": "test-1",
            "base_queries": ["diffusion model"],  # e2e.pyと同じクエリを使用
            "save_dir": f"test_{int(time.time())}",
            "file_path": None,
            "llm_name": "gemini-2.0-flash-001",
            "scrape_urls": ["https://icml.cc/virtual/2024/papers.html?filter=title"],
        }

        job_response = client.create_job(job_data)
        job_id = job_response["job_id"]
        print(f"ジョブ作成成功: {job_id}")
        print(f"レスポンス: {json.dumps(job_response, indent=2, ensure_ascii=False)}")

        # 4. ジョブ状態の監視（詳細版）
        print("\n4. ジョブ状態の監視（30秒間）")
        for i in range(30):
            try:
                status = client.get_job_status(job_id)
                print(
                    f"  {i + 1}/30: {status['status']} - {status.get('current_step', 'N/A')} ({status.get('progress', 0):.1%})"
                )

                # エラーが発生した場合の詳細情報
                if status.get("error"):
                    print(f"  エラー詳細: {status['error']}")

                if status["status"] in ["completed", "failed", "cancelled"]:
                    print(f"  ジョブ終了: {status['status']}")
                    if status["status"] == "failed":
                        print(f"  失敗理由: {status.get('error', '不明')}")
                    break

                time.sleep(1)
            except Exception as e:
                print(f"  状態取得エラー: {e}")
                break

        # 5. ジョブのキャンセル（テスト用）
        print("\n5. ジョブのキャンセル")
        try:
            cancel_response = client.cancel_job(job_id)
            print(
                f"キャンセル結果: {json.dumps(cancel_response, indent=2, ensure_ascii=False)}"
            )
        except Exception as e:
            print(f"キャンセルエラー: {e}")

    except Exception as e:
        print(f"ジョブ作成エラー: {e}")

    print("\n=== テスト完了 ===")


def test_server_connection():
    """サーバー接続テスト"""
    print("=== サーバー接続テスト ===")

    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print("✅ サーバーに接続できました")
            print(f"レスポンス: {response.json()}")
        else:
            print(f"❌ サーバーエラー: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ サーバーに接続できません。サーバーが起動しているか確認してください。")
    except Exception as e:
        print(f"❌ 接続エラー: {e}")


if __name__ == "__main__":
    # サーバー接続テスト
    test_server_connection()

    # APIテスト
    test_api()
