import os
from dataclasses import dataclass


@dataclass(frozen=True)
class EESettings:
    enabled: bool
    supabase_url: str
    supabase_anon_key: str
    supabase_jwt_secret: str


def get_ee_settings() -> EESettings:
    return EESettings(
        enabled=os.getenv("ENTERPRISE_ENABLED", "false").lower() == "true",
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_anon_key=os.getenv("SUPABASE_ANON_KEY", ""),
        supabase_jwt_secret=os.getenv("SUPABASE_JWT_SECRET", ""),
    )
