"""
WSGI config for tracker project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

for path in (BASE_DIR, PROJECT_ROOT):
	resolved = str(path)
	if resolved not in sys.path:
		sys.path.insert(0, resolved)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tracker.settings')

application = get_wsgi_application()
