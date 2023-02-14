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
        response = requests.get(url=path, headers=self.headers)
        return response

    def cancel_order(self, request):
        """
        Method: POST
        :param request:
        :return:
        """
        # ToDo --> Hint: is_cancellable method request is getting data long if data is more
        order_number = request.data['orderId']
        response_is_cancellable = self.is_cancellable(order_number=order_number)
        response_dict = json.loads(response_is_cancellable.text)
        cancellable_items = response_dict.get('data').get('cancelableModel')

        # Check if orderitem id cancellable value exist in cancellable model if it is true
        matches_is_cancelable_items = [roi for roi in request.data['orderItems'] if
                                       any(order_item['orderItemId'] == roi['orderItemId'] and order_item['isCancelable'] == True for
                                           order_item in cancellable_items)]

        if not matches_is_cancelable_items:
            print("Exception")

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
