import requests
from shopihq_service.settings import Settings as settings
import json


class ShopihqCancelService(object):

    @staticmethod
    def _get_url_with_endpoint(endpoint):
        """
        :param endpoint:
        :return:
        """
        shopi_url = getattr(settings, 'SHOPIHQ_URL')
        return f"{shopi_url}{endpoint}"

    def get_reasons(self, request):
        """
        Method: GET
        :param request:
        :return:
        """
        path = self._get_url_with_endpoint('/Order/reasons')
        response = requests.get(url=path, params=request.query_params)
        if response.status_code == 200:
            return response
        else:
            return False

    def is_cancellable(self, order_number):
        """
        Method: GET
        :param order_number:
        :return:
        """
        path = self._get_url_with_endpoint(f'/Order/isCancelable/{order_number}')
        response = requests.get(url=path)
        return response

    def cancel_order(self, request):
        # ToDo: Check the enum if user enter Other. Should write reasons in api.
        path = self._get_url_with_endpoint('/Order/cancelOrder')
        pass

    def is_draft_returnable(self, request):
        """
        :param request:
        :return:
        """
        path = self._get_url_with_endpoint('/Return/isDraftReturnable')
        headers = {"Content-Type": "application/json"}
        response = requests.post(url=path, headers=headers, data=json.dumps(request.data))
        return response

    def create_draft_return_shipment(self):
        pass

    def shipment_availability(self):
        pass
