# AI Level Director Studio — Research Foundation

**Working title:** AI Level Director Studio: A Designer-Governed Workflow for 2D Platformer Level Iteration  
**Purpose:** This document consolidates the research foundation for the final integrated capstone before implementation. It is intended to guide system design, report framing, UI decisions, evaluation planning, and responsible-use language.

---

## 1. Working Thesis

AI Level Director Studio should be framed as a **designer-governed compound AI workflow** rather than an autonomous level generator.

The system integrates prior capstone components into a candidate-level design iteration loop:

```text
Designer brief
    ↓
Candidate source
    ├── Generate candidate(s) using Project 5
    └── Upload/provide designer-authored candidate(s)
    ↓
Candidate-level workflow state
    ↓
Project 6 triage agent
    ↓
Designer decision / playtest routing
    ↓
Playtester feedback
    ↓
Project 3 feedback classifier
    ↓
Candidate becomes complete, revision_needed, or human_review_needed
```

The core claim is:

> AI Level Director Studio addresses the gap between **AI can produce candidate content** and **a designer can safely use that content**. It treats generation, metrics, feedback classification, and agentic recommendations as decision-support signals, not final creative authority.

---

## 2. Industry Need: Faster Iteration Under Production Pressure

### Key Research

The GDC 2025 State of the Game Industry survey reported continued layoff pressure and increased generative AI adoption across game development. GDC summarized that more studios are adopting generative AI while developer sentiment remains divided, and that roughly one in ten developers surveyed had lost a job in the prior year. The survey also highlights concerns around AI's effect on quality, labor, IP, and trust.

### Relevance to Project 7

The industry problem is not simply that studios need an AI level generator. The stronger problem is:

> Game teams, especially small and resource-constrained teams, need faster ways to evaluate, compare, and iterate on candidate content before investing in deeper implementation or playtesting. At the same time, raw AI-generated content cannot be trusted as final creative output.

### Design Implications

- Position the system as **design iteration support**, not replacement design labor.
- Use "designer-governed" or "advisory" language.
- Make warnings, limitations, candidate states, and feedback visible in the UI.
- Use AI to accelerate screening and iteration, not to silently ship generated content.

---

## 3. Compound AI Systems: Integrating Specialized Components

### Key Research

Berkeley's "Shift from Models to Compound AI Systems" argues that many effective AI applications are not single monolithic models, but systems composed of multiple interacting components such as model calls, retrievers, tools, external APIs, and orchestrators.

Recent work on compound AI systems similarly frames complex AI applications as coordinated systems that integrate models, agents, tools, memory, and workflows to handle tasks beyond what one model can reliably solve alone.

### Relevance to Project 7

This is the strongest technical framing for the integrated capstone. Project 7 is not simply "three prior projects chained together." It is a compound AI workflow:

| Component | Role |
|---|---|
| Project 5 | Candidate level generation |
| Project 6 | Candidate triage and design recommendation |
| Project 3 | Playtester/player feedback signal |
| Project 7 | Orchestration, candidate state, UI, session persistence, reports |

### Design Implications

- Build an **orchestration layer**, not a fourth major model.
- Wrap each prior project in adapters.
- Keep component boundaries clean.
- Use a candidate-level state machine.
- Evaluate both individual adapters and end-to-end workflow scenarios.
- Save sessions, events, candidates, and reports for transparency and reproducibility.

---

## 4. System Integration and ML Engineering Risks

### Key Research

"Hidden Technical Debt in Machine Learning Systems" warns that ML systems are prone to special maintenance risks, including entanglement, boundary erosion, hidden feedback loops, undeclared consumers, and configuration complexity.

DSPy frames LM applications as modular pipelines or computational graphs rather than ad hoc prompt strings. Even if this project does not use DSPy directly, the design lesson is relevant: complex AI systems should be structured as explicit modules that can be evaluated and improved.

### Relevance to Project 7

The final project could easily become fragile if the UI directly calls Torch model internals, Pydantic AI internals, pickled sklearn objects, and report code all in one place. The risk is not just messy code; it would make the final project hard to explain, test, and reproduce.

### Design Implications

Use a clean backend pattern stack:

```text
Gradio UI
  ↓
View models / UI callbacks
  ↓
LevelDirectorService facade
  ↓
Candidate-level workflow controller
  ↓
Adapters
    ├── Project5GeneratorAdapter
    ├── Project6TriageAdapter
    └── Project3FeedbackAdapter
  ↓
SessionStore / EventLog / ReportBuilder / Renderer
```

