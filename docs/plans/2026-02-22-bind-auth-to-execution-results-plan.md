# Bind Authenticated User to Execution Results - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace hardcoded SYSTEM_USER_ID with the actual authenticated user ID from JWT in all endpoints that create research records.

**Architecture:** Use the existing `get_current_user_id()` FastAPI dependency to inject `created_by` server-side. The subgraph receives `created_by` as a constructor parameter instead of hardcoding it. When EE is disabled, falls back to `SYSTEM_USER_ID`.

**Tech Stack:** FastAPI, dependency-injector, Pydantic, SQLModel

---

### Task 1: Pass `created_by` through the Autonomous Research subgraph

**Files:**
- Modify: `backend/src/airas/usecases/autonomous_research/topic_open_ended_research/topic_open_ended_research_subgraph.py:263-311` (constructor)
- Modify: `backend/src/airas/usecases/autonomous_research/topic_open_ended_research/topic_open_ended_research_subgraph.py:646-660` (`_create_record`)

**Step 1: Add `created_by` parameter to `TopicOpenEndedResearchSubgraph.__init__`**

In the `__init__` method (line 263), add `created_by: UUID` parameter and store it:

```python
def __init__(
    self,
    github_client: GithubClient,
    arxiv_client: ArxivClient,
    langchain_client: LangChainClient,
    litellm_client: LiteLLMClient,
    qdrant_client: QdrantClient | None,
    e2e_service: TopicOpenEndedResearchServiceProtocol,
    runner_config: RunnerConfig,
    wandb_config: WandbConfig,
    task_id: UUID,
    created_by: UUID,  # <-- ADD THIS
    ...
):
    ...
    self.created_by = created_by  # <-- ADD THIS
```

**Step 2: Use `self.created_by` in `_create_record`**

Replace the hardcoded UUID at line 655:

```python
self.e2e_service.create(
    id=self.task_id,
    title="Untitled E2E Research Task",
    created_by=self.created_by,  # <-- CHANGE from UUID("00000000-...")
    status=Status.RUNNING,
    current_step=StepType.GENERATE_QUERIES,
    github_url=github_url,
)
```

---

### Task 2: Inject `created_by` from the API route into the subgraph

**Files:**
- Modify: `backend/api/routes/v1/topic_open_ended_research.py:1-10` (imports)
- Modify: `backend/api/routes/v1/topic_open_ended_research.py:40` (remove `DEFAULT_CREATED_BY`)
- Modify: `backend/api/routes/v1/topic_open_ended_research.py:52-63` (`_execute_topic_open_ended_research` signature)
- Modify: `backend/api/routes/v1/topic_open_ended_research.py:67-91` (subgraph construction)
- Modify: `backend/api/routes/v1/topic_open_ended_research.py:128-177` (route handler)

**Step 1: Add import for `get_current_user_id`**

Add to imports:

```python
from api.ee.auth.dependencies import get_current_user_id
```

**Step 2: Remove `DEFAULT_CREATED_BY` constant (line 40)**

Delete:
```python
DEFAULT_CREATED_BY = uuid.UUID("00000000-0000-0000-0000-000000000001")
```

**Step 3: Add `created_by` parameter to `_execute_topic_open_ended_research`**

```python
async def _execute_topic_open_ended_research(
    task_id: uuid.UUID,
    created_by: uuid.UUID,  # <-- ADD THIS
    request: TopicOpenEndedResearchRequestBody,
    ...
) -> None:
```

**Step 4: Pass `created_by` to subgraph constructor**

```python
graph = TopicOpenEndedResearchSubgraph(
    ...
    task_id=task_id,
    created_by=created_by,  # <-- ADD THIS
    ...
).build_graph()
```

**Step 5: Add `get_current_user_id` dependency to the route handler**

```python
@router.post("/run", response_model=TopicOpenEndedResearchResponseBody)
@inject
@observe()
async def execute_topic_open_ended_research(
    request: TopicOpenEndedResearchRequestBody,
    fastapi_request: Request,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],  # <-- ADD
    ...
) -> TopicOpenEndedResearchResponseBody:
```

**Step 6: Pass `created_by` to the async task**

```python
asyncio.create_task(
    _execute_topic_open_ended_research(
        task_id=task_id,
        created_by=current_user_id,  # <-- ADD THIS
        request=request,
        ...
    )
)
```

---

### Task 3: Use server-side `created_by` in Assisted Research endpoints

**Files:**
- Modify: `backend/api/schemas/assisted_research.py:14-16` (remove `created_by` from session request)
- Modify: `backend/api/schemas/assisted_research.py:28-35` (remove `created_by` from step request)
- Modify: `backend/api/routes/v1/assisted_research.py:1-28` (imports)
- Modify: `backend/api/routes/v1/assisted_research.py:32-48` (`create_session`)
- Modify: `backend/api/routes/v1/assisted_research.py:71-99` (`create_step`)

**Step 1: Remove `created_by` from request schemas**

In `AssistedResearchSessionCreateRequest`:
```python
class AssistedResearchSessionCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    # created_by removed - injected server-side
```

In `AssistedResearchStepCreateRequest`:
```python
class AssistedResearchStepCreateRequest(BaseModel):
    session_id: UUID
    # created_by removed - injected server-side
    status: Status
    step_type: StepType
    error_message: str | None
    result: Any
    schema_version: int = Field(ge=1)
```

**Step 2: Add import and dependency to route handlers**

Add import:
```python
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from api.ee.auth.dependencies import get_current_user_id
```

**Step 3: Update `create_session` to use `get_current_user_id`**

```python
@router.post("/session", response_model=AssistedResearchSessionResponse)
@inject
def create_session(
    request: AssistedResearchSessionCreateRequest,
    fastapi_request: Request,
    session_service: Annotated[
        AssistedResearchSessionService,
        Depends(Closing[Provide[Container.assisted_research_session_service]]),
    ],
) -> AssistedResearchSessionResponse:
    current_user_id = get_current_user_id(fastapi_request)
    session = session_service.create(title=request.title, created_by=current_user_id)
    ...
```

**Step 4: Update `create_step` to use `get_current_user_id`**

```python
@router.post("/step", response_model=AssistedResearchStepResponse)
@inject
def create_step(
    request: AssistedResearchStepCreateRequest,
    fastapi_request: Request,
    step_service: Annotated[
        AssistedResearchStepService,
        Depends(Closing[Provide[Container.assisted_research_step_service]]),
    ],
) -> AssistedResearchStepResponse:
    current_user_id = get_current_user_id(fastapi_request)
    step = step_service.create(
        session_id=request.session_id,
        created_by=current_user_id,
        ...
    )
    ...
```

---

### Task 4: Clean up unused imports in schemas

**Files:**
- Modify: `backend/api/schemas/assisted_research.py:8-10`

**Step 1: Remove unused re-exports**

The `__all__` re-export of `SYSTEM_USER_ID` and `get_current_user_id` is no longer needed in this file since routes import directly from `api.ee.auth.dependencies`:

```python
# Remove these lines:
from api.ee.auth.dependencies import SYSTEM_USER_ID, get_current_user_id
__all__ = ["SYSTEM_USER_ID", "get_current_user_id"]
```

---

### Task 5: Run linter and type checks

**Step 1: Run ruff**

```bash
cd /workspaces/airas && make ruff
```

**Step 2: Run mypy**

```bash
cd /workspaces/airas && make mypy
```

**Step 3: Fix any issues found**
