import requests
import json
from shopihq_service.helpers.utils import get_url_with_endpoint
from shopihq_service.helpers.utils import BasicAuthUtils
from shopihq_service.helpers.custom_exceptions import handle_request_exception


class ShopihqCancelService(object):
    auth = BasicAuthUtils()

    def __init__(self, username, password):
        self.headers = {"Content-Type": "application/json",
                        "Authorization": self.auth.basic_auth(username=username, password=password)}

    def is_cancellable(self, order_number):
        """
        Method: GET
        :param order_number:
        :return:
        """
        path = get_url_with_endpoint(f'Order/isCancelable/{order_number}')
        try:
            response = requests.get(url=path, headers=self.headers)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            err = handle_request_exception(e)
            return err

    def is_draft_returnable(self, request):
        """
        Method: POST
        :param request:
        :return:
        """
        order_item_list = request["orderItems"]
        orderitem_id_list = [str(orderitem.get("orderItemId", "")) for orderitem in order_item_list]
        payload = {
            "orderId": request.get("orderId"),
            "orderItemIds": orderitem_id_list
        }
        path = get_url_with_endpoint('Return/isDraftReturnable')
        try:
            response = requests.post(url=path, headers=self.headers, data=json.dumps(payload))
            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            err = handle_request_exception(e)
            return err

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
                    "customerReason": int(orderitem["customerReason"]),
                    "customerStatement": orderitem["description"] if int(orderitem["customerReason"]) == -1 else ""
                }
                cancel_payload["orderItems"].append(order_item_payload)
            else:
                order_item_payload = {
                    "orderItemExternalId": orderitem.get("orderItemId", ""),
                    "customerReason": int(orderitem["customerReason"]),
                    "customerStatement": orderitem["description"] if int(orderitem["customerReason"]) == -1 else ""
                }
                return_payload["orderItemList"].append(order_item_payload)

        if cancel_payload["orderItems"]:
            response = self.is_cancellable(order_number=order_id)
            response_json = json.loads(response.content.decode())
            data = response_json.get("data", {}).get("cancelableModel", [])
            is_cancellable = all(cancellable_status.get("isCancelable", False) for cancellable_status in data
                                 for orderitem in order_items
                                 if cancellable_status.get("orderItemId", "") == orderitem.get("orderItemId", ""))

            if is_cancellable:
                path = get_url_with_endpoint('/Order/cancelOrder')
                response = requests.post(url=path, headers=self.headers, json=cancel_payload)
                return response
            return {}

        if return_payload["orderItemList"]:
            response = self.is_draft_returnable(request=request_data)
            response_json = json.loads(response.content.decode())
            data = response_json.get("data")
            is_returnable = all(draft_status.get("isDraftReturnable", False) for draft_status in data
                                for orderitem in order_items
                                if draft_status.get("orderItemExternalId") == orderitem.get("orderItemId", ""))

            if is_returnable:
                path = get_url_with_endpoint('/Return/createDraftReturnShipment')
                response = requests.post(url=path, headers=self.headers, json=return_payload)
                return response
            return {}
