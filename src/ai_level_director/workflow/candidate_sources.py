"""Create level candidates from uploaded text and sample levels.

These factories build LevelCandidate objects from the non generated sources and
can persist a candidate's level text and a rendered preview. The generated source
(Project 5) is added later in its own adapter. Candidate creation is kept separate
from the workflow service so it can be built and tested on its own.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ai_level_director.domain.events import CandidateEvent
from ai_level_director.domain.models import LevelCandidate
from ai_level_director.domain.states import CandidateSource
from ai_level_director.storage import paths

# Single letter id prefix per source, so candidate ids read like "U-001".
SOURCE_PREFIX: dict[CandidateSource, str] = {
    "generated": "G",
    "uploaded": "U",
    "sample": "S",
    "revised": "R",
}

# The event type recorded when a candidate is first created, by source. The
# event vocabulary has no "sample" type, so a sample candidate records "created".
_CREATION_EVENT_TYPE: dict[CandidateSource, str] = {
    "generated": "generated",
    "uploaded": "uploaded",
    "sample": "created",
    "revised": "revision_created",
}


def utc_now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def next_candidate_id(existing_ids: list[str], source: CandidateSource) -> str:
    """Return the next candidate id for a source, like 'U-001'.

    Numbers are assigned per source prefix based on how many ids with that prefix
    already exist, so uploaded and sample candidates number independently.
    """
    prefix = SOURCE_PREFIX[source]
    count = sum(1 for cid in existing_ids if cid.startswith(prefix + "-"))
    return f"{prefix}-{count + 1:03d}"


def build_candidate(
    level_text: str,
    source: CandidateSource,
    title: str,
    candidate_id: str,
    created_at: str | None = None,
    parent_candidate_id: str | None = None,
    iteration_number: int = 1,
    generation_metadata: dict | None = None,
) -> LevelCandidate:
    """Build a draft LevelCandidate with one creation event in its history."""
    timestamp = created_at or utc_now_iso()
    event = CandidateEvent(
        event_id=f"{candidate_id}-evt-1",
        timestamp=timestamp,
        event_type=_CREATION_EVENT_TYPE[source],
        candidate_id=candidate_id,
        summary=f"Candidate {candidate_id} created from {source} source.",
    )
    return LevelCandidate(
        candidate_id=candidate_id,
        title=title,
        source=source,
        level_text=level_text,
        workflow_state="draft",
        parent_candidate_id=parent_candidate_id,
        iteration_number=iteration_number,
        generation_metadata=generation_metadata or {},
        created_at=timestamp,
        updated_at=timestamp,
        history=[event],
    )


def make_uploaded_candidate(
    level_text: str,
    candidate_id: str,
    title: str | None = None,
    created_at: str | None = None,
) -> LevelCandidate:
    """Create a candidate from designer uploaded or pasted level text."""
    return build_candidate(
        level_text, "uploaded", title or "Uploaded candidate", candidate_id, created_at
    )


def make_sample_candidate(
    level_text: str,
    candidate_id: str,
    title: str | None = None,
    created_at: str | None = None,
) -> LevelCandidate:
    """Create a candidate from a bundled sample level."""
    return build_candidate(
        level_text, "sample", title or "Sample candidate", candidate_id, created_at
    )


def make_generated_candidate(
    level_text: str,
    candidate_id: str,
    title: str | None = None,
    created_at: str | None = None,
    generation_metadata: dict | None = None,
) -> LevelCandidate:
    """Create a candidate from a Project 5 generated level chunk."""
    return build_candidate(
        level_text,
        "generated",
        title or "Generated candidate",
        candidate_id,
        created_at,
        generation_metadata=generation_metadata,
    )


def save_candidate_artifacts(
    candidate: LevelCandidate,
    session_id: str,
    output_root: Path | str = paths.DEFAULT_OUTPUT_ROOT,
) -> LevelCandidate:
    """Save the candidate's raw level text and return an updated copy.

    Writes the raw tile text to a ``.txt`` file, which is the authoritative
    artifact, and returns a copy of the candidate with ``level_path`` set. ASCII
    rendering is available for display via ``render_level_ascii``; image based
    previews are a deferred polish feature, so ``rendered_preview_path`` is left
    unset here.
    """
    root = Path(output_root)
    txt_path = paths.candidate_path(session_id, candidate.candidate_id, root)
    txt_path.parent.mkdir(parents=True, exist_ok=True)
    txt_path.write_text(candidate.level_text, encoding="utf-8")

    return candidate.model_copy(update={"level_path": str(txt_path)})
