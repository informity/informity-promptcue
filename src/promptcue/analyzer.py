# promptcue | Main orchestration entry point for PromptCue
# Maintainer: Informity

from __future__ import annotations

import asyncio
import re

from promptcue.config import PromptCueConfig
from promptcue.constants import (
    PCUE_DEFAULT_REGISTRY,
    PCUE_SCHEMA_VERSION,
)
from promptcue.core.classifier import PromptCueClassifier
from promptcue.core.decision import PromptCueDecisionEngine
from promptcue.core.registry import PromptCueRegistry
from promptcue.extraction.keywords import PromptCueKeywordExtractor
from promptcue.extraction.language import PromptCueLanguageDetector
from promptcue.extraction.linguistic import PromptCueLinguisticExtractor
from promptcue.extraction.normalization import normalize_text
from promptcue.models.enums import (
    PromptCueActionHint,
    PromptCueBasis,
    PromptCueContinuationSignal,
    PromptCueDiscourseSignal,
    PromptCueFollowupSignal,
    PromptCueOutputFormat,
    PromptCueRoutingHint,
    PromptCueScope,
    PromptCueTopicShiftSignal,
)
from promptcue.models.schema import (
    PromptCueConfidenceMeta,
    PromptCueExplanations,
    PromptCuePromptSignals,
    PromptCueQueryObject,
    PromptCueSemanticHints,
)
from promptcue.patterns import (
    COMPARISON_PATTERNS,
    CONTINUATION_PATTERNS,
    CONTINUATION_REQUEST_PATTERNS,
    DISCOURSE_PREFIX_PATTERN,
    ENUMERATION_PATTERNS,
    EXPLICIT_RECENCY_PATTERNS,
    MULTI_ITEM_PATTERNS,
    MULTI_PERIOD_PATTERNS,
    OUTPUT_FORMAT_PATTERNS,
    REFERENTIAL_FOLLOWUP_PATTERN,
    STRUCTURE_PATTERNS,
    SYNTHESIS_PATTERNS,
    TEMPORAL_SCOPE_PATTERNS,
    TOPIC_SHIFT_CUE_PATTERN,
    YEAR_TOKEN_PATTERN,
)

# ==============================================================================
# Pre-classification detectors — pure regex, no model dependency
# ==============================================================================


def _detect_continuation(text: str) -> bool:
    """Return True when text appears to be a follow-up turn in a conversation.

    Uses leading-phrase regex patterns only — no model dependency.
    Does not change primary_query_type; purely informational for callers
    that maintain session context.
    """
    return any(pat.search(text) for pat in CONTINUATION_PATTERNS)


def _detect_needs_structure(text: str) -> bool:
    """Return True when text contains explicit output-structure directives.

    Matches Markdown heading patterns, 'format as table', 'in bullet points',
    'with sections:', etc.  These indicate the caller has prescribed a response
    format, which downstream generators should respect.
    """
    return any(pat.search(text) for pat in STRUCTURE_PATTERNS)


def _strip_discourse_prefix(text: str) -> tuple[str, bool]:
    stripped = DISCOURSE_PREFIX_PATTERN.sub("", text, count=1).strip(" ,:;-")
    if stripped and stripped != text:
        return stripped, True
    return text, False


def _detect_topic_shift_cue(text: str) -> bool:
    return bool(TOPIC_SHIFT_CUE_PATTERN.search(text))


def _detect_referential_followup(text: str) -> bool:
    return bool(REFERENTIAL_FOLLOWUP_PATTERN.search(text))


def _detect_continuation_request(text: str) -> bool:
    return any(pat.search(text) for pat in CONTINUATION_REQUEST_PATTERNS)


def _detect_output_formats(text: str) -> list[PromptCueOutputFormat]:
    formats: list[PromptCueOutputFormat] = []
    for key, pattern in OUTPUT_FORMAT_PATTERNS.items():
        if pattern.search(text):
            formats.append(PromptCueOutputFormat(key))
    return formats


def _detect_explicit_recency(text: str) -> bool:
    """Return True when text explicitly asks for up-to-date/current information."""
    return any(pat.search(text) for pat in EXPLICIT_RECENCY_PATTERNS)


def _detect_mentions_time(text: str) -> bool:
    """Return True when text references a specific time period or temporal aggregation.

    Covers year references (2020, 2021...), year-over-year phrases, multi-year
    duration phrases ("over the last 3 years"), year ranges, and periodic trend
    phrases.  Pure regex — no model dependency.

    Populates the generic semantic hint `mentions_time`.
    """
    return any(pat.search(text) for pat in TEMPORAL_SCOPE_PATTERNS)


def _detect_requires_multi_period_analysis(text: str) -> bool:
    """Return True for prompts that explicitly require analysis across periods."""
    if any(pat.search(text) for pat in MULTI_PERIOD_PATTERNS):
        return True
    years = YEAR_TOKEN_PATTERN.findall(text)
    return len(set(years)) >= 2


