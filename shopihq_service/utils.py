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


def get_order_status_mapping(order_data):
    if not isinstance(order_data, dict):
        order_data = {order_data}
    order_status = order_data["status"]

    refund_info_status = [orderitem_refund.get("returnStatus") for orderitem_refund in order_data["returnInfo"]]
    state_mapping = {
        210: {"value": "450", "label": "Hazırlanıyor"},
        240: {"value": "500", "label": "Kargolandı"},
        330: {"value": "450", "label": "Hazırlanıyor"},
        410: {"value": "500", "label": "Kargolandı"},
        425: {"value": "500", "label": "Kargolandı"},
        510: {"value": "450", "label": "Hazırlanıyor"},
        540: {"value": "550", "label": "Delivered"},
        50: {"value": "100", "label": "İptal Edildi"}
    }
    if order_status == 540 and any(status == 635 for status in refund_info_status):
        return {"value": "600", "label": "İade edildi"}
    if order_status not in state_mapping:
        return {}
    return state_mapping[order_status]
