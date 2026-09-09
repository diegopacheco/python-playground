import atexit
import os
from typing import Optional

from dotenv import load_dotenv
from posthog import Posthog

load_dotenv()


def _initialize_posthog() -> Optional[Posthog]:
    project_token = os.getenv("POSTHOG_PROJECT_TOKEN")
    host = os.getenv("POSTHOG_HOST")

    if not project_token or not host:
        if os.getenv("PYTHON_ENV") in {"development", "debug"}:
            missing_variable = "POSTHOG_PROJECT_TOKEN" if not project_token else "POSTHOG_HOST"
            raise RuntimeError(
                f"{missing_variable} variable required by PostHog is missing or "
                f"un-configured, this causes events to be silently missed. This error "
                f"stops appearing once {missing_variable} is configured"
            )
        return None

    return Posthog(
        project_token,
        host=host,
        enable_exception_autocapture=True,
    )


posthog_client = _initialize_posthog()

if posthog_client:
    atexit.register(posthog_client.shutdown)
