import requests
from shopihq_service.utils import get_url_with_endpoint


class ShopihqOrderService(object):
    def __init__(self):
        self.headers = {"Content-Type": "application/json"}

    def get_reasons(self, request):
        """
        Method: GET
        :param request: Ex: ?type=0&language=1
        : type=0 -> Cancel, type=1 -> Refund, language=0 -> Turkish, language=1 -> English
        :return:
        """
        path = get_url_with_endpoint('/Order/reasons')
        response = requests.get(url=path, params=request.query_params)
        return response


    def order_search(self, request):
        pass
