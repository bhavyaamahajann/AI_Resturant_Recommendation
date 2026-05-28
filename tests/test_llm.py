from unittest.mock import patch, MagicMock
import pytest
from httpx import HTTPStatusError, Request, Response, TimeoutException
from src.services.llm import LLMGateway, LLMError


@pytest.fixture
def mock_settings():
    class MockSettings:
        llm_api_key = "test_key"
        llm_model = "llama-3.3-70b-versatile"
        llm_timeout_sec = 1
    return MockSettings()


@patch("src.services.llm.get_settings")
@patch("src.services.llm.httpx.Client.post")
def test_llm_gateway_success(mock_post, mock_get_settings, mock_settings):
    mock_get_settings.return_value = mock_settings
    
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"summary": "test"}'}}]
    }
    mock_post.return_value = mock_response

    gateway = LLMGateway()
    result = gateway.complete([{"role": "user", "content": "test"}])
    
    assert result == '{"summary": "test"}'
    mock_post.assert_called_once()


@patch("src.services.llm.get_settings")
@patch("src.services.llm.httpx.Client.post")
def test_llm_gateway_timeout_retry(mock_post, mock_get_settings, mock_settings):
    mock_get_settings.return_value = mock_settings
    
    mock_post.side_effect = [
        TimeoutException("Timeout"),
        MagicMock(status_code=200, json=lambda: {"choices": [{"message": {"content": "ok"}}]})
    ]

    gateway = LLMGateway()
    result = gateway.complete([])
    
    assert result == "ok"
    assert mock_post.call_count == 2


@patch("src.services.llm.get_settings")
@patch("src.services.llm.httpx.Client.post")
def test_llm_gateway_server_error_retry_failure(mock_post, mock_get_settings, mock_settings):
    mock_get_settings.return_value = mock_settings
    
    mock_post.return_value = MagicMock(status_code=502)

    gateway = LLMGateway()
    with pytest.raises(LLMError, match="status 502"):
        gateway.complete([])
    
    assert mock_post.call_count == 2
