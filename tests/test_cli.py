import pytest
from unittest.mock import patch, MagicMock

from src.cli import main
from config.settings import Settings
from pathlib import Path


from src.services.llm import LLMError


@pytest.fixture
def mock_settings():
    fixture_path = Path(__file__).parent / "fixtures" / "restaurants_small.parquet"
    settings = Settings(data_path=fixture_path, candidate_limit=30, default_top_n=5)
    settings.llm_api_key = "" # Force fallback for deterministic testing
    return settings


@patch("src.services.llm.LLMGateway.complete")
@patch("config.settings.get_settings")
def test_cli_valid_args(mock_get_settings, mock_complete, mock_settings, capsys):
    mock_get_settings.return_value = mock_settings
    mock_complete.side_effect = LLMError("Mocked LLM error")
    if not mock_settings.data_path.exists():
        pytest.skip("Run: python scripts/generate_test_fixture.py")

    args = [
        "--location",
        "Bangalore",
        "--budget",
        "medium",
        "--cuisine",
        "Italian",
        "--min-rating",
        "4.0",
        "--top-n",
        "3",
    ]

    exit_code = main(args)
    assert exit_code == 0

    captured = capsys.readouterr()
    # Check that output includes some key terms
    assert "RECOMMENDATIONS" in captured.out
    assert "Matches your Italian pre" in captured.out
    assert "Rank" in captured.out


@patch("config.settings.get_settings")
def test_cli_invalid_budget(mock_get_settings, mock_settings, capsys):
    mock_get_settings.return_value = mock_settings

    args = [
        "--location",
        "Bangalore",
        "--budget",
        "invalid_budget",
        "--cuisine",
        "Italian",
    ]

    with pytest.raises(SystemExit):
        # argparse will call sys.exit(2)
        main(args)
    
    captured = capsys.readouterr()
    assert "error: argument --budget: invalid choice" in captured.err


@patch("config.settings.get_settings")
def test_cli_missing_required_args(mock_get_settings, mock_settings, capsys):
    mock_get_settings.return_value = mock_settings

    args = ["--location", "Bangalore"]

    with pytest.raises(SystemExit):
        main(args)
        
    captured = capsys.readouterr()
    assert "the following arguments are required: --budget, --cuisine" in captured.err


@patch("config.settings.get_settings")
def test_cli_validation_error(mock_get_settings, mock_settings, capsys):
    mock_get_settings.return_value = mock_settings
    
    args = [
        "--location",
        "Bangalore",
        "--budget",
        "medium",
        "--cuisine",
        "Italian",
        "--top-n",
        "-1",  # Invalid top_n
    ]

    exit_code = main(args)
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Validation Error" in captured.err
    assert "top_n" in captured.err


@patch("config.settings.get_settings")
def test_cli_no_results(mock_get_settings, mock_settings, capsys):
    mock_get_settings.return_value = mock_settings
    if not mock_settings.data_path.exists():
        pytest.skip("Run: python scripts/generate_test_fixture.py")

    args = [
        "--location",
        "Atlantis",  # Unknown location
        "--budget",
        "high",
        "--cuisine",
        "Martian",
    ]

    exit_code = main(args)
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "No results found" in captured.err