Key implementation choices:

- **Adapter pattern:** isolate prior project internals.
- **Facade/service layer:** give the UI one simple backend API.
- **Candidate state machine:** track each candidate independently.
- **JSON session store:** persist state without a database.
- **JSONL event log:** preserve workflow history.
- **Report builder:** produce consistent human-readable artifacts.
- **View models:** keep Gradio callbacks clean.

---

## 5. Procedural Content Generation and PCGML

### Key Research

Summerville et al.'s PCGML survey defines Procedural Content Generation via Machine Learning as generating game content using ML models trained on existing content. Importantly, the survey frames PCGML as useful not only for autonomous generation, but also for co-creativity, mixed-initiative design, repair, critique, and content analysis.

Recent generative-AI-for-PCG research highlights a limitation directly relevant to this project: high-performing generative AI often requires large training data, but game content is customized and domain-specific, so suitable training data can be scarce.

### Relevance to Project 7

Project 5 demonstrated exactly this problem. The conditional Transformer produced structurally valid, difficulty-controlled level chunks, but novelty and nearest-neighbor analysis showed substantial similarity to training levels. That means the generator is useful as a **candidate source**, not as a final-content creator.

### Design Implications

- Treat generated levels as **candidate drafts**.
- Include derivative/novelty risk in candidate state and reports.
- Avoid claiming that the generator creates production-ready levels.
- Allow designer-uploaded candidates as an equal candidate source.
- Use Project 6 triage to review generated or uploaded candidates before playtesting.
- Use Project 7 to manage candidate lifecycle, not to pretend generation solved level design.

---

## 6. Mixed-Initiative and Co-Creative Level Design

### Key Research

Mixed-initiative content creation research frames human and AI systems as collaborative partners. The key design goal is not full automation, but supporting the human designer's creative process.

Tanagra is a direct precedent for this project: a mixed-initiative tool for 2D platformer level design where a human designer and computer work together to produce a level. The designer can specify constraints while the system assists with level construction.

Co-creative level design via machine learning research asks whether ML-generated content actually benefits human designers, rather than only whether it resembles training content.

Mixed-initiative level design studies such as RL Brush and other procedural level design user studies provide evidence that AI suggestions can support designer exploration and inspiration when properly framed as assistance.

### Relevance to Project 7

AI Level Director Studio is best framed as a **designer-governed design workspace**. The system manages candidate states, triage, playtest routing, feedback, and iteration, but the human designer decides what to accept, revise, playtest, or reject.

### Design Implications

- Build the UI around candidate cards and human actions.
- Include explicit "send to playtest" and "mark complete" actions.
- Let the designer choose between generated and uploaded candidates.
- Avoid automatic level editing in the MVP.
- Preserve revision history rather than overwriting candidate state.
- Use the playtester tab as a human checkpoint, even if the actual game is not playable inside the app.

---

## 7. Platformer Level Design Knowledge

### Key Research

Platformer level design research emphasizes that level analysis is genre-specific. Smith et al.'s work on 2D platformer level analysis and rhythm-based platformer generation supports thinking about pacing, rhythm, structure, and player action timing rather than relying on a single global difficulty score.

Khalifa, Silva, and Togelius identify common 2D level design patterns such as:

- Guidance
- Foreshadowing
- Safe Zone
- Layering
- Branching
- Pace Breaking

These patterns provide useful vocabulary for warnings and design feedback.

### Relevance to Project 7

P6 already introduced design-aware signals such as pacing, safe zones, and local difficulty spikes. P7 should preserve this domain language in candidate cards, detail views, reports, and playtest questions.

### Design Implications

The system should not only say:

```text
difficulty = medium
novelty = low
```

It should also say:

```text
The opening lacks a safe zone.
The candidate has an early local difficulty spike.
This is style-consistent but potentially derivative.
The level may be ready for playtest, but testers should focus on whether the first jump feels fair.
```

This helps the output feel like level-design assistance rather than raw metric reporting.

---

## 8. Metrics, Playtesting, and Feedback

### Key Research

Research on platformer metrics, including Mario-level evaluation work, uses computational measures such as leniency, density, and linearity. These metrics can be useful for comparing levels, but they do not fully replace human evaluation or user studies.

AI-assisted 2D platformer design research also emphasizes estimating jump difficulty, completion probability, and player frustration risk, reinforcing that playability and player experience are more than structural validity.

