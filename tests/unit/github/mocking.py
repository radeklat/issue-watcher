from time import time
from typing import List
from unittest.mock import MagicMock


def set_issue_state(req_mock: MagicMock, value: str, status_code: int = 200):
    mock_response = MagicMock()
    mock_response.json.return_value = {"state": value}
    mock_response.status_code = status_code
    req_mock.get.return_value = mock_response


def set_limit_exceeded(req_mock: MagicMock):
    mock_message = "Message from GitHub"
    mock_response = MagicMock()
    mock_response.json.return_value = {"message": mock_message}
    mock_response.status_code = 403
    mock_response.headers = {
        "X-RateLimit-Remaining": 0,
        "X-RateLimit-Limit": 60,
        "X-RateLimit-Reset": time() + 3600,
    }
    req_mock.get.return_value = mock_response


def set_number_of_releases_to(req_mock: MagicMock, count: int, status_code: int = 200):
    mock_response = MagicMock()
    mock_response.json.return_value = [{}] * count
    mock_response.status_code = status_code
    req_mock.get.return_value = mock_response


def set_git_tags_to(req_mock: MagicMock, tags: List[str], status_code: int = 200):
    mock_response = MagicMock()
    mock_response.json.return_value = [{"ref": f"refs/tags/{tag}"} for tag in tags]
    mock_response.status_code = status_code
    req_mock.get.return_value = mock_response
