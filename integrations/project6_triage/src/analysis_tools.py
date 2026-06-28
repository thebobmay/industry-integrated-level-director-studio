"""Deterministic analysis tools (facts only).

Each function reports a fact about a candidate level and returns a typed result.
They never decide and never edit the level. The tile vocabulary is the VGLC Super
Mario Bros set used throughout the project. Difficulty is structural and heuristic,
not player validated.
"""

from __future__ import annotations

from src.level_io import parse_level
from src.models import (
    DifficultyResult,
    NoveltyResult,
    PacingResult,
    SafeZoneResult,
    SpikeResult,
    ValidationResult,
)

# Tile vocabulary (VGLC Super Mario Bros).
EMPTY = "-"
GROUND = "X"
BREAKABLE = "S"
QUESTION_FULL = "?"
QUESTION_USED = "Q"
ENEMY = "E"
COIN = "o"
PIPE_TOP_LEFT = "<"
PIPE_TOP_RIGHT = ">"
PIPE_BODY_LEFT = "["
PIPE_BODY_RIGHT = "]"
CANNON_TOP = "B"
CANNON_BODY = "b"

VALID_TILES = {
    EMPTY, GROUND, BREAKABLE, QUESTION_FULL, QUESTION_USED, ENEMY, COIN,
    PIPE_TOP_LEFT, PIPE_TOP_RIGHT, PIPE_BODY_LEFT, PIPE_BODY_RIGHT,
    CANNON_TOP, CANNON_BODY,
}
SOLID_TILES = {GROUND, BREAKABLE}
COLLECTIBLE_TILES = {COIN, QUESTION_FULL}
DANGER_TILES = {ENEMY, CANNON_TOP}  # enemies and cannons; gaps are handled separately

EXPECTED_HEIGHT = 14
EXPECTED_WIDTH = 32

# Difficulty scoring (structural, heuristic). Calibrated against the fixtures.
W_ENEMY = 100.0
W_HAZARD = 100.0
W_GAP = 5.0
EASY_MAX_SCORE = 8.0
HARD_MIN_SCORE = 22.0

# Novelty thresholds (nearest neighbour similarity).
LOW_NOVELTY_SIMILARITY = 0.95
HIGH_NOVELTY_SIMILARITY = 0.85

# Design aware thresholds.
SAFE_ZONE_MIN_WIDTH = 4
SPIKE_WINDOW = 5
SPIKE_MIN_GAP = 2
SECTION_INTENSITY_THRESHOLD = 2


def _bottom_row(grid: list[list[str]]) -> list[str]:
    """Return the bottom row of the grid, or an empty list."""
    return grid[-1] if grid else []


def _gap_columns(grid: list[list[str]]) -> set[int]:
    """Return the set of bottom row columns that are floor gaps (air)."""
    return {c for c, tile in enumerate(_bottom_row(grid)) if tile == EMPTY}


def _danger_columns(grid: list[list[str]]) -> set[int]:
    """Return columns that contain an enemy or a cannon top in any row."""
    return {c for row in grid for c, tile in enumerate(row) if tile in DANGER_TILES}


def _longest_gap(grid: list[list[str]]) -> int:
    """Return the longest run of floor gap columns in the bottom row."""
    longest = run = 0
    for tile in _bottom_row(grid):
        if tile == EMPTY:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    return longest


def validate_level(level_text: str) -> ValidationResult:
    """Validate structure, vocabulary, dimensions, and pipe and cannon integrity."""
    grid = parse_level(level_text)
    fatal: list[str] = []
    warnings: list[str] = []

    if not grid or all(not row for row in grid):
        return ValidationResult(is_valid=False, fatal_errors=["level is empty"])

    widths = {len(row) for row in grid}
    if len(widths) != 1:
        fatal.append(f"inconsistent row widths: {sorted(widths)}")
    height, width = len(grid), len(grid[0])
    if height != EXPECTED_HEIGHT or width != EXPECTED_WIDTH:
        fatal.append(f"expected {EXPECTED_HEIGHT} by {EXPECTED_WIDTH}, got {height} by {width}")

    bad = sorted({tile for row in grid for tile in row if tile not in VALID_TILES})
    if bad:
        fatal.append(f"invalid tile characters: {bad}")

    fatal.extend(_check_pipes(grid))
    warnings.extend(_check_cannons(grid))

    fatal = list(dict.fromkeys(fatal))
    return ValidationResult(is_valid=not fatal, warnings=warnings, fatal_errors=fatal)


