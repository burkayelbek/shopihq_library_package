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

    def is_draft_returnable(self, request):
        """
        Method: POST
        :param request:
        :return:
        """
        path = get_url_with_endpoint('/Return/isDraftReturnable')
        response = requests.post(url=path, headers=self.headers, data=json.dumps(request.data))
        return response

    def cancel_order(self, request):
        """
        Method: POST
        :param request:
        :return:
        """
        request_data = request.data.get("cancel_order_items", {})
        order_id = request_data.get("orderId", "")
        order_items = request_data.get("orderItems", [])

        cancel_payload = {
            "orderId": order_id,
            "orderItems": []
        }

        return_payload = {
            "orderId": order_id,
            "orderItemList": [],
            "returnDestinationNodeId": None,
            "shipmentProvider": "20",
            "deliveryAddressforRejectedReturn": None
        }

        for orderitem in order_items:
            cancellation_type = orderitem.get("cancellation_type")
            if cancellation_type == "cancel":
                order_item_payload = {
                    "orderItemId": orderitem.get("orderItemId", ""),
                    "customerReason": int(orderitem["customerReason"])
                }
                cancel_payload["orderItems"].append(order_item_payload)
            else:
                order_item_payload = {
                    "orderItemExternalId": orderitem.get("orderItemId", ""),
                    "customerReason": int(orderitem["customerReason"])
                }
                return_payload["orderItemList"].append(order_item_payload)

        if cancel_payload["orderItems"]:
            path = get_url_with_endpoint('/Order/cancelOrder')
            response = requests.post(url=path, headers=self.headers, json=cancel_payload)
            return response

        if return_payload["orderItemList"]:
            path = get_url_with_endpoint('/Return/createDraftReturnShipment')
            response = requests.post(url=path, headers=self.headers, json=return_payload)
            return response

    # def create_draft_return_shipment(self, request):
    #     """
    #     Method: POST
    #     :param request:
    #     :return:
    #     """
    #     path = get_url_with_endpoint('/Return/createDraftReturnShipment')
    #     response = requests.post(url=path, headers=self.headers, data=json.dumps(request.data))
    #     return response
