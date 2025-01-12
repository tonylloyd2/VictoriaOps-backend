from django.apps import AppConfig

class ProductsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products"
    verbose_name = "Product Management"

    def ready(self):
        import products.signals  # noqa