### Relevance to Project 7

P6 can decide whether a candidate is **ready for playtest**, but it cannot decide whether the level is fun or successful. P3 feedback classification should therefore occur after a candidate is sent to playtest.

### Design Implications

The correct loop is:

```text
P6 triage
  ↓
ready_for_playtest?
  ↓
designer sends candidate to playtester
  ↓
playtester enters feedback
  ↓
P3 classifies feedback
  ↓
positive → complete
negative → revision_needed
uncertain → human_review_needed
```

This avoids overclaiming that computed metrics or agent judgments can replace playtesting.

---

## 9. Agentic AI and Tool Use

### Key Research

ReAct demonstrates an agent pattern where language models interleave reasoning with actions and observations. This supports the idea that an agent should reason over external tool results rather than rely only on internal language-model knowledge.

Toolformer further supports the broader principle that language models can benefit from calling external tools for tasks requiring computation, factual lookup, or specialized capabilities.

### Relevance to Project 7

Project 6 already embodies this pattern: it calls deterministic analysis tools and uses an agentic triage process to produce recommendations. P7 should reuse P6 rather than building a new agent.

### Design Implications

- Do not add a new "synthesis agent" in P7.
- Let P6 remain the agentic decision layer.
- Let P7 manage orchestration, state, and UI.
- Keep Project 3 and Project 5 as tool/model components called by the workflow.
- Avoid asking an LLM to infer facts that can be computed or classified by existing tools.

---

## 10. Human-AI Interaction and Responsible AI

### Key Research

Amershi et al.'s Guidelines for Human-AI Interaction emphasize transparency, user control, understanding AI behavior, supporting recovery from errors, and managing uncertainty.

Model Cards support documenting intended use, limitations, evaluation conditions, and failure modes for trained models.

Human-in-the-loop design-pattern research reinforces that human checkpoints are useful when model outputs are uncertain, incomplete, or potentially harmful if treated as fully autonomous.

### Relevance to Project 7

The system should be explicitly **designer-governed**. This means the UI should expose state, warnings, feedback, and next actions rather than hiding the reasoning behind a single "good/bad" label.

### Design Implications

- Use state badges on candidate cards.
- Show triage rationale and warnings.
- Show feedback sentiment and confidence.
- Allow designer actions: send to playtest, mark complete, revise, archive.
- Preserve candidate history and event logs.
- Document limitations for each component.
- Avoid claiming objective quality or fun prediction.
- Add "request clarification" and "human review" states.

---

## 11. Gradio and Lightweight ML Interfaces

### Key Research

The Gradio paper frames ML accessibility as a major challenge: non-technical collaborators and endpoint users often struggle to interact with ML models. Gradio was designed to rapidly create visual interfaces for ML models, support input manipulation, enable interactive inference by domain experts, and facilitate collaboration.

The current Gradio documentation describes it as an open-source Python package for quickly building demo or web applications around ML models, APIs, or arbitrary Python functions.

### Relevance to Project 7

A UI is not merely polish for this project. The UI makes the designer-governed workflow visible:

- designer starts a session,
- generates or uploads candidates,
- sees candidate states,
- sends candidates to playtest,
- enters feedback as the playtester,
- watches candidate state change,
- downloads the session report.

### Design Implications

Use a light but functional Gradio interface with:

1. Design Session tab
2. Candidate Board tab
3. Candidate Detail tab
4. Playtester View tab
5. Reports / Session History tab

The UI should call backend service methods and should not contain project logic directly.

---

## 12. Rendering and Candidate Visualization

### Research / Design Context

The primary research justification is usability rather than AI novelty. Candidate visualization helps designers and playtesters understand level structure before reading metrics or recommendations.

### Relevance to Project 7

Rendered previews will make the UI more usable and easier to present. However, visual rendering should not become a core requirement that risks the timeline.

### Design Implications

MVP renderer:

```text
tile text → simple colored tile image
```

Optional polish:

```text
tile text → sprite-mapped preview using legally safe free/CC0 assets
```

Important caution:

- Do not use actual Nintendo/Mario sprites.
- Use generic free assets, CC0 assets, or simple custom placeholder sprites.
- Keep raw tile text available for reproducibility.

---

## 13. Prior Capstone Lessons Mapped to Research

