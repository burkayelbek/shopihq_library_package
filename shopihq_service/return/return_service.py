import requests
import json
from shopihq_service.utils import get_url_with_endpoint


class ShopihqReturnService(object):
    def __init__(self):
        self.headers = {"Content-Type": "application/json"}

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
        # ToDo: Has not been finished yet.
        path = get_url_with_endpoint('/Return/createDraftReturnShipment')
        response = requests.post(url=path, headers=self.headers, data=json.dumps(request.data))
        return response