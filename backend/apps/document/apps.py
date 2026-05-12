from django.apps import AppConfig


class DocumentConfig(AppConfig):
    name = 'apps.document'

    def ready(self):
        import apps.document.signals