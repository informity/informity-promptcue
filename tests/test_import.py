# promptcue | Smoke tests for public package imports and enum values
# Maintainer: Informity

from promptcue import (
    PromptCueActionHint,
    PromptCueAnalyzer,
    PromptCueBasis,
    PromptCueConfidenceBand,
    PromptCueConfig,
    PromptCueEmbedFn,
    PromptCueError,
    PromptCueModelLoadError,
    PromptCueQueryObject,
    PromptCueRegistryError,
    PromptCueRoutingHint,
    PromptCueScope,
)


def test_public_imports() -> None:
    assert PromptCueAnalyzer    is not None
    assert PromptCueConfig      is not None
    assert PromptCueQueryObject is not None
    assert PromptCueEmbedFn     is not None


def test_exception_imports() -> None:
    assert issubclass(PromptCueModelLoadError, PromptCueError)
    assert issubclass(PromptCueRegistryError,  PromptCueError)


def test_enum_imports() -> None:
    assert PromptCueScope.BROAD                          == 'broad'
    assert PromptCueRoutingHint.NEEDS_RETRIEVAL          == 'needs_retrieval'
    assert PromptCueRoutingHint.NEEDS_STRUCTURE          == 'needs_structure'
    assert PromptCueActionHint.CONVERSATIONAL            == 'should_respond_conversationally'
    assert PromptCueBasis.TRIGGER_MATCH                  == 'trigger_match'
    assert PromptCueBasis.BELOW_THRESHOLD                == 'below_threshold'
    assert PromptCueConfidenceBand.HIGH                  == 'high'
