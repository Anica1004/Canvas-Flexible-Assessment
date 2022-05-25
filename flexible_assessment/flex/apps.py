from django.apps import AppConfig
from django.db.models.signals import post_migrate


class FlexConfig(AppConfig):
    """Extends AppConfig for startup routines"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'flex'

    def ready(self):
        """Creates groups based on models.Roles on server ready"""
        import flex.signals
        from .utils import create_groups
        # TODO: Check if needed
        post_migrate.connect(create_groups, sender=self)