def _detect_mentions_multiple_items(text: str) -> bool:
    return any(pat.search(text) for pat in MULTI_ITEM_PATTERNS)


def _detect_requests_comparison(text: str) -> bool:
    return any(pat.search(text) for pat in COMPARISON_PATTERNS)


def _detect_requests_enumeration(text: str) -> bool:
    return any(pat.search(text) for pat in ENUMERATION_PATTERNS)


def _detect_requests_synthesis(text: str) -> bool:
    return any(pat.search(text) for pat in SYNTHESIS_PATTERNS)


def _extract_evidence_tokens(text: str, limit: int = 8) -> list[str]:
    seen: set[str] = set()
    tokens: list[str] = []
    for token in re.findall(r"[a-z0-9][a-z0-9_-]{2,}", text.casefold()):
        if token in seen:
            continue
        seen.add(token)
        tokens.append(token)
        if len(tokens) >= limit:
            break
    return tokens


def _should_promote_to_coverage(
    *,
    primary_label: str,
    hints: PromptCueSemanticHints,
    requests_synthesis: bool,
) -> bool:
    """Promote focused-family intents to coverage when prompt shape is clearly broad synthesis.

    This keeps routing model-agnostic while preventing lookup/procedure drift on
    prompts that explicitly request corpus-wide aggregation/structured survey output.
    """
    if primary_label not in {
        "lookup",
        "procedure",
        "troubleshooting",
        "recommendation",
        "validation",
        "update",
        "unknown",
    }:
        return False
    if not hints.mentions_multiple_items:
        return False
    return bool(
        hints.requests_structure
        or hints.requests_enumeration
        or hints.requires_multi_period_analysis
        or hints.requests_comparison
        or requests_synthesis
    )


