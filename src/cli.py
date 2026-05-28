from __future__ import annotations
import argparse
import sys
from pydantic import ValidationError

from config.settings import get_settings
from src.data.models import BudgetTier
from src.data.preferences import UserPreferences
from src.data.store import RestaurantStore
from src.services.filter import CandidateFilterService, NoCandidatesError
from src.services.prompt import PromptBuilder
from src.services.llm import LLMGateway, LLMError
from src.services.parser import LLMParser


def _setup_parser() -> argparse.ArgumentParser:
    settings = get_settings()
    parser = argparse.ArgumentParser(
        description="Restaurant Recommendation CLI (Filter-Only MVP)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--location",
        type=str,
        required=True,
        help="City or location for recommendations",
    )
    parser.add_argument(
        "--budget",
        type=str,
        required=True,
        choices=[b.value for b in BudgetTier],
        help="Budget tier: $, $$, $$$, or $$$$",
    )
    parser.add_argument(
        "--cuisine",
        type=str,
        action="append",
        required=True,
        help="Preferred cuisine (can be specified multiple times)",
    )
    parser.add_argument(
        "--min-rating",
        type=float,
        default=None,
        help="Minimum rating (0.0 to 5.0)",
    )
    parser.add_argument(
        "--extras",
        type=str,
        action="append",
        default=[],
        help="Extra preferences (can be specified multiple times)",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=settings.default_top_n,
        help="Number of recommendations to return (1-20)",
    )
    return parser


def main(args: list[str] | None = None) -> int:
    parser = _setup_parser()
    parsed_args = parser.parse_args(args)

    try:
        preferences = UserPreferences(
            location=parsed_args.location,
            budget=BudgetTier(parsed_args.budget),
            cuisines=parsed_args.cuisine,
            min_rating=parsed_args.min_rating,
            extras=parsed_args.extras,
            top_n=parsed_args.top_n,
        )
    except ValidationError as e:
        print("Validation Error:", file=sys.stderr)
        for err in e.errors():
            loc = ".".join(str(l) for l in err["loc"])
            print(f"  {loc}: {err['msg']}", file=sys.stderr)
        return 1

    try:
        settings = get_settings()
        store = RestaurantStore.from_parquet(settings.data_path)
    except Exception as e:
        print(f"Failed to load data store: {e}", file=sys.stderr)
        return 1

    filter_service = CandidateFilterService(store=store, settings=settings)

    try:
        candidates = filter_service.get_candidates(preferences)
    except NoCandidatesError as e:
        print(f"No results found: {e}", file=sys.stderr)
        if e.suggestions:
            print(f"Suggestions: {', '.join(e.suggestions)}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error filtering candidates: {e}", file=sys.stderr)
        return 1

    print("Generating AI recommendations... ", end="", flush=True)

    try:
        messages = PromptBuilder.build(preferences, candidates.restaurants, preferences.top_n)
        gateway = LLMGateway()
        llm_response = gateway.complete(messages)
        result = LLMParser.parse_and_enrich(llm_response, candidates, preferences)
        print("Done!\n")
    except LLMError as e:
        print(f"Failed! ({e})")
        print("Falling back to deterministic ranking...\n")
        result = LLMParser.deterministic_fallback(candidates, preferences)

    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    if result.summary:
        print(f"Summary: {result.summary}")
        print("-" * 80)

    print(
        f"{'Rank':<5} | {'Name':<25} | {'Cuisine':<20} | {'Rating':<6} | {'Cost':<6} | {'Explanation'}"
    )
    print("-" * 80)

    for r in result.recommendations:
        # Format the values
        name = (r.name[:22] + "...") if len(r.name) > 25 else r.name
        cuisine = (
            (r.cuisine[:17] + "...")
            if len(r.cuisine) > 20
            else r.cuisine
        )
        rating_str = f"{r.rating:.1f}" if r.rating is not None else "N/A"
        cost_str = f"{r.estimated_cost:.0f}" if r.estimated_cost is not None else "N/A"
        
        explanation = (r.explanation[:25] + "...") if len(r.explanation) > 28 else r.explanation

        print(
            f"{r.rank:<5} | {name:<25} | {cuisine:<20} | {rating_str:<6} | {cost_str:<6} | {explanation}"
        )

    if result.metadata.warnings:
        print("\nWarnings:")
        for w in result.metadata.warnings:
            print(f"  - {w}")

    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
