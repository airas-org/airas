import time
from functools import wraps
from logging import getLogger

from typing import Callable
from typing_extensions import TypedDict

logger = getLogger(__name__)


class ExecutionTimeState(TypedDict):
    execution_time: dict[str, dict[str, list[float]]]


def time_node(
    subgraph_name: str, 
    node_name: str | None = None
) -> Callable[..., Callable[..., object]]:
    def decorator(func):
        actual_node = node_name or func.__name__

        @wraps(func)
        def wrapper(self, state, *args, **kwargs):
            header = f"[{subgraph_name}.{actual_node}]".ljust(40)
            logger.info(f"{header} Start")
            start = time.time()

            result = func(self, state, *args, **kwargs)
            end = time.time()
            duration = round(end - start, 4)

            execution_time = state.get("execution_time", {})
            subgraph_log = execution_time.get(subgraph_name, {})
            durations = subgraph_log.get(actual_node, [])
            durations.append(duration)

            subgraph_log[actual_node] = durations
            execution_time[subgraph_name] = subgraph_log
            state["execution_time"] = execution_time

            logger.info(f"{header} End    Execution Time: {duration:7.4f} seconds")
            return result

        return wrapper

    return decorator


def time_subgraph(subgraph_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(state, *args, **kwargs):
            header = f"[{subgraph_name}]".ljust(40)
            logger.info(f"{header} Start")
            start = time.time()
            result = func(state, *args, **kwargs)
            end = time.time()
            duration = round(end - start, 4)

            timings = state.get("execution_time", {})
            subgraph_log = timings.get(subgraph_name, {})
            durations = subgraph_log.get("__subgraph_total__", [])
            durations.append(duration)
            subgraph_log["__subgraph_total__"] = durations
            timings[subgraph_name] = subgraph_log
            state["execution_time"] = timings

            logger.info(f"{header} End    Execution Time: {duration:7.4f} seconds")
            return result

        return wrapper

    return decorator

__all__ = ["time_node", "time_subgraph", "ExecutionTimeState"]
