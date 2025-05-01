import time
import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
from logging import getLogger

logger = getLogger(__name__)


def fetch_api_data(
    url, headers=None, params=None, method="GET", data=None, stream=False
):
    """
    APIリクエストを実行する関数（GET / POST に対応）
    - JSON: `response.json()`
    - テキスト: `response.text`
    - バイナリデータ: `response.content`
    - `stream=True` の場合は `requests.Response` オブジェクトをそのまま返す
    """
    logger.info(f"Requests to endpoints:{url}")
    try:
        method = method.upper()
        if method == "GET":
            response = requests.get(
                url, headers=headers, params=params, timeout=10, stream=stream
            )
        elif method == "POST":
            response = requests.post(
                url, headers=headers, json=data, timeout=10, stream=stream
            )
        elif method == "PUT":
            response = requests.put(
                url, headers=headers, json=data, timeout=10, stream=stream
            )
        else:
            raise ValueError("Unsupported HTTP method: Use 'GET' or 'POST'")

        response.raise_for_status()  # HTTPエラーがあれば例外を発生

        # Content-Type をチェック
        content_type = response.headers.get("Content-Type", "").lower()

        # JSONレスポンス
        if "application/json" in content_type:
            return response.json() if response.text.strip() else {}

        # ZIP / バイナリファイル
        elif any(
            ext in content_type
            for ext in [
                "application/zip",
                "application/octet-stream",
                "application/x-zip-compressed",
            ]
        ):
            if stream:
                return response  # `stream=True` の場合は `requests.Response` をそのまま返す
            return response.content  # `stream=False` の場合は `bytes` を返す

        # テキストレスポンス
        elif "text/" in content_type:
            return response.text.strip()

        # 不明なフォーマットの場合
        else:
            logger.warning(
                f"Unknown response format ({content_type}). Returning raw content."
            )
            return response.content  # バイナリデータの可能性があるので `content` を返す

    except requests.exceptions.RequestException as e:
        logger.warning(f"Error during API request: {e}")
        return None  # 例外発生時は `None` を返す


def retry_request(
    fetch_function,
    *args,
    max_retries=50,
    initial_wait_time=10,
    max_wait_time=60,
    check_condition=None,
    **kwargs,
) -> dict | None:
    """
    Generic function to retry API requests until success
    """
    retry_count = 0
    wait_time = initial_wait_time

    while retry_count < max_retries:
        try:
            response = fetch_function(*args, **kwargs)

            # NOTE:Conditions are set for repeating responses from outside the system.
            if check_condition and check_condition(response):
                logger.warning(
                    f"Condition not met, retrying in {wait_time} seconds... (Attempt {retry_count + 1})"
                )
            # elif response is None:
            #     print(f"API request failed on attempt {retry_count + 1}.")
            else:
                logger.info(f"API request successful on attempt {retry_count + 1}.")
                return response

        except HTTPError as http_err:
            logger.warning(
                f"HTTP error occurred on attempt {retry_count + 1}: {http_err}"
            )
        except ConnectionError as conn_err:
            logger.warning(
                f"Connection error occurred on attempt {retry_count + 1}: {conn_err}"
            )
        except Timeout as timeout_err:
            logger.warning(
                f"Timeout error occurred on attempt {retry_count + 1}: {timeout_err}"
            )
        except RequestException as req_err:
            logger.warning(
                f"Request error occurred on attempt {retry_count + 1}: {req_err}"
            )
        except Exception as err:
            logger.warning(
                f"An unexpected error occurred on attempt {retry_count + 1}: {err}"
            )

        wait_time = min(wait_time * 2, max_wait_time)
        logger.info(f"Retrying in {wait_time} seconds...")
        time.sleep(wait_time)

        retry_count += 1

    logger.warning("Max retries reached. API request failed.")
    return None
