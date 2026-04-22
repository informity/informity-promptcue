# promptcue | Pydantic models for PromptCue public schema
# Maintainer: Informity

from __future__ import annotations

from pydantic import BaseModel, Field

from promptcue.constants import (
    PCUE_SCHEMA_VERSION,
)
from promptcue.models.enums import (
    PromptCueActionHint,
    PromptCueBasis,
    PromptCueConfidenceBand,
    PromptCueContinuationSignal,
    PromptCueDiscourseSignal,
    PromptCueFollowupSignal,
    PromptCueOutputFormat,
    PromptCueRoutingHint,
    PromptCueScope,
    PromptCueTopicShiftSignal,
)


class PromptCueCandidate(BaseModel):
    """A scored candidate query type from the classifier."""

    label: str
    score: float = Field(ge=0.0, le=1.0)
    basis: PromptCueBasis = PromptCueBasis.FALLBACK


class PromptCueEntity(BaseModel):
    """A named entity extracted by spaCy — surface text plus entity type."""

    text: str
    entity_type: str  # spaCy label: ORG, PRODUCT, GPE, PERSON, DATE, etc.


class PromptCueKeyword(BaseModel):
    """A keyword or keyphrase extracted by KeyBERT."""

    text: str
    weight: float = Field(ge=0.0, le=1.0)
    kind: str = "keyphrase"


class PromptCueLinguistics(BaseModel):
    """Linguistic features extracted from a query."""

    main_verbs: list[str] = Field(default_factory=list)
    noun_phrases: list[str] = Field(default_factory=list)
    entities: list[PromptCueEntity] = Field(default_factory=list)  # structured (text + type)


class PromptCueConfidenceMeta(BaseModel):
    """Generic confidence diagnostics for downstream policy decisions."""

    type_confidence_margin: float = Field(ge=0.0, le=1.0, default=0.0)
    scope_confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    scope_confidence_margin: float = Field(ge=0.0, le=1.0, default=0.0)


class PromptCueSemanticHints(BaseModel):
    """Agnostic semantic cues inferred from the input prompt."""

    mentions_multiple_items: bool = False
    requests_comparison: bool = False
    requests_enumeration: bool = False
    requests_structure: bool = False
    mentions_time: bool = False
    explicit_recency: bool = False
    requires_multi_period_analysis: bool = False


class PromptCuePromptSignals(BaseModel):
    """Generic prompt-shape signals for downstream policy layers."""

    has_discourse_prefix: bool = False
    has_topic_shift_cue: bool = False
    has_referential_followup: bool = False
    requests_continuation: bool = False
    requested_output_formats: list[PromptCueOutputFormat] = Field(default_factory=list)

    discourse_signal: PromptCueDiscourseSignal = PromptCueDiscourseSignal.NONE
    topic_shift_signal: PromptCueTopicShiftSignal = PromptCueTopicShiftSignal.NONE
    followup_signal: PromptCueFollowupSignal = PromptCueFollowupSignal.NONE
    continuation_signal: PromptCueContinuationSignal = PromptCueContinuationSignal.NONE


class PromptCueExplanations(BaseModel):
    """Compact human-readable rationale for debugging and observability."""

    decision_notes: list[str] = Field(default_factory=list)
    evidence_tokens: list[str] = Field(default_factory=list)


class PromptCueQueryObject(BaseModel):
    """Structured understanding of a single query — the public output of PromptCueAnalyzer."""

    # ==============================================================================
    # Identity and versioning
    # ==============================================================================
    schema_version: str = PCUE_SCHEMA_VERSION
    input_text: str
    normalized_text: str
    language: str

    # ==============================================================================
    # Pre-classification signals
    # Populated before the classifier runs — pure structural / regex checks.
    # ==============================================================================
    is_continuation: bool = False

    # ==============================================================================
    # Classification
    # ==============================================================================
    primary_query_type: str
    classification_basis: PromptCueBasis = PromptCueBasis.FALLBACK
    candidate_query_types: list[PromptCueCandidate] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_band: PromptCueConfidenceBand = PromptCueConfidenceBand.LOW
    ambiguity_score: float = Field(ge=0.0, le=1.0)
    confidence_meta: PromptCueConfidenceMeta = Field(default_factory=PromptCueConfidenceMeta)

    @property
    def runner_up(self) -> PromptCueCandidate | None:
        """Second-ranked candidate, or None when fewer than two candidates exist."""
        return self.candidate_query_types[1] if len(self.candidate_query_types) > 1 else None

    # ==============================================================================
    # Query dimensions
    # ==============================================================================
    scope: PromptCueScope = PromptCueScope.UNKNOWN

    # ==============================================================================
    # Linguistic enrichment (populated when enable_linguistic_extraction=True)
    # ==============================================================================
    main_verbs: list[str] = Field(default_factory=list)
    noun_phrases: list[str] = Field(default_factory=list)
    entities: list[PromptCueEntity] = Field(default_factory=list)  # structured (text + type)

    # ==============================================================================
    # Keyword enrichment (populated when enable_keyword_extraction=True)
    # ==============================================================================
    keywords: list[PromptCueKeyword] = Field(default_factory=list)

    # ==============================================================================
    # Routing and action directives
    # ==============================================================================
    routing_hints: dict[PromptCueRoutingHint, bool] = Field(default_factory=dict)
    action_hints: dict[PromptCueActionHint, bool] = Field(default_factory=dict)

    # ==============================================================================
    # Constraints (reserved — populated in future milestones)
    # ==============================================================================
    constraints: list[str] = Field(default_factory=list)
    semantic_hints: PromptCueSemanticHints = Field(default_factory=PromptCueSemanticHints)
    prompt_signals: PromptCuePromptSignals = Field(default_factory=PromptCuePromptSignals)
    explanations: PromptCueExplanations = Field(default_factory=PromptCueExplanations)

    @property
    def query_type(self) -> str:
        """Compatibility alias for tests and simpler consumers."""
        return self.primary_query_type

    def to_routing_dict(self) -> dict[str, bool]:
        """Return a flat dict merging routing_hints and action_hints.

        Convenience method for callers that only need the combined hint surface
        without inspecting the full PromptCueQueryObject.  routing_hints keys take
        priority when the same key appears in both dicts.
        """
        merged = {
            **{str(k): v for k, v in self.action_hints.items()},
            **{str(k): v for k, v in self.routing_hints.items()},
        }
        return merged