class PromptCueAnalyzer:
    """Public entry point for query understanding."""

    def __init__(self, config: PromptCueConfig | None = None) -> None:
        self.config = config or PromptCueConfig()
        registry_path = self.config.registry_path or PCUE_DEFAULT_REGISTRY
        self.registry = PromptCueRegistry.from_yaml(registry_path)
        self.classifier = PromptCueClassifier(self.registry, self.config)
        self.decision_engine = PromptCueDecisionEngine(self.config, self.registry)
        self.language_detector = PromptCueLanguageDetector(
            enabled=self.config.enable_language_detection,
        )
        self.linguistic_extractor = PromptCueLinguisticExtractor(
            enabled=self.config.enable_linguistic_extraction,
            model_name=self.config.spacy_model,
        )
        self.keyword_extractor = PromptCueKeywordExtractor(
            enabled=self.config.enable_keyword_extraction,
            max_keywords=self.config.max_keywords,
        )

    # ==============================================================================
    # Public
    # ==============================================================================

    def warm_up(self) -> None:
        """Pre-load all optional models at application startup.

        Covers:
        - Sentence-transformer embedding model (when enable_semantic_scoring=True)
        - spaCy language model (when enable_linguistic_extraction=True)
        - KeyBERT model (when enable_keyword_extraction=True)
        - langdetect library (when enable_language_detection=True)

        Safe to call when none of the above are enabled — each component
        guards internally and becomes a no-op when disabled.
        """
        self.classifier.warm_up()
        self.linguistic_extractor.warm_up()
        self.keyword_extractor.warm_up()
        self.language_detector.warm_up()

    async def warm_up_async(self) -> None:
        """Async equivalent of warm_up() — safe to await from any async startup handler.

        Runs warm_up() in a thread-pool executor so the event loop is not
        blocked while models are loading (~10–15 s on first run, ~1–2 s
        when models are cached locally).
        """
        await asyncio.to_thread(self.warm_up)

    async def analyze_async(self, text: str) -> PromptCueQueryObject:
        """Async equivalent of analyze() — safe to await from any async context.

        Runs analyze() in a thread-pool executor so ML inference does not
        block the event loop.  Models must be loaded before calling this
        (call warm_up_async() at startup) otherwise the first request will
        pay the full model-load cost inside the executor.
        """
        return await asyncio.to_thread(self.analyze, text)

    def analyze(self, text: str) -> PromptCueQueryObject:
        """Analyze a natural-language query and return a structured PromptCueQueryObject."""
        normalized = normalize_text(text)
        _, has_discourse_prefix = _strip_discourse_prefix(normalized)
        language = self.language_detector.detect(normalized)

        # Pre-classification structural signals — pure regex, no model dependency.
        is_continuation = _detect_continuation(normalized)
        needs_structure = _detect_needs_structure(text)  # use raw text for Markdown patterns
        mentions_time = _detect_mentions_time(normalized)
        explicit_recency = _detect_explicit_recency(normalized)
        requires_multi_period_analysis = _detect_requires_multi_period_analysis(normalized)
        mentions_multiple_items = _detect_mentions_multiple_items(normalized)
        requests_comparison = _detect_requests_comparison(normalized)
        requests_enumeration = _detect_requests_enumeration(normalized)
        requests_synthesis = _detect_requests_synthesis(normalized)
        has_topic_shift_cue = _detect_topic_shift_cue(normalized)
        has_referential_followup = _detect_referential_followup(normalized)
        requests_continuation = _detect_continuation_request(normalized)
        requested_output_formats = _detect_output_formats(text)

        classification = self.classifier.classify(normalized)

        # Use the semantic threshold only when the classifier actually ran the
        # semantic path — deterministic results should be evaluated against the
        # deterministic threshold.
        top_basis = classification.candidates[0].basis if classification.candidates else None
        threshold = (
            self.config.semantic_similarity_threshold
            if top_basis == PromptCueBasis.SEMANTIC
            else None
        )

        decision = self.decision_engine.resolve(classification, threshold_override=threshold)
        linguistic = self.linguistic_extractor.extract(normalized)
        keywords = self.keyword_extractor.extract(normalized)

        # Merge computed routing hints on top of YAML-derived hints from the decision engine.
        routing_hints = {
            **decision.routing_hints,
            PromptCueRoutingHint.NEEDS_STRUCTURE: needs_structure,
            PromptCueRoutingHint.NEEDS_CURRENT_INFO: (
                bool(decision.routing_hints.get(PromptCueRoutingHint.NEEDS_CURRENT_INFO))
                or explicit_recency
            ),
        }
        action_hints = {
            **decision.action_hints,
            PromptCueActionHint.CHECK_RECENCY: (
                bool(decision.action_hints.get(PromptCueActionHint.CHECK_RECENCY))
                or explicit_recency
            ),
        }

        prompt_signals = PromptCuePromptSignals(
            has_discourse_prefix=has_discourse_prefix,
            has_topic_shift_cue=has_topic_shift_cue,
            has_referential_followup=has_referential_followup,
            requests_continuation=requests_continuation,
            requested_output_formats=requested_output_formats,
            discourse_signal=(
                PromptCueDiscourseSignal.PREFIX
                if has_discourse_prefix
                else PromptCueDiscourseSignal.NONE
            ),
            topic_shift_signal=(
                PromptCueTopicShiftSignal.EXPLICIT_CUE
                if has_topic_shift_cue
                else PromptCueTopicShiftSignal.NONE
            ),
            followup_signal=(
                PromptCueFollowupSignal.REFERENTIAL
                if has_referential_followup
                else PromptCueFollowupSignal.NONE
            ),
            continuation_signal=(
                PromptCueContinuationSignal.REQUEST
                if requests_continuation
                else PromptCueContinuationSignal.NONE
            ),
        )

        semantic_hints = PromptCueSemanticHints(
            mentions_multiple_items=mentions_multiple_items,
            requests_comparison=requests_comparison,
            requests_enumeration=requests_enumeration,
            requests_structure=needs_structure,
            mentions_time=mentions_time,
            explicit_recency=explicit_recency,
            requires_multi_period_analysis=requires_multi_period_analysis,
        )

        primary_label = decision.primary_label
        scope = decision.scope
        decision_notes = list(decision.decision_notes)
        if _should_promote_to_coverage(
            primary_label=primary_label,
            hints=semantic_hints,
            requests_synthesis=requests_synthesis,
        ):
            primary_label = "coverage"
            scope = PromptCueScope.BROAD
            routing_hints[PromptCueRoutingHint.NEEDS_RETRIEVAL] = True
            decision_notes.append("promoted_to_coverage_by_semantic_hints")

        return PromptCueQueryObject(
            schema_version=PCUE_SCHEMA_VERSION,
            input_text=text,
            normalized_text=normalized,
            language=language,
            is_continuation=is_continuation,
            primary_query_type=primary_label,
            classification_basis=decision.classification_basis,
            candidate_query_types=classification.candidates,
            confidence=decision.confidence,
            confidence_band=decision.confidence_band,
            ambiguity_score=decision.ambiguity_score,
            confidence_meta=PromptCueConfidenceMeta(
                type_confidence_margin=decision.type_confidence_margin,
                scope_confidence=decision.scope_confidence,
                scope_confidence_margin=decision.scope_confidence_margin,
            ),
            scope=scope,
            main_verbs=linguistic.main_verbs,
            noun_phrases=linguistic.noun_phrases,
            entities=linguistic.entities,
            keywords=keywords,
            routing_hints=routing_hints,
            action_hints=action_hints,
            semantic_hints=semantic_hints,
            prompt_signals=prompt_signals,
            explanations=PromptCueExplanations(
                decision_notes=decision_notes,
                evidence_tokens=_extract_evidence_tokens(normalized),
            ),
        )
