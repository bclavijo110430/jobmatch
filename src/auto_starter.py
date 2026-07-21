import os
import time
import sys

os.environ.setdefault("AUTO_START", os.getenv("AUTO_START", "false"))
os.environ.setdefault("AUTO_INTERVAL", os.getenv("AUTO_INTERVAL", "30"))
os.environ.setdefault("AUTO_KEYWORD", os.getenv("AUTO_KEYWORD", ""))

if os.getenv("AUTO_START", "false").lower() != "true":
    print("[auto-starter] AUTO_START=false, skipping")
    sys.exit(0)

token = os.getenv("TELEGRAM_BOT_TOKEN", "")
chat = os.getenv("TELEGRAM_CHAT_ID", "")
if not token or not chat:
    print("[auto-starter] Telegram not configured, skipping")
    sys.exit(1)

interval = max(int(os.getenv("AUTO_INTERVAL", "30")), 1)
keyword = os.getenv("AUTO_KEYWORD", "")

time.sleep(10)

from src.automation import start_automation, is_automation_running

if is_automation_running():
    print("[auto-starter] Automation already running")
    sys.exit(0)

print(f"[auto-starter] Starting: keyword='{keyword}', interval={interval}min")

pid_file = "/app/data/auto_starter.pid"
with open(pid_file, "w") as f:
    f.write(str(os.getpid()))

# Restore persisted CV profile from DB (if user uploaded a CV via UI before)
from src.database import load_all_app_state
persisted = load_all_app_state()
profile = persisted.get("cv_profile") if isinstance(persisted.get("cv_profile"), dict) else {}
if profile:
    print(f"[auto-starter] Restored CV profile: skills={len(profile.get('skills', []))}, "
          f"titles={len(profile.get('target_titles', []))}")
else:
    print("[auto-starter] No persisted CV profile; using keyword-only filtering")

err = start_automation(
    profile=profile,
    keyword=keyword,
    interval_minutes=interval,
    log_callback=lambda msg: print(f"[auto] {msg}", flush=True),
    telegram_token=token,
    telegram_chat_id=chat,
    modality="Remoto,Híbrido",
)
if err:
    print(f"[auto-starter] ERROR: {err}")
else:
    print("[auto-starter] Started OK")

try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    print("[auto-starter] Stopped")