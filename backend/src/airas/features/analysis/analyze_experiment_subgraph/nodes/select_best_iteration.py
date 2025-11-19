import logging

from airas.types.research_session import ResearchSession

logger = logging.getLogger(__name__)


def select_best_iteration(
    research_session: ResearchSession,
) -> ResearchSession:
    if not research_session.iterations:
        logger.warning("No iterations to compare")
        return research_session

    gaps = {
        iter.iteration_id: (
            (iter.experimental_analysis.aggregated_metrics.get("gap"))
            if getattr(iter.experimental_analysis, "aggregated_metrics", None)
            else None
        )
        for iter in research_session.iterations
    }

    if valid_gaps := {k: v for k, v in gaps.items() if v is not None}:
        best_id, best_gap = max(valid_gaps.items(), key=lambda x: x[1])
        research_session.best_iteration_id = best_id
        logger.info(f"Selected Iteration {best_id} as best (GAP: {best_gap:.2f}%)")
    else:
        logger.warning("No valid gaps found, defaulting to latest iteration")
        research_session.best_iteration_id = research_session.iterations[
            -1
        ].iteration_id

    return research_session
