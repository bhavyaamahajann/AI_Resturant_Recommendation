from config.settings import get_settings


def test_settings_load():
    settings = get_settings()
    assert settings.dataset_name
    assert settings.candidate_limit == 30
    assert settings.budget_low_percentile < settings.budget_medium_percentile
