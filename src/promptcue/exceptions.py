# promptcue | PromptCue-specific exception hierarchy
# Maintainer: Informity


class PromptCueError(Exception):
    """Base exception for all PromptCue errors."""


class PromptCueRegistryError(PromptCueError):
    """Raised when the query type registry cannot be loaded."""


class PromptCueModelLoadError(PromptCueError):
    """Raised when the sentence-transformers model cannot be loaded.

    This is a hard failure — PromptCue does not degrade to deterministic-only
    mode.  Classification without semantic scoring is not production-quality.
    Ensure the model is pre-downloaded and accessible at the configured cache
    path before calling warm_up() or analyze().
    """

    def __init__(self, model_name: str, cache_path: str, cause: BaseException) -> None:
        self.model_name  = model_name
        self.cache_path  = cache_path
        self.cause       = cause
        super().__init__(
            f'Failed to load sentence-transformers model {model_name!r} '
            f'from cache path {cache_path!r}.\n'
            f'Ensure the model is pre-downloaded before starting the service:\n'
            f'  python -c "from sentence_transformers import SentenceTransformer; '
            f'SentenceTransformer({model_name!r})"\n'
            f'Cause: {cause}'
        )
