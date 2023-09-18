import requests
import json
from shopihq_service.helpers.utils import get_url_with_endpoint
from shopihq_service.helpers.utils import BasicAuthUtils


class ShopihqShipmentService(object):
    auth = BasicAuthUtils()

    def __init__(self, username, password):
        self.headers = {"Content-Type": "application/json",
                        "Authorization": self.auth.basic_auth(username=username, password=password)}

    def shipment_availability(self, request):
        """
        Method: POST
        :param request:
        :return:
        """
        path = get_url_with_endpoint('Shipment/availability')
        pre_order = request.get("pre_order", {})
        shipping_address = pre_order.get("shipping_address", {})
        city = shipping_address.get("city", {}).get("name", ("",))

        if '-' in city:
            city = city.split('-')[0].strip()

        payload = {
            "basketTotal": pre_order.get("total_amount", ""),
            "orderItems": [
                {
                    "integrationId": item.get("product", {}).get("sku", ""),
                    "quantity": item.get("quantity", 0),
                    "price": item.get("total_amount", "")
                }
                for item in pre_order.get("basket", {}).get("basketitem_set", [])
            ],
            "customerInfo": {
                "customerType": "",
                "firstName": shipping_address.get("first_name", ""),
                "lastName": shipping_address.get("last_name", ""),
                "phoneNumber": shipping_address.get("phone_number", ""),
                "email": shipping_address.get("email", ""),
            },
            "deliveryAddress": {
                "countryName": shipping_address.get("country", {}).get("name", ""),
                "cityName": city,
                "townName": shipping_address.get("township", {}).get("name", ""),
            }
        }
        response = requests.post(url=path, headers=self.headers, data=json.dumps(payload))
        return response