| Project | Lesson | Research Connection | P7 Design Effect |
|---|---|---|---|
| P1 Programming/Data Workflow | Broad game datasets have scope and missingness limits | Responsible data practice, Model Cards | Keep P7 scoped to 2D platformer iteration |
| P2 Statistics | Significant results may have weak practical value | Metrics vs practical effect | Treat all metrics as signals, not truth |
| P3 Applied ML | Sentiment classifier is useful but domain-limited | Model Cards, feedback interpretation | Use as feedback signal only |
| P4 Deep Learning | Behavior modeling benefits from temporal context but is narrow | Behavior inference and scope limits | Future live telemetry extension |
| P5 Generative AI | Generator produces candidate drafts but novelty is weak | PCGML, limited data, mixed-initiative design | Generate candidates, then review and triage |
| P6 Agentic AI | Agent value is design judgment, not facts | ReAct, Toolformer, HAI guidelines | Use P6 as triage decision layer |

---

## 14. Research-to-System Design Matrix

| Research Area | System Design Decision |
|---|---|
| GDC industry survey | Frame the project around faster iteration under resource pressure |
| Compound AI systems | Integrate specialized components rather than building one monolithic model |
| Hidden ML technical debt | Use adapters, clean boundaries, state persistence, and logs |
| DSPy / modular LM pipelines | Treat the system as typed modules and workflow steps |
| PCGML | Treat generated levels as candidate drafts and support critique/content analysis |
| Generative AI for PCG | Explicitly handle limited-data and novelty limitations |
| Mixed-initiative design | Preserve designer choice and visible human actions |
| Tanagra / co-creative tools | Build a level-iteration assistant, not a generic AI game director |
| Platformer design patterns | Use pacing, safe-zone, guidance, and layering language |
| Mario/platformer metrics | Use metrics as screening signals, not final truth |
| ReAct / Toolformer | Keep the agent tool-grounded |
| Human-AI guidelines | Show uncertainty, support control, enable recovery |
| Model Cards | Document model limitations and intended use |
| Gradio | Use a lightweight UI for interaction, feedback, and demonstration |

---

## 15. Project 7 Design Principles

1. **Designer-governed, not autonomous.**  
   The designer remains responsible for final creative decisions.

2. **Compound AI system, not monolithic model.**  
   Project 7 coordinates Project 3, Project 5, and Project 6 through adapters.

3. **Candidate-level state, not only session-level state.**  
   Each candidate has its own lifecycle, history, triage result, and feedback result.

4. **Generated levels are drafts.**  
   Project 5 is a candidate source, not a production-level generator.

5. **Feedback is post-playtest.**  
   P3 classifies feedback after a candidate is sent to playtest.

6. **Metrics are signals.**  
   Validity, difficulty, novelty, pacing, and sentiment are evidence, not truth.

7. **P6 remains the agentic decision layer.**  
   P7 should not add a new synthesis agent unless absolutely necessary.

8. **The UI is part of the system design.**  
   Gradio makes designer and playtester checkpoints visible.

9. **Persistence supports transparency.**  
   Save JSON sessions, JSONL events, candidate files, and reports.

10. **Reproducibility matters.**  
    The system should run from a backend script/notebook even if the UI is used for presentation.

---

## 16. Candidate-Level Workflow

Recommended candidate states:

```text
draft
triaged
ready_for_playtest
sent_to_playtest
feedback_received
complete
revision_needed
clarification_needed
structural_rejected
derivative_review_needed
human_review_needed
archived
```

Recommended flow:

```text
Candidate created
    ↓
P6 triage
    ↓
Candidate state updated
    ↓
If ready_for_playtest:
    designer sends to playtest
    ↓
    playtester enters feedback
    ↓
    P3 classifies feedback
    ↓
    positive → complete
    negative → revision_needed
    uncertain → human_review_needed
```

If a candidate is revised, create a new candidate version with `parent_candidate_id` rather than overwriting the original.

---

## 17. Recommended Sources for Final Report

### Industry Need

- Game Developers Conference. (2025). *GDC 2025 State of the Game Industry: Devs Weigh in on Layoffs, AI, and More.*  
  https://gdconf.com/article/gdc-2025-state-of-the-game-industry-devs-weigh-in-on-layoffs-ai-and-more/

### Compound AI and System Architecture

- Zaharia, M., et al. (2024). *The Shift from Models to Compound AI Systems.* Berkeley AI Research Blog.  
  https://bair.berkeley.edu/blog/2024/02/18/compound-ai-systems/

