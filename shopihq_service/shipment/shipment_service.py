import requests
import json
from shopihq_service.utils import get_url_with_endpoint


class ShopihqShipmentService(object):
    def __init__(self):
        self.headers = {"Content-Type": "application/json"}

    def shipment_availability(self, request):
        """
        Method: POST
        :param request:
        :return:
        """
        path = get_url_with_endpoint('/Shipment/availability')
        response = requests.post(url=path, headers=self.headers, data=json.dumps(request.data))
        return response
