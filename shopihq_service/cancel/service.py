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

    def is_draft_returnable(self, request, extra_data=None):
        """
        Method: POST
        :param request:
        :return:
        """
        if isinstance(request, list):
            order_item_id_list = [str(item.get("order_item")) for item in request]
        else:
            try:
                order_item_id_list = [str(item.get("order_item")) for item in request.get("order_items", [])]
            except:
                order_item_id_list = [str(request.get("order_item"))]

        payload = {
            "orderId": request.get("order_id") if extra_data is None else extra_data,
            "orderItemIds": order_item_id_list
        }
        path = get_url_with_endpoint('Return/isDraftReturnable')
        try:
            response = requests.post(url=path, headers=self.headers, data=json.dumps(payload))
            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            err = handle_request_exception(e)
            return err

    def single_cancel_order(self, request):
        """
        Method: POST
        :param request:
        :return:
        """

        """
        {
          order_item: productId,
          reason: reason.value
          cancellation_type: "cancel"/"refund"
          description:: "xxxx"
          order_id: "xxxxx"
        }
        """

        order_id = request.data.get("order_id", "")
        order_item_id = request.data.get("order_item", "")

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

        cancellation_type = request.data.get("cancellation_type")
        if cancellation_type == "cancel":
            order_item_payload = {
                "orderItemId": str(request.data.get("order_item", "")),
                "customerReason": int(request.data.get("reason")),
                "customerStatement": request.data.get("description") if int(request.data.get("reason")) == -1 else ""
            }
            cancel_payload["orderItems"].append(order_item_payload)
        else:
            order_item_payload = {
                "orderItemExternalId": str(request.data.get("order_item", "")),
                "customerReason": int(request.data.get("reason")),
                "customerStatement": request.data.get("description") if int(request.data.get("reason")) == -1 else ""
            }
            return_payload["orderItemList"].append(order_item_payload)

        if cancel_payload["orderItems"]:
            response = self.is_cancellable(order_number=order_id)
            response_json = json.loads(response.content.decode())
            data = response_json.get("data", {}).get("cancelableModel", [])
            is_cancellable = all(cancellable_status.get("isCancelable", False) for cancellable_status in data
                                 if cancellable_status.get("orderItemId", "") == order_item_id)

            if is_cancellable:
                path = get_url_with_endpoint('Order/cancelOrder')
                response = requests.post(url=path, headers=self.headers, json=cancel_payload)
                return response
            return {}

        if return_payload["orderItemList"]:
            request = request.data
            response = self.is_draft_returnable(request=request)
            response_json = json.loads(response.content.decode())
            data = response_json.get("data")
            is_returnable = all(draft_status.get("isDraftReturnable", False) for draft_status in data
                                if draft_status.get("orderItemExternalId") == order_item_id)

            if is_returnable:
                path = get_url_with_endpoint('Return/createDraftReturnShipment')
                response = requests.post(url=path, headers=self.headers, json=return_payload)
                return response
            return {}

    def cancel_order(self, request):
        """
        Method: POST
        :param request:
        :return:
        """
        order_id = request.data.get("order_id")
        if not order_id:
            order_id = request.data.get("cancel_order_items", []).get("order_id", "")

        order_items = request.data.get("order_items")
        if not order_items:
            order_items = request.data.get("cancel_order_items", []).get("order_items", [])
        order_item_id_list = [str(item.get("order_item")) for item in order_items]

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
                    "orderItemId": str(orderitem.get("order_item", "")),
                    "customerReason": int(orderitem.get("reason")),
                    "customerStatement": orderitem.get("description") if int(orderitem.get("reason")) == -1 else ""
                }
                cancel_payload["orderItems"].append(order_item_payload)
            else:
                order_item_payload = {
                    "orderItemExternalId": str(orderitem.get("order_item", "")),
                    "customerReason": int(orderitem.get("reason")),
                    "customerStatement": orderitem.get("description") if int(orderitem.get("reason")) == -1 else ""
                }
                return_payload["orderItemList"].append(order_item_payload)

        if cancel_payload["orderItems"]:
            response = self.is_cancellable(order_number=order_id)
            response_json = json.loads(response.content.decode())
            data = response_json.get("data", {}).get("cancelableModel", [])
            is_cancellable = all(cancellable_status.get("isCancelable", False) for cancellable_status in data
                                 for orderitem in order_item_id_list
                                 if cancellable_status.get("orderItemId", "") == orderitem)

            if not is_cancellable:
                response.status_code = 400
                response.json = lambda: {}
                return response
            path = get_url_with_endpoint('Order/cancelOrder')
            response = requests.post(url=path, headers=self.headers, json=cancel_payload)
            return response

        if return_payload["orderItemList"]:
            response = self.is_draft_returnable(request=request.data)
            response_json = json.loads(response.content.decode())
            data = response_json.get("data")
            is_returnable = all(draft_status.get("isDraftReturnable", False) for draft_status in data
                                for orderitem in order_item_id_list
                                if draft_status.get("orderItemExternalId") == orderitem)

            if not is_returnable:
                response.status_code = 400
                response.json = lambda: {}
                return response
            path = get_url_with_endpoint('Return/createDraftReturnShipment')
            response = requests.post(url=path, headers=self.headers, json=return_payload)
            return response

    def bulk_cancel_order(self, request):
        request_data = request.data.get("cancel_order_items")
        user_id = request.user.id
        order_item_id = request_data[0].get("order_item")
        order_item_id_list = [str(item.get("order_item")) for item in request_data]
        order_number = self._get_order_by_orderitem_id(request=request, order_item_id=order_item_id, user_id=user_id)

        if not order_number:
            response = requests.Response()
            response.status_code = 400
            response._content = json.dumps({}).encode()
            return response

        cancel_payload = {
            "orderId": order_number,
            "orderItems": []
        }

        return_payload = {
            "orderId": order_number,
            "orderItemList": [],
            "returnDestinationNodeId": None,
            "shipmentProvider": "20",
            "deliveryAddressforRejectedReturn": None
        }

        for orderitem in request_data:
            cancellation_type = orderitem.get("cancellation_type")
            if cancellation_type == "cancel":
                order_item_payload = {
                    "orderItemId": str(orderitem.get("order_item", "")),
                    "customerReason": int(orderitem["reason"]),
                    "customerStatement": orderitem["description"] if int(orderitem["reason"]) == -1 else ""
                }
                cancel_payload["orderItems"].append(order_item_payload)
            else:
                order_item_payload = {
                    "orderItemExternalId": str(orderitem.get("order_item", "")),
                    "customerReason": int(orderitem["reason"]),
                    "customerStatement": orderitem["description"] if int(orderitem["reason"]) == -1 else ""
                }
                return_payload["orderItemList"].append(order_item_payload)

        if cancel_payload["orderItems"]:
            response = self.is_cancellable(order_number=order_number)
            response_json = json.loads(response.content.decode())
            data = response_json.get("data", {}).get("cancelableModel", [])
            is_cancellable = all(cancellable_status.get("isCancelable", False) for cancellable_status in data
                                 for orderitem in order_item_id_list
                                 if cancellable_status.get("orderItemId", "") == orderitem)

            if not is_cancellable:
                response.status_code = 400
                response.json = lambda: {}
                return response
            path = get_url_with_endpoint('Order/cancelOrder')
            response = requests.post(url=path, headers=self.headers, json=cancel_payload)
            return response

        if return_payload["orderItemList"]:
            response = self.is_draft_returnable(request=request_data, extra_data=order_number)
            response_json = json.loads(response.content.decode())
            data = response_json.get("data")
            is_returnable = all(draft_status.get("isDraftReturnable", False) for draft_status in data
                                for orderitem in order_item_id_list
                                if draft_status.get("orderItemExternalId") == orderitem)

            if not is_returnable:
                response.status_code = 400
                response.json = lambda: {}
                return response
            path = get_url_with_endpoint('Return/createDraftReturnShipment')
            response = requests.post(url=path, headers=self.headers, json=return_payload)
            return response

    def _get_order_by_orderitem_id(self, request, user_id, order_item_id):
        path = get_url_with_endpoint(
            f'Order/search?OrderItemId={order_item_id}&customerId={user_id}')
        try:
            response = requests.get(url=path, params=request.query_params, headers=self.headers)
            response.raise_for_status()

        except requests.exceptions.RequestException as e:
            return handle_request_exception(e)

        response_json = json.loads(response.content.decode())
        order_id = response_json.get("data", {}).get("results", [])[0].get("orderId", "")

        if not order_id:
            return None

        return order_id
