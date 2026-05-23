from datetime import datetime
from zoneinfo import ZoneInfo

SINGAPORE_TZ = ZoneInfo("Asia/Singapore")


def singapore_now() -> datetime:
    return datetime.now(SINGAPORE_TZ)
