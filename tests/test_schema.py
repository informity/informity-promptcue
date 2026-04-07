# promptcue | Tests for schema fields: scope, action_hints, entities, constraints
# Maintainer: Informity

import pytest

from promptcue import PromptCueAnalyzer, PromptCueConfig
from promptcue.constants import (
    PCUE_ACTION_CHECK_RECENCY,
    PCUE_ACTION_CLARIFY,
    PCUE_ACTION_COMPARE,
    PCUE_ACTION_CONVERSATIONAL,
    PCUE_ACTION_ENUMERATE,
    PCUE_ACTION_SURVEY,
    PCUE_SCOPE_BROAD,
    PCUE_SCOPE_COMPARATIVE,
    PCUE_SCOPE_EXPLORATORY,
    PCUE_SCOPE_FOCUSED,
    PCUE_SCOPE_UNKNOWN,
)
from promptcue.models.schema import PromptCueEntity

_VALID_SCOPES = {
    PCUE_SCOPE_BROAD, PCUE_SCOPE_FOCUSED,
    PCUE_SCOPE_COMPARATIVE, PCUE_SCOPE_EXPLORATORY, PCUE_SCOPE_UNKNOWN,
}


# ==============================================================================
# Scope field
# ==============================================================================

def test_scope_present_in_result() -> None:
    result = PromptCueAnalyzer().analyze('compare aurora and opensearch for rag')
    assert result.scope in _VALID_SCOPES


def test_comparison_query_is_comparative_scope() -> None:
    result = PromptCueAnalyzer().analyze('compare aurora and opensearch for rag')
    assert result.scope == PCUE_SCOPE_COMPARATIVE


def test_lookup_query_is_focused_scope() -> None:
    result = PromptCueAnalyzer().analyze('what is the default timeout for lambda')
    assert result.scope == PCUE_SCOPE_FOCUSED


def test_coverage_query_is_broad_scope() -> None:
    # 'tell me everything about' is a long trigger → det score 0.77 → stays deterministic
    result = PromptCueAnalyzer().analyze('tell me everything about serverless on aws')
    assert result.scope == PCUE_SCOPE_BROAD


def test_analysis_query_is_exploratory_scope() -> None:
    result = PromptCueAnalyzer().analyze(
        'evaluate this architecture and tell me if it is a good idea'
    )
    assert result.scope == PCUE_SCOPE_EXPLORATORY


def test_unknown_query_scope_is_unknown() -> None:
    # Gibberish with semantic disabled — deterministic scorer returns nothing above
    # threshold, so the decision engine should resolve to unknown scope.
    config = PromptCueConfig(enable_semantic_scoring=False)
    result = PromptCueAnalyzer(config).analyze('xyzzy qrstuv blorgh')
    assert result.scope == PCUE_SCOPE_UNKNOWN


# ==============================================================================
# Action hints field
# ==============================================================================

def test_action_hints_present_in_result() -> None:
    result = PromptCueAnalyzer().analyze('compare aurora and opensearch for rag')
    assert isinstance(result.action_hints, dict)
    assert len(result.action_hints) > 0


def test_comparison_query_has_should_compare() -> None:
    result = PromptCueAnalyzer().analyze('compare aurora and opensearch for rag')
    assert result.action_hints.get(PCUE_ACTION_COMPARE) is True


def test_procedure_query_has_should_enumerate() -> None:
    result = PromptCueAnalyzer().analyze('how do I set up a vpc with private subnets step by step')
    assert result.action_hints.get(PCUE_ACTION_ENUMERATE) is True


def test_update_query_has_should_check_recency() -> None:
    # Use a trigger that unambiguously maps to the update type.
    result = PromptCueAnalyzer().analyze('any recent updates to the aws cdk')
    assert result.action_hints.get(PCUE_ACTION_CHECK_RECENCY) is True


def test_chitchat_query_has_should_respond_conversationally() -> None:
    result = PromptCueAnalyzer().analyze('hello how are you')
    assert result.action_hints.get(PCUE_ACTION_CONVERSATIONAL) is True


