import hashlib
import base64
import re
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


def get_order_status_mapping(order_data, **kwargs):
    lang_code = kwargs.get("lang_code")
    if not isinstance(order_data, dict):
        order_data = {order_data}
    order_status = order_data["status"]
    if lang_code in ["tr-tr", "tr", "tr-TR"]:
        lang_code = "tr"
    else:
        lang_code = "en"

    refunded = any(return_info.get("returnStatus") == 635 for return_info in order_data.get("returnInfo", []))
    state_mapping = {
        210: {"value": "450", "label": {"en": "Preparing", "tr": "Hazırlanıyor"}},
        240: {"value": "450", "label": {"en": "Preparing", "tr": "Hazırlanıyor"}},
        330: {"value": "450", "label": {"en": "Preparing", "tr": "Hazırlanıyor"}},
        410: {"value": "450", "label": {"en": "Preparing", "tr": "Hazırlanıyor"}},
        242: {"value": "450", "label": {"en": "Preparing", "tr": "Hazırlanıyor"}},
        415: {"value": "500", "label": {"en": "Shipped", "tr": "Kargolandı"}},
        425: {"value": "500", "label": {"en": "Shipped", "tr": "Kargolandı"}},
        550: {"value": "500", "label": {"en": "Shipped", "tr": "Kargolandı"}},
        510: {"value": "450", "label": {"en": "Preparing", "tr": "Hazırlanıyor"}},
        540: {"value": "550", "label": {"en": "Delivered", "tr": "Teslim Edildi"}},
        50: {"value": "100", "label": {"en": "Cancelled", "tr": "İptal Edildi"}},
        10: {"value": "400", "label": {"en": "Approved", "tr": "Onaylandı"}},
        140: {"value": "400", "label": {"en": "Approved", "tr": "Onaylandı"}}
    }
    if refunded:
        return {"value": "600", "label": "Refunded" if lang_code == "en" else "İade Edildi"}
    if order_status not in state_mapping:
        return {}
    #return state_mapping[order_status]
    return {"value": state_mapping[order_status]["value"], "label": state_mapping[order_status]["label"][lang_code]} if order_status in state_mapping else {}



def check_full_name_compatibility(full_name):
    # Split the full name"
    if full_name is not None:
        name_parts = full_name.split()
        first_name = " ".join(name_parts[:-1]) if len(name_parts) > 1 else ""
        last_name = name_parts[-1] if name_parts else ""
    else:
        first_name = ""
        last_name = ""

    return first_name, last_name


def convert_to_int_and_remove_prefix(order_id_str):
    # Use regular expression to remove any leading non-digit characters
    order_id_digits = re.sub(r'^\D*', '', order_id_str)

    # Convert the remaining digits to an integer
    order_id = int(order_id_digits)
    return order_id
