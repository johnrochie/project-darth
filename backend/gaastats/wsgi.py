"""
WSGI config for GAA Stats App
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gaastats.settings')

application = get_wsgi_application()
