from django.apps import AppConfig
class ChemicalDataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chemical_data'
    def ready(self):
        import chemical_data.signals



