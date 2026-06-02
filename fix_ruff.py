import os, re
files = {
    'backend/app/api/v1/endpoints/alerts.py': [
        (r'from backend\.app\.notifications\.whatsapp import whatsapp\n', ''),
        (r'\s*from alerts\.alert_manager import AlertManager\n', '\n'),
        (r'\s*manager = AlertManager\(\)\n', '\n')
    ],
    'backend/app/api/v1/endpoints/analysis.py': [
        (r'TokenPayload, get_current_user, require_role, UserRole', 'TokenPayload, require_role, UserRole')
    ],
    'backend/app/api/v1/endpoints/analytics.py': [
        (r'from typing import Optional\n', '')
    ],
    'backend/app/api/v1/endpoints/auth.py': [
        (r'\s*decode_token,\n', '\n')
    ],
    'backend/app/api/v1/endpoints/events.py': [
        (r'\s*thirty_days = today \+ timedelta\(days=30\)\n', '\n')
    ],
    'backend/app/api/v1/endpoints/forecast.py': [
        (r'from datetime import datetime, timedelta\n', ''),
        (r'\s*import os\n', '\n')
    ],
    'backend/app/api/v1/endpoints/shelves.py': [
        (r'from fastapi import APIRouter, Depends, Query', 'from fastapi import APIRouter, Depends')
    ],
    'backend/app/api/v1/endpoints/stores.py': [
        (r'from fastapi import APIRouter, Depends, HTTPException, status', 'from fastapi import APIRouter, Depends, status')
    ],
    'backend/app/api/v1/endpoints/webhooks.py': [
        (r'context = msg\.get\("context", \{\}\)', 'msg.get("context", {})'),
        (r'text = msg\.get\("text", \{\}\)\.get\("body", ""\)', 'msg.get("text", {}).get("body", "")'),
        (r'payment = payload\.get', 'payload.get'),
        (r'subscription = payload\.get', 'payload.get')
    ],
    'backend/app/core/config.py': [
        (r'from typing import Optional\n', '')
    ],
    'backend/app/core/encryption.py': [
        (r'import base64\n', ''),
        (r'from typing import Optional\n', '')
    ],
    'backend/app/core/security.py': [
        (r'import hashlib\n', '')
    ],
    'backend/app/db/database.py': [
        (r'from contextlib import asynccontextmanager\n', '')
    ],
    'backend/app/db/models.py': [
        (r'Text, func,', 'Text,'),
        (r'Text, func', 'Text')
    ],
    'backend/app/main.py': [
        (r'sys\.path\.insert\(0, str\(PROJECT_ROOT\)\)', 'sys.path.insert(0, str(PROJECT_ROOT))  # noqa: E402'),
        (r'from backend\.app\.core\.config import settings', 'from backend.app.core.config import settings  # noqa: E402'),
        (r'from backend\.app\.db\.database import init_db, close_db', 'from backend.app.db.database import init_db, close_db  # noqa: E402'),
        (r'from backend\.app\.services\.cache import cache', 'from backend.app.services.cache import cache  # noqa: E402'),
        (r'from backend\.app\.schemas\.schemas import HealthResponse', 'from backend.app.schemas.schemas import HealthResponse  # noqa: E402'),
        (r'from backend\.app\.api\.v1\.router import api_router', 'from backend.app.api.v1.router import api_router  # noqa: E402'),
        (r'from models\.shelf_detector import ShelfDetector', 'import models.shelf_detector'),
        (r'from models\.sku_recognizer import SKURecognizer', 'import models.sku_recognizer'),
        (r'from forecasting\.demand_forecaster import DemandForecaster', 'import forecasting.demand_forecaster'),
        (r'from alerts\.alert_manager import AlertManager', 'import alerts.alert_manager')
    ],
    'backend/app/notifications/whatsapp.py': [
        (r'import json\n', ''),
        (r'from backend\.app\.core\.encryption import decrypt_field\n', '')
    ],
    'backend/app/services/audit.py': [
        (r'from datetime import datetime, timezone\n', '')
    ],
    'backend/app/services/billing.py': [
        (r'import os\n', ''),
        (r'from datetime import datetime, timedelta\n', '')
    ],
    'backend/app/services/cache.py': [
        (r'import hashlib\n', '')
    ],
    'backend/app/services/quick_commerce.py': [
        (r'from typing import Optional\n', ''),
        (r'from backend\.app\.core\.config import settings\n', '')
    ],
    'backend/app/workers/tasks.py': [
        (r'from celery import Celery', 'from celery import Celery  # noqa: E402'),
        (r'from celery\.schedules import crontab', 'from celery.schedules import crontab  # noqa: E402'),
        (r'forecast = forecaster\.forecast', 'forecaster.forecast')
    ],
    'backend/tests/test_api_quick.py': [
        (r'import json\n', ''),
        (r'f"\\n\{\'=\' \* 65\}"', r'"\\n" + "=" * 65'),
        (r'f"  Frontend: http://localhost:5173"', r'"  Frontend: http://localhost:5173"'),
        (r'f"\{\'=\' \* 65\}"', r'"=" * 65')
    ]
}

for path, rules in files.items():
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        for pattern, repl in rules:
            content = re.sub(pattern, repl, content)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
