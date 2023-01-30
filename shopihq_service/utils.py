from shopihq_service.settings import Settings as settings
import os


def get_url_with_endpoint(endpoint):
    """
    :param endpoint:
    :return:
    """
    shopi_url = getattr(settings, 'SHOPIHQ_BACKEND_URL')
    return f"{shopi_url}{endpoint}"


class EnvAccessor:
    def __getattr__(self, name):
        try:
            return os.environ[name]
        except KeyError:
            raise AttributeError(f"Attribute '{name}' does not exist in the .env file")

    def __setattr__(self, name, value):
        os.environ[name] = value
