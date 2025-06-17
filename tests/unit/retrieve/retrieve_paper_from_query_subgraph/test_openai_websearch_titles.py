import json
from unittest.mock import Mock, patch

import pytest

from airas.retrieve.retrieve_paper_from_query_subgraph2.nodes.openai_websearch_titles import (
    _extract_json,
    _is_excluded_title,
    openai_websearch_titles,
)


class TestIsExcludedTitle:
    """Test the _is_excluded_title function."""

    def test_excluded_keywords(self):
        """Test that titles with excluded keywords are filtered out."""
        excluded_titles = [
            "A survey of machine learning techniques",
            "Review of deep learning approaches",
            "An overview of neural networks",
            "Systematic review of computer vision",
        ]
        for title in excluded_titles:
            assert _is_excluded_title(title) is True

    def test_non_excluded_titles(self):
        """Test that normal titles are not filtered out."""
        normal_titles = [
            "Novel approach to image classification",
            "Efficient training of large language models",
            "Improving performance with attention mechanisms",
        ]
        for title in normal_titles:
            assert _is_excluded_title(title) is False

    def test_case_insensitive(self):
        """Test that filtering is case insensitive."""
        assert _is_excluded_title("SURVEY of machine learning") is True
        assert _is_excluded_title("Machine Learning REVIEW") is True


class TestExtractJson:
    """Test the _extract_json function."""

    def test_extract_plain_json(self):
        """Test extraction of plain JSON."""
        json_text = '{"titles": ["Title 1", "Title 2"]}'
        result = _extract_json(json_text)
        assert result == {"titles": ["Title 1", "Title 2"]}

    def test_extract_json_with_code_fences(self):
        """Test extraction of JSON wrapped in code fences."""
        json_text = '```json\n{"titles": ["Title 1", "Title 2"]}\n```'
        result = _extract_json(json_text)
        assert result == {"titles": ["Title 1", "Title 2"]}

    def test_extract_json_with_language_tag(self):
        """Test extraction of JSON with language tag."""
        json_text = '```\n{"titles": ["Title 1", "Title 2"]}\n```'
        result = _extract_json(json_text)
        assert result == {"titles": ["Title 1", "Title 2"]}

    def test_invalid_json_raises_error(self):
        """Test that invalid JSON raises an error."""
        with pytest.raises(json.JSONDecodeError):
            _extract_json("invalid json")


