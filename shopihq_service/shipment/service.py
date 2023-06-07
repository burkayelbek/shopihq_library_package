import requests
import json
from shopihq_service.helpers.utils import get_url_with_endpoint
from shopihq_service.helpers.utils import BasicAuthUtils


class ShopihqShipmentService(object):
    auth = BasicAuthUtils()

    def __init__(self, username, password):
        self.headers = {"Content-Type": "application/json", "Authorization": self.auth.basic_auth(username=username, password=password)}

    def shipment_availability(self, request):
        """
        Method: POST
        :param request:
        :return:
        """
        path = get_url_with_endpoint('Shipment/availability')
        response = requests.post(url=path, headers=self.headers, data=json.dumps(request.data))
        return response
