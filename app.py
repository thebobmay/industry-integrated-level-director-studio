"""Gradio app for AI Level Director Studio.

A thin interaction layer over the tested UI callbacks. Five tabs (Design Session,
Candidate Board, Candidate Detail, Playtester View, Reports) plus a Live/Mock
engine toggle. The Candidate Board and Playtester View are card grids rendered
dynamically with ``gr.render``; cards show the level as an ASCII tile grid (image
previews are a deferred polish feature). The app never touches prior project
internals or persistence directly; it only calls callbacks, which call the
LevelDirectorService.

Run with: ``python app.py`` (from the repository root).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import gradio as gr  # noqa: E402

from ai_level_director.config import load_environment  # noqa: E402
from ai_level_director.rendering.ascii_renderer import render_level_ascii  # noqa: E402
from ai_level_director.ui import callbacks as cb  # noqa: E402
from ai_level_director.ui.view_models import candidate_detail_view, find_candidate  # noqa: E402

_OUTPUT_ROOT = "outputs"
_DIFFICULTY = ["unspecified", "easy", "medium", "hard"]
_NOVELTY = ["unspecified", "style consistent", "balanced", "original"]
_TERMINAL = {"complete", "archived", "structural_rejected"}
_SENDABLE = {"ready_for_playtest", "derivative_review_needed"}
_CARDS_PER_ROW = 3

# One service per engine, built lazily so the real adapters (which load models and
# import the vendored agent) are only constructed when Live is first used.
_services: dict[str, object] = {}


def _get_service(engine: str):
    """Return the cached LevelDirectorService for the chosen engine."""
    if engine not in _services:
        from ai_level_director.workflow.service import LevelDirectorService

        if engine == "Mock":
            from ai_level_director.adapters.mocks import (
                MockFeedbackAdapter,
                MockGeneratorAdapter,
                MockTriageAdapter,
            )

            _services[engine] = LevelDirectorService(
                _OUTPUT_ROOT,
                triage_adapter=MockTriageAdapter(),
                feedback_adapter=MockFeedbackAdapter(),
                generator_adapter=MockGeneratorAdapter(),
            )
        else:  # Live
            from ai_level_director.adapters.project3_feedback import Project3FeedbackAdapter
            from ai_level_director.adapters.project5_generator import Project5GeneratorAdapter
            from ai_level_director.adapters.project6_triage import Project6TriageAdapter

            _services[engine] = LevelDirectorService(
                _OUTPUT_ROOT,
                triage_adapter=Project6TriageAdapter(),
                feedback_adapter=Project3FeedbackAdapter(),
                generator_adapter=Project5GeneratorAdapter(),
            )
    return _services[engine]


# Action helpers. State changing actions return the new refresh tick and a status;
# every dynamic tab re-renders when the tick changes.

def _act(engine, session_id, tick, cid, op):
    """Run a candidate action callback and bump the refresh tick."""
    *_, status = op(_get_service(engine), session_id, cid)
    return tick + 1, status


def w_start(engine, brief, difficulty, novelty, tick):
    sid, _b, _i, _q, status = cb.start_session(_get_service(engine), brief, difficulty, novelty)
    return sid, tick + 1, status


def w_generate(engine, sid, n, temperature, seed, tick):
    *_, status = cb.generate_candidates(_get_service(engine), sid, n, temperature, seed)
    return tick + 1, status


def w_upload(engine, sid, text, title, tick):
    *_, status = cb.upload_candidate(_get_service(engine), sid, text, title)
    return tick + 1, status


def w_sample(engine, sid, sample, tick):
    *_, status = cb.load_sample(_get_service(engine), sid, sample)
    return tick + 1, status


def w_feedback(engine, sid, cid, text, tick):
    *_, status = cb.submit_feedback(_get_service(engine), sid, cid, text)
    return tick + 1, status


def w_revise(engine, sid, parent, text, notes, tick):
    *_, status = cb.create_revised_candidate(_get_service(engine), sid, parent, text, notes)
    return tick + 1, status


def w_report(engine, sid):
    report_text, report_path, session_json, timeline, status = cb.build_report(_get_service(engine), sid)
    return report_text, timeline, report_path, session_json, status


def _card_info(candidate) -> str:
    """Short status text shown on a candidate card."""
    lines = []
    triage = candidate.triage_result
    if triage:
        lines.append(f"Triage: **{triage.action}** ({triage.readiness})")
        if triage.warnings:
            lines.append(f"Warning: {triage.warnings[0]}")
    if candidate.feedback_records:
        lines.append(f"Feedback: {candidate.feedback_records[-1].feedback_result.sentiment}")
    return "\n\n".join(lines) if lines else "_Not triaged yet._"


def build_app() -> gr.Blocks:
    """Construct the Gradio Blocks app (does not launch it)."""
    with gr.Blocks(title="AI Level Director Studio") as demo:
        gr.Markdown("# AI Level Director Studio")
        gr.Markdown("A designer governed workflow for 2D platformer level iteration.")

        with gr.Row():
            engine = gr.Radio(
                ["Live", "Mock"], value="Live", label="Engine",
                info="Live uses the real Projects 5, 6, 3 (needs an API key). Mock is instant and free.",
            )
            status = gr.Markdown("Start or load a session to begin.")

        session_id = gr.State(None)
        refresh_tick = gr.State(0)
        selected_detail_id = gr.State(None)

        with gr.Tab("Design Session"):
            brief = gr.Textbox(label="Design brief", lines=3,
                               placeholder="An easy beginner friendly opening segment...")
            with gr.Row():
                difficulty = gr.Dropdown(_DIFFICULTY, value="unspecified", label="Target difficulty")
                novelty = gr.Dropdown(_NOVELTY, value="unspecified", label="Novelty preference")
            start_btn = gr.Button("Start New Session", variant="primary")

            gr.Markdown("### Add candidates")
            with gr.Row():
                with gr.Column():
                    gr.Markdown("**Generate (Project 5)**")
                    gen_n = gr.Slider(1, 5, value=1, step=1, label="Count")
                    gen_temp = gr.Slider(0.7, 1.5, value=1.2, step=0.1, label="Temperature")
                    gen_seed = gr.Number(label="Seed (optional)", value=None)
                    gen_btn = gr.Button("Generate Candidates")
                with gr.Column():
                    gr.Markdown("**Upload**")
                    up_text = gr.Textbox(label="Paste tile grid", lines=6)
                    up_title = gr.Textbox(label="Title (optional)")
                    up_btn = gr.Button("Add Uploaded Candidate")
                with gr.Column():
                    gr.Markdown("**Sample**")
                    sample_dd = gr.Dropdown(cb.list_sample_levels(), label="Bundled sample")
                    sample_btn = gr.Button("Load Sample Candidate")

            start_btn.click(w_start, [engine, brief, difficulty, novelty, refresh_tick],
                            [session_id, refresh_tick, status])
            gen_btn.click(w_generate, [engine, session_id, gen_n, gen_temp, gen_seed, refresh_tick],
                          [refresh_tick, status])
            up_btn.click(w_upload, [engine, session_id, up_text, up_title, refresh_tick],
                         [refresh_tick, status])
            sample_btn.click(w_sample, [engine, session_id, sample_dd, refresh_tick],
                             [refresh_tick, status])

        with gr.Tab("Candidate Board"):
            @gr.render(inputs=[session_id, refresh_tick, engine])
            def render_board(sid, tick, eng):
                if not sid:
                    gr.Markdown("_Start a session and add candidates to see the board._")
                    return
                candidates = _get_service(eng).load_session(sid).candidates
                if not candidates:
                    gr.Markdown("_No candidates yet. Generate, upload, or load a sample._")
                    return
                for start in range(0, len(candidates), _CARDS_PER_ROW):
                    with gr.Row():
                        for c in candidates[start:start + _CARDS_PER_ROW]:
                            with gr.Column():
                                with gr.Group():
                                    gr.Markdown(
                                        f"#### {c.candidate_id} · {c.source}\n"
                                        f"**{c.title}**\n\nState: `{c.workflow_state}`"
                                    )
                                    gr.Code(render_level_ascii(c.level_text))
                                    gr.Markdown(_card_info(c))
                                    with gr.Row():
                                        state = c.workflow_state
                                        if state == "draft":
                                            b = gr.Button("Triage", size="sm")
                                            b.click(
                                                lambda e, s, t, cid=c.candidate_id: _act(e, s, t, cid, cb.run_triage),
                                                [engine, session_id, refresh_tick], [refresh_tick, status],
                                            )
                                        if state in _SENDABLE:
                                            b = gr.Button("Send to Playtest", size="sm")
                                            b.click(
                                                lambda e, s, t, cid=c.candidate_id: _act(e, s, t, cid, cb.send_to_playtest),
                                                [engine, session_id, refresh_tick], [refresh_tick, status],
                                            )
                                        if state not in _TERMINAL:
                                            bc = gr.Button("Complete", size="sm")
                                            bc.click(
                                                lambda e, s, t, cid=c.candidate_id: _act(e, s, t, cid, cb.mark_complete),
                                                [engine, session_id, refresh_tick], [refresh_tick, status],
                                            )
                                            ba = gr.Button("Archive", size="sm")
                                            ba.click(
                                                lambda e, s, t, cid=c.candidate_id: _act(e, s, t, cid, cb.archive_candidate),
                                                [engine, session_id, refresh_tick], [refresh_tick, status],
                                            )

        with gr.Tab("Candidate Detail"):
            # The candidate selector and the detail body are rendered separately on
            # purpose. The selector does not depend on selected_detail_id, so choosing
            # a candidate updates only the body and never tears down the dropdown that
            # fired the change. The body depends on selected_detail_id and re-renders
            # on selection. Combining them caused the dropdown to lock after actions
            # that bumped the refresh tick (for example submitting playtest feedback).
            @gr.render(inputs=[session_id, refresh_tick, engine])
            def render_detail_selector(sid, tick, eng):
                if not sid:
                    return
                ids = [c.candidate_id for c in _get_service(eng).load_session(sid).candidates]
                dd = gr.Dropdown(ids, label="Candidate", value=None)
                dd.change(lambda v: v, dd, selected_detail_id)

            @gr.render(inputs=[session_id, refresh_tick, selected_detail_id, engine])
            def render_detail(sid, tick, cid, eng):
                if not sid:
                    gr.Markdown("_No session yet._")
                    return
                session = _get_service(eng).load_session(sid)
                detail = candidate_detail_view(session, cid)
                gr.Markdown(detail["metadata_markdown"])
                gr.Code(detail["raw_level_text"], label="Level tiles")
                gr.Markdown(detail["triage_markdown"])
                gr.Markdown("**Feedback**\n\n" + detail["feedback_markdown"])
                gr.Markdown("**History**\n\n" + detail["history_markdown"])

                candidate = find_candidate(session, cid) if cid else None
                if candidate:
                    arts = cb.triage_artifacts(_get_service(eng), sid, cid)
                    if arts["report_path"] or arts["transcript_path"]:
                        gr.Markdown("### Triage deliberation and report")
                        if arts["report_path"]:
                            with gr.Accordion("Triage report", open=False):
                                gr.Markdown(arts["report_text"])
                                gr.File(value=arts["report_path"], label="Download report (.md)", interactive=False)
                        if arts["transcript_path"]:
                            with gr.Accordion("Agent deliberation transcript", open=False):
                                gr.Code(arts["transcript_text"], label="Transcript")
                                gr.File(value=arts["transcript_path"], label="Download transcript (.md)", interactive=False)
                    if candidate.level_path:
                        gr.File(value=candidate.level_path, label="Download level text", interactive=False)
                    gr.Markdown("### Create a revised candidate")
                    rtext = gr.Textbox(label="Revised tile grid", lines=6)
                    rnotes = gr.Textbox(label="Revision notes (optional)")
                    rbtn = gr.Button("Create Revised Candidate")
                    rbtn.click(
                        lambda e, s, text, notes, t, parent=cid: w_revise(e, s, parent, text, notes, t),
                        [engine, session_id, rtext, rnotes, refresh_tick], [refresh_tick, status],
                    )

        with gr.Tab("Playtester View"):
            @gr.render(inputs=[session_id, refresh_tick, engine])
            def render_playtest(sid, tick, eng):
                if not sid:
                    gr.Markdown("_No session yet._")
                    return
                queue = [
                    c for c in _get_service(eng).load_session(sid).candidates
                    if c.workflow_state == "sent_to_playtest"
                ]
                if not queue:
                    gr.Markdown("_No candidates awaiting playtest. Send a ready candidate from the board._")
                    return
                for start in range(0, len(queue), _CARDS_PER_ROW):
                    with gr.Row():
                        for c in queue[start:start + _CARDS_PER_ROW]:
                            with gr.Column():
                                with gr.Group():
                                    gr.Markdown(f"#### {c.candidate_id}\n**{c.title}**")
                                    gr.Code(render_level_ascii(c.level_text))
                                    triage = c.triage_result
                                    if triage and triage.playtest_questions:
                                        gr.Markdown(
                                            "**Playtest focus**\n"
                                            + "\n".join(f"- {q}" for q in triage.playtest_questions)
                                        )
                                    fb = gr.Textbox(label="Feedback", lines=3)
                                    sb = gr.Button("Submit Feedback", size="sm", variant="primary")
                                    sb.click(
                                        lambda e, s, text, t, cid=c.candidate_id: w_feedback(e, s, cid, text, t),
                                        [engine, session_id, fb, refresh_tick], [refresh_tick, status],
                                    )

        with gr.Tab("Reports"):
            report_btn = gr.Button("Generate Session Report", variant="primary")
            report_md = gr.Markdown()
            timeline_md = gr.Markdown()
            report_file = gr.File(label="Download report (.md)", interactive=False)
            session_file = gr.File(label="Download session (.json)", interactive=False)
            report_btn.click(w_report, [engine, session_id],
                             [report_md, timeline_md, report_file, session_file, status])

    return demo


def main() -> None:
    """Load the local environment and launch the app."""
    load_environment()
    build_app().launch()


if __name__ == "__main__":
    main()
