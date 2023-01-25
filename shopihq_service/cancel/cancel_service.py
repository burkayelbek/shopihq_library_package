import requests
import json
from shopihq_service.utils import get_url_with_endpoint


class ShopihqCancelService(object):
    def __init__(self):
        self.headers = {"Content-Type": "application/json"}

    def is_cancellable(self, order_number):
        """
        Method: GET
        :param order_number:
        :return:
        """
        path = get_url_with_endpoint(f'/Order/isCancelable/{order_number}')
        response = requests.get(url=path)
        return response

    def cancel_order(self, request):
        # ToDo: Check the enum if user enter Other. Should write reasons in api.
        # ToDo: Has not been finished yet.
        path = get_url_with_endpoint('/Order/cancelOrder')
        pass





