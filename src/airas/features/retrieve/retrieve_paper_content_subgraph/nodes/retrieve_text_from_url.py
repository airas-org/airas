from io import BytesIO
from logging import getLogger

import requests
from pypdf import PdfReader

from airas.types.research_study import ResearchStudy

logger = getLogger(__name__)


def retrieve_text_from_url(
    research_study_list: list[ResearchStudy],
) -> list[ResearchStudy]:
    for research_study in research_study_list:
        pdf_url = research_study.meta_data.pdf_url if research_study.meta_data else None
        if not pdf_url:
            continue

        try:
            response = requests.get(pdf_url, timeout=30)
            response.raise_for_status()

            pdf_reader = PdfReader(BytesIO(response.content))
            text = "".join(page.extract_text() for page in pdf_reader.pages)
            research_study.full_text = text.replace("\n", " ")
        except Exception as e:
            logger.error(f"Failed to extract text from PDF {pdf_url}: {e}")

    return research_study_list


if __name__ == "__main__":
    from airas.types.research_study import MetaData, ResearchStudy

    research_study = ResearchStudy(
        title="Test Paper",
        meta_data=MetaData(pdf_url="https://arxiv.org/pdf/1706.03762.pdf"),
    )

    results = retrieve_text_from_url([research_study])
    print(
        f"Extracted {len(results[0].full_text)} characters"
        if results[0].full_text
        else "No text extracted"
    )