def test_coverage_query_has_should_survey() -> None:
    result = PromptCueAnalyzer().analyze('give me an overview of this topic')
    assert result.action_hints.get(PCUE_ACTION_SURVEY) is True


def test_ambiguous_query_sets_should_clarify() -> None:
    # A query that produces two very close scores should set should_clarify in action_hints.
    # very wide margin — forces ambiguous classification on any query above threshold
    analyzer = PromptCueAnalyzer(PromptCueConfig(ambiguity_margin=0.99))
    result   = analyzer.analyze('compare aurora and opensearch for rag')
    if result.primary_query_type != 'unknown':
        assert result.action_hints.get(PCUE_ACTION_CLARIFY) is True


def test_below_threshold_sets_clarify_in_action_hints() -> None:
    # similarity_threshold=0.99 is unreachable → forces below-threshold path
    analyzer = PromptCueAnalyzer(PromptCueConfig(similarity_threshold=0.99))
    result   = analyzer.analyze('compare aurora and opensearch for rag')
    assert result.action_hints.get(PCUE_ACTION_CLARIFY) is True


# ==============================================================================
# Entities field (structured, populated when linguistic extraction enabled)
# ==============================================================================

def test_entities_empty_when_linguistic_disabled() -> None:
    result = PromptCueAnalyzer().analyze('compare aurora and opensearch for rag')
    assert result.entities == []


def _spacy_model_available() -> bool:
    try:
        import spacy
        spacy.load('en_core_web_sm')
        return True
    except (ImportError, OSError):
        return False

if not _spacy_model_available():
    pytest.skip(
        'spaCy or en_core_web_sm model not available — skipping entity tests',
        allow_module_level=True,
    )


def test_entities_are_promptcue_entity_instances() -> None:
    analyzer = PromptCueAnalyzer(PromptCueConfig(enable_linguistic_extraction=True))
    result   = analyzer.analyze('Compare Aurora and OpenSearch for RAG workloads on AWS')
    for entity in result.entities:
        assert isinstance(entity, PromptCueEntity)
        assert entity.text
        assert entity.entity_type


def test_entities_and_named_entities_are_consistent() -> None:
    analyzer = PromptCueAnalyzer(PromptCueConfig(enable_linguistic_extraction=True))
    result   = analyzer.analyze('Compare Aurora and OpenSearch for RAG workloads on AWS')
    # named_entities is the plain-text list derived from entities
    assert result.named_entities == [e.text for e in result.entities]


# ==============================================================================
# Constraints field (reserved, always empty in Phase 1)
# ==============================================================================

def test_constraints_field_is_present_and_empty() -> None:
    result = PromptCueAnalyzer().analyze('compare aurora and opensearch for rag')
    assert result.constraints == []


def test_confidence_meta_present_and_normalized() -> None:
    result = PromptCueAnalyzer().analyze('compare aurora and opensearch for rag')
    assert 0.0 <= result.confidence_meta.type_confidence_margin <= 1.0
    assert 0.0 <= result.confidence_meta.scope_confidence <= 1.0
    assert 0.0 <= result.confidence_meta.scope_confidence_margin <= 1.0


def test_semantic_hints_present() -> None:
    result = PromptCueAnalyzer().analyze('Compare yearly trends in incidents from 2021 to 2023.')
    assert isinstance(result.semantic_hints.mentions_multiple_items, bool)
    assert isinstance(result.semantic_hints.requests_structure, bool)
    assert result.semantic_hints.mentions_time is True
    assert result.semantic_hints.requires_multi_period_analysis is True



def test_explicit_recency_semantic_hint_present() -> None:
    result = PromptCueAnalyzer().analyze('Who is the current US president?')
    assert isinstance(result.semantic_hints.explicit_recency, bool)
    assert result.semantic_hints.explicit_recency is True
    assert result.routing_hints.get('needs_current_info') is True
    assert result.action_hints.get(PCUE_ACTION_CHECK_RECENCY) is True

def test_explanations_present() -> None:
    result = PromptCueAnalyzer().analyze('How do I configure Redis cache step by step?')
    assert isinstance(result.explanations.decision_notes, list)
    assert isinstance(result.explanations.evidence_tokens, list)
