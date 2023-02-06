import hashlib
import base64
from shopihq_service.settings import Settings as settings


class BasicAuthUtils:
    @staticmethod
    def _generate_token(username, password):
        token = f"{username}:{password}".encode("utf-8")
        encoded_token = base64.b64encode(token).decode("utf-8")
        return encoded_token

    def basic_auth(self, username, password):
        return "Basic " + self._generate_token(username, password)


def get_url_with_endpoint(endpoint):
    """
    :param endpoint:
    :return:
    """
    shopi_url = getattr(settings, 'SHOPIHQ_BACKEND_URL')
    return f"{shopi_url}{endpoint}"
