"""
ASGI config for GAA Stats App with Channels support
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gaastats.settings')

# Import django channels after django setup
import django
django.setup()

from channels.routing import get_default_application

application = get_asgi_application()

# Make Django Channels work with ASGI
application = get_asgi_application()
