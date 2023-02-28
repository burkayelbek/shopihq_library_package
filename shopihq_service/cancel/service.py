import requests
import json
from shopihq_service.utils import get_url_with_endpoint
from shopihq_service.utils import BasicAuthUtils


class ShopihqCancelService(object):
    auth = BasicAuthUtils()

    def __init__(self, username, password):
        self.headers = {"Content-Type": "application/json", "Authorization": self.auth.basic_auth(username=username, password=password)}

    def is_cancellable(self, order_number):
        """
        Method: GET
        :param order_number:
        :return:
        """
        path = get_url_with_endpoint(f'/Order/isCancelable/{order_number}')
        response = requests.get(url=path, headers=self.headers)
        return response

    def cancel_order(self, request):
        """
        Method: POST
        :param request:
        :return:
        """
        path = get_url_with_endpoint('/Order/cancelOrder')
        response = requests.post(url=path, headers=self.headers, data=json.dumps(request.data))
        return response

    def is_draft_returnable(self, request):
        """
        Method: POST
        :param request:
        :return:
        """
        path = get_url_with_endpoint('/Return/isDraftReturnable')
        response = requests.post(url=path, headers=self.headers, data=json.dumps(request.data))
        return response

    def create_draft_return_shipment(self, request):
        """
        Method: POST
        :param request:
        :return:
        """
        path = get_url_with_endpoint('/Return/createDraftReturnShipment')
        response = requests.post(url=path, headers=self.headers, data=json.dumps(request.data))
        return response
