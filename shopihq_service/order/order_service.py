import requests
from shopihq_service.utils import get_url_with_endpoint


class ShopihqOrderService(object):
    def __init__(self):
        self.headers = {"Content-Type": "application/json"}

    def get_reasons(self, request, env_var):
        """
        Method: GET
        :param env_var:
        :param request: Ex: ?type=0&language=1
        :return:
        """
        path = get_url_with_endpoint('/Order/reasons')
        response = requests.get(url=path, params=request.query_params, auth=env_var)
        return response