- Sculley, D., et al. (2015). *Hidden Technical Debt in Machine Learning Systems.* NeurIPS.  
  https://papers.neurips.cc/paper/5656-hidden-technical-debt-in-machine-learning-systems.pdf

- Khattab, O., et al. (2023). *DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines.*  
  https://arxiv.org/abs/2310.03714

### Procedural Content Generation and Level Design

- Summerville, A., Snodgrass, S., Guzdial, M., Holmgård, C., Hoover, A. K., Isaksen, A., Nealen, A., & Togelius, J. (2018). *Procedural Content Generation via Machine Learning.* IEEE Transactions on Games.  
  https://arxiv.org/abs/1702.00539

- Mao, X., Yu, W., Yamada, K. D., & Zielewski, M. R. (2024). *Procedural Content Generation via Generative Artificial Intelligence.*  
  https://arxiv.org/abs/2407.09013

- Smith, G., Whitehead, J., & Mateas, M. (2010). *Tanagra: A Mixed-Initiative Level Design Tool.*  
  https://dl.acm.org/doi/10.1145/1822348.1822376

- Guzdial, M., Liao, N., & Riedl, M. (2018). *Co-Creative Level Design via Machine Learning.*  
  https://arxiv.org/abs/1809.09420

- Khalifa, A., Silva, F., & Togelius, J. (2019). *Level Design Patterns in 2D Games.*  
  https://www.gamedeveloper.com/design/level-design-patterns-in-2d-games

- Mariño, J. R. H., Reis, W. M. P., Lelis, L. H. S., & Gal, Y. K. (2015). *An Empirical Evaluation of Evaluation Metrics of Procedurally Generated Mario Levels.*  
  https://cdn.aaai.org/ojs/12785/12785-52-16302-1-2-20201228.pdf

- Aramini, A. U., Lanzi, P. L., & Loiacono, D. (2018). *An Integrated Framework for AI Assisted Level Design in 2D Platformers.*  
  https://arxiv.org/abs/1804.09153

### Agentic AI and Tool Use

- Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2022). *ReAct: Synergizing Reasoning and Acting in Language Models.*  
  https://arxiv.org/abs/2210.03629

- Schick, T., Dwivedi-Yu, J., Dessì, R., Raileanu, R., Lomeli, M., Zettlemoyer, L., Cancedda, N., & Scialom, T. (2023). *Toolformer: Language Models Can Teach Themselves to Use Tools.*  
  https://arxiv.org/abs/2302.04761

### Human-AI Interaction and Responsible AI

- Amershi, S., Weld, D., Vorvoreanu, M., Fourney, A., Nushi, B., Collisson, P., Suh, J., Iqbal, S., Bennett, P. N., Inkpen, K., Teevan, J., Kikin-Gil, R., & Horvitz, E. (2019). *Guidelines for Human-AI Interaction.* CHI.  
  https://dl.acm.org/doi/fullHtml/10.1145/3290605.3300233

- Mitchell, M., Wu, S., Zaldivar, A., Barnes, P., Vasserman, L., Hutchinson, B., Spitzer, E., Raji, I. D., & Gebru, T. (2019). *Model Cards for Model Reporting.*  
  https://arxiv.org/abs/1810.03993

### UI / Gradio

- Abid, A., Abdalla, A., Abid, A., Khan, D., Alfozan, A., & Zou, J. (2019). *Gradio: Hassle-Free Sharing and Testing of ML Models in the Wild.*  
  https://arxiv.org/abs/1906.02569

- Gradio. (n.d.). *Build Machine Learning Apps in Python.*  
  https://gradio.app/

---

## 18. Draft Report Framing Paragraph

AI Level Director Studio is designed as a compound AI workflow for 2D platformer level iteration. Rather than relying on a single model to generate finished content, the system coordinates multiple specialized components: a generative model for candidate creation, an agentic triage workflow for design-readiness assessment, and a supervised feedback classifier for post-playtest reception signals. This design reflects prior research on compound AI systems, mixed-initiative content creation, and PCGML, while also responding to the practical limitation observed in the generative capstone: small-corpus level generation can produce structurally valid and difficulty-controlled candidates while still exhibiting substantial derivative risk. The integrated system therefore treats generated content as a draft, exposes candidate state and feedback to the designer, and uses human checkpoints to decide whether a candidate should be revised, playtested, completed, or reviewed further.
