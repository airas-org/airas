from uuid import UUID

from airas.infra.db.models.user_plan import PlanStatus, PlanType, UserPlanModel
from airas.repository.user_plan_repository import UserPlanRepository


class PlanService:
    def __init__(self, repo: UserPlanRepository):
        self.repo = repo

    def get_plan(self, user_id: UUID) -> UserPlanModel:
        plan = self.repo.get_by_user(user_id)
        if plan is None:
            plan = UserPlanModel(
                user_id=user_id,
                plan_type=PlanType.FREE,
                status=PlanStatus.ACTIVE,
            )
            return self.repo.create(plan)
        return plan

    def close(self) -> None:
        self.repo.db.close()