class TestOpenaiWebsearchTitles:
    """Test the openai_websearch_titles function."""

    @patch("airas.retrieve.retrieve_paper_from_query_subgraph.nodes.openai_websearch_titles.sleep")
    def test_successful_search(self, mock_sleep):
        """Test successful paper title search."""
        # Mock OpenAI client and response
        mock_client = Mock()
        mock_response = Mock()
        
        # Create mock assistant message
        mock_message = Mock()
        mock_message.type = "message"
        mock_message.role = "assistant"
        mock_content = Mock()
        mock_content.text = '{"titles": ["Novel Neural Network Architecture", "Advanced Deep Learning Method"]}'
        mock_message.content = [mock_content]
        
        mock_response.output = [mock_message]
        mock_client.responses.create.return_value = mock_response
        
        result = openai_websearch_titles(
            queries=["machine learning"],
            max_results=5,
            sleep_sec=0.1,
            client=mock_client,
        )
        
        expected_titles = ["Advanced Deep Learning Method", "Novel Neural Network Architecture"]
        assert result == expected_titles
        assert mock_client.responses.create.call_count == 1
        
        # Verify the API call parameters
        call_args = mock_client.responses.create.call_args
        assert call_args[1]["model"] == "gpt-4o"
        assert call_args[1]["tools"] == [{"type": "web_search_preview"}]
        assert "machine learning" in call_args[1]["input"]

    @patch("airas.retrieve.retrieve_paper_from_query_subgraph.nodes.openai_websearch_titles.sleep")
    def test_no_assistant_response(self, mock_sleep):
        """Test handling when no assistant response is received."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.output = []  # No assistant messages
        mock_client.responses.create.return_value = mock_response
        
        result = openai_websearch_titles(
            queries=["test query"],
            max_results=5,
            sleep_sec=0.1,
            client=mock_client,
        )
        
        assert result is None

    @patch("airas.retrieve.retrieve_paper_from_query_subgraph.nodes.openai_websearch_titles.sleep")
    def test_api_error_handling(self, mock_sleep):
        """Test handling of API errors."""
        mock_client = Mock()
        mock_client.responses.create.side_effect = Exception("API Error")
        
        result = openai_websearch_titles(
            queries=["test query"],
            max_results=5,
            sleep_sec=0.1,
            client=mock_client,
        )
        
        assert result is None

    @patch("airas.retrieve.retrieve_paper_from_query_subgraph.nodes.openai_websearch_titles.sleep")
    def test_excluded_titles_filtering(self, mock_sleep):
        """Test that excluded titles are filtered out."""
        mock_client = Mock()
        mock_response = Mock()
        
        mock_message = Mock()
        mock_message.type = "message"
        mock_message.role = "assistant"
        mock_content = Mock()
        mock_content.text = '{"titles": ["A survey of AI", "Novel Neural Network", "Review of ML"]}'
        mock_message.content = [mock_content]
        
        mock_response.output = [mock_message]
        mock_client.responses.create.return_value = mock_response
        
        result = openai_websearch_titles(
            queries=["AI research"],
            max_results=5,
            sleep_sec=0.1,
            client=mock_client,
        )
        
        # Only the non-excluded title should remain
        assert result == ["Novel Neural Network"]

    @patch("airas.retrieve.retrieve_paper_from_query_subgraph.nodes.openai_websearch_titles.sleep")
    def test_multiple_queries_with_sleep(self, mock_sleep):
        """Test that sleep is called between multiple queries."""
        mock_client = Mock()
        mock_response = Mock()
        
        mock_message = Mock()
        mock_message.type = "message"
        mock_message.role = "assistant"
        mock_content = Mock()
        mock_content.text = '{"titles": ["Title 1"]}'
        mock_message.content = [mock_content]
        
        mock_response.output = [mock_message]
        mock_client.responses.create.return_value = mock_response
        
        openai_websearch_titles(
            queries=["query1", "query2"],
            max_results=5,
            sleep_sec=0.1,
            client=mock_client,
        )
        
        # Sleep should be called once (between query1 and query2)
        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_with(0.1)

    @patch("airas.retrieve.retrieve_paper_from_query_subgraph.nodes.openai_websearch_titles.sleep")
    def test_max_results_limit(self, mock_sleep):
        """Test that results are limited by max_results parameter."""
        mock_client = Mock()
        mock_response = Mock()
        
        mock_message = Mock()
        mock_message.type = "message"
        mock_message.role = "assistant"
        mock_content = Mock()
        mock_content.text = '{"titles": ["Title 1", "Title 2", "Title 3", "Title 4", "Title 5"]}'
        mock_message.content = [mock_content]
        
        mock_response.output = [mock_message]
        mock_client.responses.create.return_value = mock_response
        
        result = openai_websearch_titles(
            queries=["query"],
            max_results=3,
            sleep_sec=0.1,
            client=mock_client,
        )
        
        # Should return exactly max_results titles
        assert len(result) == 3

    def test_default_client_creation(self):
        """Test that OpenAI client is created when not provided."""
        with patch("airas.retrieve.retrieve_paper_from_query_subgraph.nodes.openai_websearch_titles.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            mock_response = Mock()
            mock_response.output = []
            mock_client.responses.create.return_value = mock_response
            
            openai_websearch_titles(
                queries=["test"],
                max_results=5,
            )
            
            # OpenAI() should be called to create default client
            mock_openai.assert_called_once()

    @patch("airas.retrieve.retrieve_paper_from_query_subgraph.nodes.openai_websearch_titles.sleep")
    def test_invalid_json_response_handling(self, mock_sleep):
        """Test handling of invalid JSON in API response."""
        mock_client = Mock()
        mock_response = Mock()
        
        mock_message = Mock()
        mock_message.type = "message"
        mock_message.role = "assistant"
        mock_content = Mock()
        mock_content.text = "Invalid JSON response"
        mock_message.content = [mock_content]
        
        mock_response.output = [mock_message]
        mock_client.responses.create.return_value = mock_response
        
        result = openai_websearch_titles(
            queries=["test query"],
            max_results=5,
            sleep_sec=0.1,
            client=mock_client,
        )
        
        assert result is None

    @patch("airas.retrieve.retrieve_paper_from_query_subgraph.nodes.openai_websearch_titles.sleep")
    def test_empty_titles_response(self, mock_sleep):
        """Test handling when API returns empty titles list."""
        mock_client = Mock()
        mock_response = Mock()
        
        mock_message = Mock()
        mock_message.type = "message"
        mock_message.role = "assistant"
        mock_content = Mock()
        mock_content.text = '{"titles": []}'
        mock_message.content = [mock_content]
        
        mock_response.output = [mock_message]
        mock_client.responses.create.return_value = mock_response
        
        result = openai_websearch_titles(
            queries=["test query"],
            max_results=5,
            sleep_sec=0.1,
            client=mock_client,
        )
        
        assert result is None

    @patch("airas.retrieve.retrieve_paper_from_query_subgraph.nodes.openai_websearch_titles.sleep")
    def test_conference_preference_parameter(self, mock_sleep):
        """Test that conference_preference parameter is properly passed to template."""
        mock_client = Mock()
        mock_response = Mock()
        
        mock_message = Mock()
        mock_message.type = "message"
        mock_message.role = "assistant"
        mock_content = Mock()
        mock_content.text = '{"titles": ["Conference Paper Title"]}'
        mock_message.content = [mock_content]
        
        mock_response.output = [mock_message]
        mock_client.responses.create.return_value = mock_response
        
        result = openai_websearch_titles(
            queries=["machine learning"],
            max_results=5,
            sleep_sec=0.1,
            conference_preference="NeurIPS, ICML, ICLR",
            client=mock_client,
        )
        
        assert result == ["Conference Paper Title"]
        
        # Check that the API was called with the conference preference in prompt
        call_args = mock_client.responses.create.call_args
        prompt_text = call_args[1]["input"]
        assert "NeurIPS, ICML, ICLR" in prompt_text
        assert "Focus on papers from these conferences" in prompt_text

    @patch("airas.retrieve.retrieve_paper_from_query_subgraph.nodes.openai_websearch_titles.sleep")
    def test_no_conference_preference(self, mock_sleep):
        """Test that when conference_preference is None, no conference instruction is added."""
        mock_client = Mock()
        mock_response = Mock()
        
        mock_message = Mock()
        mock_message.type = "message"
        mock_message.role = "assistant"
        mock_content = Mock()
        mock_content.text = '{"titles": ["General Paper Title"]}'
        mock_message.content = [mock_content]
        
        mock_response.output = [mock_message]
        mock_client.responses.create.return_value = mock_response
        
        result = openai_websearch_titles(
            queries=["machine learning"],
            max_results=5,
            sleep_sec=0.1,
            conference_preference=None,
            client=mock_client,
        )
        
        assert result == ["General Paper Title"]
        
        # Check that no conference instruction is in the prompt
        call_args = mock_client.responses.create.call_args
        prompt_text = call_args[1]["input"]
        assert "Focus on papers from these conferences" not in prompt_text

    @patch("airas.retrieve.retrieve_paper_from_query_subgraph.nodes.openai_websearch_titles.sleep")
    def test_custom_prompt_template_with_conference(self, mock_sleep):
        """Test using custom prompt template with conference preference."""
        mock_client = Mock()
        mock_response = Mock()
        
        mock_message = Mock()
        mock_message.type = "message"
        mock_message.role = "assistant"
        mock_content = Mock()
        mock_content.text = '{"titles": ["Custom Template Paper"]}'
        mock_message.content = [mock_content]
        
        mock_response.output = [mock_message]
        mock_client.responses.create.return_value = mock_response
        
        custom_template = """
        Custom search for: {{ query }}
        {% if conference_preference -%}
        From venues: {{ conference_preference }}
        {%- endif %}
        Return {{ max_results }} titles in JSON format.
        """
        
        result = openai_websearch_titles(
            queries=["deep learning"],
            max_results=3,
            sleep_sec=0.1,
            prompt_template=custom_template,
            conference_preference="CVPR, ICCV",
            client=mock_client,
        )
        
        assert result == ["Custom Template Paper"]
        
        # Check that custom template was used
        call_args = mock_client.responses.create.call_args
        prompt_text = call_args[1]["input"]
        assert "Custom search for: deep learning" in prompt_text
        assert "From venues: CVPR, ICCV" in prompt_text
