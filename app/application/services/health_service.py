from dataclasses import dataclass


@dataclass(slots=True)
class HealthService:
    app_name: str
    environment: str

    def execute(self) -> dict[str, str]:
        return {
            "status": "ok",
            "app": self.app_name,
            "environment": self.environment,
        }