def _below(grid: list[list[str]], r: int, c: int) -> str | None:
    """Return the tile directly below (r, c), or None if off the grid."""
    if r + 1 >= len(grid) or c >= len(grid[r + 1]):
        return None
    return grid[r + 1][c]


def _check_pipes(grid: list[list[str]]) -> list[str]:
    """Return fatal errors for malformed pipes (unmatched halves or missing support)."""
    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, tile in enumerate(row):
            right = row[c + 1] if c + 1 < len(row) else None
            left = row[c - 1] if c - 1 >= 0 else None
            below = _below(grid, r, c)
            if tile == PIPE_TOP_LEFT:
                if right != PIPE_TOP_RIGHT:
                    errors.append("pipe top left without a matching pipe top right")
                if below not in (PIPE_BODY_LEFT, GROUND):
                    errors.append("pipe top without a body or ground support")
            elif tile == PIPE_TOP_RIGHT:
                if left != PIPE_TOP_LEFT:
                    errors.append("pipe top right without a matching pipe top left")
                if below not in (PIPE_BODY_RIGHT, GROUND):
                    errors.append("pipe top without a body or ground support")
            elif tile == PIPE_BODY_LEFT:
                if right != PIPE_BODY_RIGHT:
                    errors.append("pipe body left without a matching pipe body right")
                if below not in (PIPE_BODY_LEFT, GROUND):
                    errors.append("pipe body without support beneath it")
            elif tile == PIPE_BODY_RIGHT:
                if left != PIPE_BODY_LEFT:
                    errors.append("pipe body right without a matching pipe body left")
                if below not in (PIPE_BODY_RIGHT, GROUND):
                    errors.append("pipe body without support beneath it")
    return errors


def _check_cannons(grid: list[list[str]]) -> list[str]:
    """Return warnings for floating cannons (a cannon tile with air beneath it)."""
    warnings: list[str] = []
    for r, row in enumerate(grid):
        for c, tile in enumerate(row):
            if tile in (CANNON_TOP, CANNON_BODY):
                below = _below(grid, r, c)
                if below not in (CANNON_TOP, CANNON_BODY, GROUND):
                    warnings.append("cannon without support beneath it")
    return list(dict.fromkeys(warnings))


def estimate_difficulty(level_text: str) -> DifficultyResult:
    """Estimate structural difficulty from engineered features (not player validated)."""
    grid = parse_level(level_text)
    total = sum(len(row) for row in grid) or 1
    counts = {tile: 0 for tile in VALID_TILES}
    for row in grid:
        for tile in row:
            if tile in counts:
                counts[tile] += 1

    enemy_density = counts[ENEMY] / total
    hazard_density = counts[CANNON_TOP] / total
    longest_gap = _longest_gap(grid)
    solid_ratio = sum(counts[t] for t in SOLID_TILES) / total
    collectible_density = sum(counts[t] for t in COLLECTIBLE_TILES) / total

    score = enemy_density * W_ENEMY + hazard_density * W_HAZARD + longest_gap * W_GAP
    if score < EASY_MAX_SCORE:
        label = "easy"
    elif score < HARD_MIN_SCORE:
        label = "medium"
    else:
        label = "hard"

    return DifficultyResult(
        difficulty_label=label,
        difficulty_score=round(score, 3),
        enemy_density=round(enemy_density, 4),
        hazard_density=round(hazard_density, 4),
        longest_gap=longest_gap,
        solid_ratio=round(solid_ratio, 4),
        collectible_density=round(collectible_density, 4),
    )


