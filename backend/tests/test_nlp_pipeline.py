import os

os.environ["NLP_MODE"] = "rules"
os.environ["NLP_TREND_CLUSTERING"] = "off"

from app.nlp.pipeline import analyze_headline


def test_rules_pipeline_classifies_macro_headline() -> None:
    analysis = analyze_headline("Fed signals inflation may keep rates higher for longer")
    assert analysis.category == "macro"
    assert analysis.method == "rules"
    assert analysis.sentiment in {"positive", "negative", "neutral"}


def test_rules_pipeline_detects_single_stock() -> None:
    analysis = analyze_headline("Nvidia beats estimates as AI chip demand accelerates")
    assert analysis.category == "single_stock"
    assert analysis.ticker == "NVDA"
