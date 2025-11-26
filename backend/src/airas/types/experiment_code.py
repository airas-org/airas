from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ExperimentCode(BaseModel):
    train_py: str = ""
    evaluate_py: str = ""
    preprocess_py: str = ""
    model_py: str = ""
    main_py: str = ""
    pyproject_toml: str = ""
    config_yaml: str = ""
    run_configs: Optional[dict[str, str]] = Field(
        None, description="Run configuration YAMLs keyed by run_id"
    )

    def to_file_dict(self) -> dict[str, str]:
        files = {
            "src/train.py": self.train_py,
            "src/evaluate.py": self.evaluate_py,
            "src/preprocess.py": self.preprocess_py,
            "src/model.py": self.model_py,
            "src/main.py": self.main_py,
            "pyproject.toml": self.pyproject_toml,
            "config/config.yaml": self.config_yaml,
        }
        if self.run_configs:
            files.update(
                {
                    f"config/runs/{run_id}.yaml": yaml_content
                    for run_id, yaml_content in self.run_configs.items()
                }
            )
        return files