def tile_similarity(level_a: str, level_b: str) -> float:
    """Return the content similarity of two levels (0 to 1).

    Positions where both levels are empty air are skipped, so a shared blank
    background does not inflate the score. Two levels are compared on the cells
    where at least one places a tile.
    """
    ga, gb = parse_level(level_a), parse_level(level_b)
    rows = max(len(ga), len(gb))
    matches = total = 0
    for r in range(rows):
        ra = ga[r] if r < len(ga) else []
        rb = gb[r] if r < len(gb) else []
        for c in range(max(len(ra), len(rb))):
            ca = ra[c] if c < len(ra) else EMPTY
            cb = rb[c] if c < len(rb) else EMPTY
            if ca == EMPTY and cb == EMPTY:
                continue
            total += 1
            if ca == cb:
                matches += 1
    return matches / total if total else 1.0


def measure_novelty(level_text: str, reference_levels: list[str]) -> NoveltyResult:
    """Measure novelty as one minus the nearest neighbour similarity to the references."""
    similarity = max((tile_similarity(level_text, ref) for ref in reference_levels), default=0.0)
    if similarity >= LOW_NOVELTY_SIMILARITY:
        label = "low"
        warning = (
            f"high similarity ({similarity:.3f}) to a known level; the candidate may be derivative"
        )
    elif similarity >= HIGH_NOVELTY_SIMILARITY:
        label = "medium"
        warning = None
    else:
        label = "high"
        warning = None
    return NoveltyResult(
        nearest_neighbor_similarity=round(similarity, 4),
        novelty_label=label,
        warning=warning,
    )


def _section_intensity(grid: list[list[str]], start: int, end: int) -> int:
    """Sum enemy, cannon, and gap contributions within a column range."""
    gaps = _gap_columns(grid)
    intensity = sum(1 for c in range(start, end) if c in gaps)
    for row in grid:
        for c in range(start, min(end, len(row))):
            if row[c] in DANGER_TILES:
                intensity += 1
    return intensity


def analyze_pacing(level_text: str) -> PacingResult:
    """Analyze challenge pacing across the opening, middle, and final thirds."""
    grid = parse_level(level_text)
    width = len(grid[0]) if grid else 0
    b1, b2 = width // 3, 2 * width // 3
    opening = _section_intensity(grid, 0, b1)
    middle = _section_intensity(grid, b1, b2)
    final = _section_intensity(grid, b2, width)

    total = opening + middle + final
    if total == 0:
        flag = "flat"
    elif opening > middle and opening > final and opening >= SECTION_INTENSITY_THRESHOLD:
        flag = "front_loaded"
    elif final > opening and final >= middle:
        flag = "back_loaded"
    else:
        flag = "balanced"

    detail = f"intensity opening {opening}, middle {middle}, final {final}"
    return PacingResult(
        flag=flag,
        opening_intensity=opening,
        middle_intensity=middle,
        final_intensity=final,
        detail=detail,
    )


def detect_safe_zone(level_text: str) -> SafeZoneResult:
    """Detect whether the segment opens with a safe zone before the first challenge."""
    grid = parse_level(level_text)
    width = len(grid[0]) if grid else 0
    gaps = _gap_columns(grid)
    danger = _danger_columns(grid)

    first_challenge = width
    for c in range(width):
        if c in gaps or c in danger:
            first_challenge = c
            break

    has_safe_zone = first_challenge >= SAFE_ZONE_MIN_WIDTH
    if first_challenge >= width:
        detail = "no challenge found in the segment"
    else:
        detail = f"first challenge at column {first_challenge}"
    return SafeZoneResult(
        has_opening_safe_zone=has_safe_zone,
        first_challenge_column=first_challenge,
        detail=detail,
    )


def detect_difficulty_spike(level_text: str) -> SpikeResult:
    """Detect a localized window that combines a gap with an enemy or cannon."""
    grid = parse_level(level_text)
    width = len(grid[0]) if grid else 0
    gaps = _gap_columns(grid)
    danger = _danger_columns(grid)

    for start in range(0, max(1, width - SPIKE_WINDOW + 1)):
        window = range(start, start + SPIKE_WINDOW)
        gap_count = sum(1 for c in window if c in gaps)
        has_danger = any(c in danger for c in window)
        if gap_count >= SPIKE_MIN_GAP and has_danger:
            return SpikeResult(
                has_spike=True,
                location_column=start,
                detail=f"gap of {gap_count} combined with an enemy or cannon near column {start}",
            )
    return SpikeResult(has_spike=False, location_column=None, detail="no local difficulty spike found")
