"""Curated design knowledge injected into the agents.

A concise block of research informed level design guidance, written in our own
words, that is injected into the Triage Director and Critic instructions so they
reason with real design knowledge rather than the model's training data alone. The
deterministic tools measure the facts; this guidance tells the agents how to
interpret and act on them. The formal citations live in the report References.
"""

from __future__ import annotations

DESIGN_GUIDANCE = """\
Level design knowledge to ground your reasoning. Apply it to the tool facts and
the designer's intent. Do not just restate the numbers.

Interpreting intent in context:
- Whether a fact is a problem depends on the brief. Low novelty is fine when the
  designer asked for consistency with an existing style, but a concern when they
  asked for something fresh. Judge each fact against the stated intent, not against
  a fixed threshold.

When to recommend revision:
- Recommend a change only to fix a diagnosed problem that conflicts with the
  intent. If the candidate is valid, on target, and has no issue that matters for
  the brief, accept it for playtest. Do not invent work on a sound level.

Pacing and rhythm, read relative to the target:
- For a medium or hard segment, intensity that ramps toward the end reads as good
  pacing, and a front loaded opening reads as weak. For an easy or beginner
  segment, low and fairly flat intensity is appropriate. Do not add challenge to an
  easy segment just to make its pacing ramp.
- A short calmer stretch after an intense one lets the player recover.

Safe zone for beginners:
- An easy or beginner segment should open with a short safe stretch before the
  first hazard, so the player can orient. A challenge in the first few columns of a
  beginner level is too abrupt.

Leniency and layered hazards:
- Difficulty is local as well as global. A short window that combines a gap with an
  enemy or cannon is a low leniency moment that can frustrate beginners even when
  the overall difficulty is low. For easy targets, prefer separating layered
  hazards rather than stacking them.

Guidance and affordance:
- Layout communicates. Coins placed along a jump arc or ahead of a hazard act as
  visual cues that guide the player toward the intended path. Use this when
  prescribing edits, even where there is no metric for it.

Structural integrity:
- Broken structures, such as a pipe top with no body, or invalid tiles, are
  defects, not design choices. They cannot go to playtest as is.

Derivative content:
- High similarity to known levels means the candidate may be derivative. If the
  brief wanted style consistency it can still be useful as a draft, but flag that it
  should not ship as final without variation.

Advisory stance:
- You never edit the level. When a change is warranted, prescribe ordered, reasoned
  edits that respect the hard constraints, and let the designer apply them.
- Readiness means the segment is sound enough for a human to playtest, not that it
  is proven fun. Difficulty here is a heuristic estimate, not player validated.
  Frame everything as informing the designer's decision, never replacing it.
"""


def get_design_guidance() -> str:
    """Return the curated design guidance block injected into the agent instructions."""
    return DESIGN_GUIDANCE
