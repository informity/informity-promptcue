from promptcue import (
    PromptCueActionHint,
    PromptCueAnalyzer,
    PromptCueConfig,
    PromptCueQueryObject,
    PromptCueRoutingHint,
    PromptCueScope,
)


def test_public_imports() -> None:
    assert PromptCueAnalyzer    is not None
    assert PromptCueConfig      is not None
    assert PromptCueQueryObject is not None


def test_enum_imports() -> None:
    assert PromptCueScope.BROAD                        == 'broad'
    assert PromptCueRoutingHint.NEEDS_RETRIEVAL        == 'needs_retrieval'
    assert PromptCueActionHint.CONVERSATIONAL          == 'should_respond_conversationally'
