import json
from typing import Any, Dict, Union

import requests

from airas.services.api_client.llm_client.llm_facade_client import LLMFacadeClient
from airas.services.api_client.qdrant_client import QdrantClient


def request_paper_data(url: str) -> Union[Dict[str, Any], list[Any]]:
    """
    指定されたURLからNeurIPS 2020のデータを取得する

    Args:
        url (str): データを取得するURL

    Returns:
        Dict[str, Any]: 取得したJSONデータ

    Raises:
        requests.RequestException: HTTPリクエストが失敗した場合
        json.JSONDecodeError: JSONのパースに失敗した場合
    """
    try:
        # HTTPリクエストを送信
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # ステータスコードが200番台以外の場合は例外を発生

        # JSONデータをパース
        data = response.json()

        print(
            f"データを正常に取得しました。論文数: {len(data) if isinstance(data, list) else 'N/A'}"
        )
        return data

    except requests.exceptions.RequestException as e:
        print(f"HTTPリクエストエラー: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"JSONパースエラー: {e}")
        raise


def retrieve_all_paper() -> list[dict[str, Any]]:
    url_list = [
        # NeurIPS
        "https://raw.githubusercontent.com/airas-org/airas-papers-db/refs/heads/main/data/neurips/2020.json",
        "https://raw.githubusercontent.com/airas-org/airas-papers-db/refs/heads/main/data/neurips/2021.json",
        "https://raw.githubusercontent.com/airas-org/airas-papers-db/refs/heads/main/data/neurips/2022.json",
        "https://raw.githubusercontent.com/airas-org/airas-papers-db/refs/heads/main/data/neurips/2023.json",
        "https://raw.githubusercontent.com/airas-org/airas-papers-db/refs/heads/main/data/neurips/2024.json",
        # ICML
        "https://raw.githubusercontent.com/airas-org/airas-papers-db/refs/heads/main/data/icml/2020.json",
        "https://raw.githubusercontent.com/airas-org/airas-papers-db/refs/heads/main/data/icml/2021.json",
        "https://raw.githubusercontent.com/airas-org/airas-papers-db/refs/heads/main/data/icml/2022.json",
        "https://raw.githubusercontent.com/airas-org/airas-papers-db/refs/heads/main/data/icml/2023.json",
        "https://raw.githubusercontent.com/airas-org/airas-papers-db/refs/heads/main/data/icml/2024.json",
        # ICLR
        "https://raw.githubusercontent.com/airas-org/airas-papers-db/refs/heads/main/data/iclr/2020.json",
        "https://raw.githubusercontent.com/airas-org/airas-papers-db/refs/heads/main/data/iclr/2021.json",
        "https://raw.githubusercontent.com/airas-org/airas-papers-db/refs/heads/main/data/iclr/2023.json",
        "https://raw.githubusercontent.com/airas-org/airas-papers-db/refs/heads/main/data/iclr/2024.json",
        # CVPR
        "https://raw.githubusercontent.com/airas-org/airas-papers-db/refs/heads/main/data/cvpr/2023.json",
        "https://raw.githubusercontent.com/airas-org/airas-papers-db/refs/heads/main/data/cvpr/2024.json",
    ]

    all_data_list: list[Any] = []
    for url in url_list:
        data = request_paper_data(url)
        all_data_list.extend(data)
    return all_data_list[29695:]


def create_qdrant_collection(collection_name: str) -> None:
    """
    Qdrantにコレクションを作成する
    """
    qdrant_client = QdrantClient()
    vector_size = 3072
    distance = "Cosine"

    response = qdrant_client.create_a_collection(
        collection_name=collection_name, vector_size=vector_size, distance=distance
    )
    print(f"Collection '{collection_name}' created: {response}")


def upload_paper_to_qdrant(collection_name: str) -> None:
    llm_client = LLMFacadeClient(llm_name="gemini-embedding-001")
    qdrant_client = QdrantClient()
    # 論文の取得
    all_paper_list = retrieve_all_paper()
    for idx, paper in enumerate(all_paper_list):
        idx = idx + 29695
        print(f"Processing paper {idx + 1}/{len(all_paper_list)}")
        abstract = paper["abstract"]
        # エンべディング
        query_vector = llm_client.text_embedding(message=abstract)
        # 加工
        data = [
            {
                "id": idx,
                "vector": query_vector,
                "payload": {
                    "title": paper["title"],
                },
            }
        ]
        # Qdrantにアップロード
        qdrant_client.upsert_points(collection_name, data)
    return


def paper_search(
    collection_name: str, query: str, limit: int = 10
) -> list[dict[str, Any]]:
    llm_client = LLMFacadeClient(llm_name="gemini-embedding-001")
    qdrant_client = QdrantClient()
    query_vector = llm_client.text_embedding(message=query)
    if query_vector:
        result = qdrant_client.query_points(
            collection_name=collection_name, query_vector=query_vector, limit=limit
        )
        return result
    else:
        print("Query vector is empty. Please check the input query.")
        return []


if __name__ == "__main__":
    collection_name = "airas_database"
    create_qdrant_collection(collection_name)
    upload_paper_to_qdrant(collection_name)

    # query = "Faster inference for large language models"
    # limit = 10
    # result = paper_search(collection_name, query=query)
    # print(result)

    # result = QdrantClient().retrieve_a_points(
    #     collection_name=collection_name,
    #     id=29694
    # )
    # print(result)
