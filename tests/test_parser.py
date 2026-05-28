import json
from src.data.models import BudgetTier, Restaurant
from src.data.preferences import CandidateList, CandidateMetadata, UserPreferences
from src.services.parser import LLMParser


def test_extract_json():
    text = "```json\n{\"test\": 123}\n```"
    extracted = LLMParser._extract_json(text)
    assert extracted == "{\"test\": 123}"

    text2 = "Here is the json:\n```\n{\"a\": 1}\n```"
    assert LLMParser._extract_json(text2) == "{\"a\": 1}"


def test_parse_and_enrich_valid():
    r1 = Restaurant(
        id="1",
        name="Test Rest",
        location="Bangalore",
        location_normalized="bangalore",
        cuisines=["Italian"],
        rating=4.5,
        cost_estimate=1200,
        budget_tier=BudgetTier.MEDIUM
    )
    prefs = UserPreferences(location="Bangalore", budget=BudgetTier.MEDIUM, cuisine="Italian", top_n=1)
    candidates = CandidateList(
        preferences=prefs,
        restaurants=[r1],
        metadata=CandidateMetadata()
    )

    llm_resp = json.dumps({
        "summary": "Great picks",
        "recommendations": [
            {
                "restaurant_id": "1",
                "rank": 1,
                "explanation": "Because it's italian"
            }
        ]
    })

    res = LLMParser.parse_and_enrich(llm_resp, candidates, prefs)
    assert res.summary == "Great picks"
    assert len(res.recommendations) == 1
    assert res.recommendations[0].name == "Test Rest"
    assert res.recommendations[0].explanation == "Because it's italian"


def test_parse_and_enrich_hallucination_fallback():
    r1 = Restaurant(
        id="1",
        name="Test Rest",
        location="Bangalore",
        location_normalized="bangalore",
        cuisines=["Italian"],
        rating=4.5,
        cost_estimate=1200,
        budget_tier=BudgetTier.MEDIUM
    )
    prefs = UserPreferences(location="Bangalore", budget=BudgetTier.MEDIUM, cuisine="Italian", top_n=1)
    candidates = CandidateList(
        preferences=prefs,
        restaurants=[r1],
        metadata=CandidateMetadata()
    )

    llm_resp = json.dumps({
        "summary": "Great picks",
        "recommendations": [
            {
                "restaurant_id": "unknown_id",
                "rank": 1,
                "explanation": "Fake place"
            }
        ]
    })

    res = LLMParser.parse_and_enrich(llm_resp, candidates, prefs)
    # Since ID is hallucinated and name doesn't match, it should fallback
    assert len(res.recommendations) == 1
    assert res.recommendations[0].name == "Test Rest"
    assert "AI generation failed" in res.metadata.warnings[-1]


def test_parse_and_enrich_invalid_json():
    r1 = Restaurant(
        id="1",
        name="Test Rest",
        location="Bangalore",
        location_normalized="bangalore",
        cuisines=["Italian"],
        rating=4.5,
        cost_estimate=1200,
        budget_tier=BudgetTier.MEDIUM
    )
    prefs = UserPreferences(location="Bangalore", budget=BudgetTier.MEDIUM, cuisine="Italian", top_n=1)
    candidates = CandidateList(
        preferences=prefs,
        restaurants=[r1],
        metadata=CandidateMetadata()
    )

    llm_resp = "This is not json."

    res = LLMParser.parse_and_enrich(llm_resp, candidates, prefs)
    # Should use fallback
    assert len(res.recommendations) == 1
    assert "AI generation failed" in res.metadata.warnings[-1]
