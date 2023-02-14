import requests
import json
import re
from shopihq_service.utils import get_url_with_endpoint
from shopihq_service.utils import BasicAuthUtils


class ShopihqOrderService(object):
    auth = BasicAuthUtils()

    def __init__(self):
        self.headers = {"Content-Type": "application/json", "Authorization": self.auth.basic_auth()}

    def get_reasons(self, request):
        """
        Method: GET
        :param request: Ex: ?type=0&language=1
        : type=0 -> Cancel, type=1 -> Refund, language=0 -> Turkish, language=1 -> English
        :return:
        """
        data = []
        path = get_url_with_endpoint('/Order/reasons')
        website_url = request.META.get('PATH_INFO')
        match = re.search(r'/en/|/en', website_url)
        if match:
            # Website language is English
            language = 1
        else:
            # Website language is default (Turkish)
            language = 0
        cancel_params = {'type': 0, 'language': language}
        refund_params = {'type': 1, 'language': language}
        cancel_response = requests.get(url=path, params=cancel_params, headers=self.headers)
        refund_response = requests.get(url=path, params=refund_params, headers=self.headers)
        if (cancel_response.status_code and refund_response.status_code) != 200:
            raise Exception(
                f"Error: API returned status code CancelAPI: {cancel_response.status_code} "
                f"& REFUND API: {refund_response.status_code}")
        response_json_cancel = json.loads(cancel_response.content.decode())
        response_json_refund = json.loads(refund_response.content.decode())
        parsed_json = response_json_cancel.get('data', {}).get('reasonList', []) + response_json_refund.get('data', {}).get(
            'reasonList', [])

        for index, res in enumerate(parsed_json, start=1):
            response_data = {
                "id": res['reasonId'],
                "cancellation_type": "cancel" if res.get("reasonId") not in [d["id"] for d in data] and res in response_json_cancel.get('data').get(
                    'reasonList') else "refund",
                "subject": res['reason'],
                "extra_information_needed": True if res.get("reasonId") == -1 else False,
                "order": index,

            }
            data.append(response_data)
        results = {"count": data.__len__(), "results": data}
        response = requests.Response()
        response.status_code = 200
        response._content = json.dumps(results).encode()
        return response

    def order_search(self, request, user_id):
        # ToDo: next & previous for pagination.
        """
        :param user_id:
        :param request:
        :return:
        """
        data = []
        path = get_url_with_endpoint(f'/Order/search?customerId={user_id}')
        response = requests.get(url=path, params=request.query_params, headers=self.headers)
        if response.status_code != 200:
            raise Exception(
                f"Error: API returned status code API: {response.status_code}")
        response_json = json.loads(response.content.decode())
        count = response_json.get("data", {})["totalCount"]
        parsed_json = response_json.get("data", {}).get("results", [])
        for res in parsed_json:
            response_data = {
                "id": res["orderId"],
                "status": {},
                "currency": {
                    "value": "try",
                    "label": "TL",
                },
                "orderitem_set": [{
                    "id": orderitem["orderItemId"],
                    "status": {},
                    "price_currency": {
                        "value": "try",
                        "label": "TL"
                    },
                    "product": {
                        "pk": orderitem["orderItemId"],
                        "sku": orderitem["productSku"],
                        "base_code": orderitem["productBarcode"],
                        "name": orderitem["productName"],
                        "image": orderitem.get("productUrl", None),
                        "absolute_url": None,
                        "attributes": {},
                        "attributes_kwargs": {}
                    },
                    "is_cancelled": None,
                    "is_cancellable": orderitem["isCancelable"],
                    "is_refundable": orderitem["isRefunded"],
                    "active_cancellation_request": {},
                    "shipping_company": {},
                    "tracking_url": None,
                    "price": orderitem["price"],
                    "tax_rate": orderitem["taxRate"]
                } for orderitem in res["items"]],
                "is_cancelled": None,
                "is_cancellable": None,
                "is_refundable": None,
                "shipping_address": {
                    "pk": res["items"][0].get("deliveryAddress", {})["id"],
                    "email": res["items"][0].get("deliveryAddress", {})["email"],
                    "phone_number": res["items"][0].get("deliveryAddress", {})["phone"],
                    "first_name": res["items"][0].get("deliveryAddress", {})["fullName"].split()[0],
                    "last_name": res["items"][0].get("deliveryAddress", {})["fullName"].split()[1],
                    "country": {},
                    "city": {},
                    "line": res["items"][0].get("deliveryAddress", {})["details"],
                    "title": None,
                    "township": {},
                    "district": {},
                    "postcode": res["items"][0].get("deliveryAddress", {})["zipPostalCode"],
                    "company_name": None,
                    "tax_office": None,
                    "tax_no": None,
                    "e_bill_taxpayer": False,
                    "address_type": None,
                    "extra_field": None,
                    "is_corporate": False,
                    "primary": False
                },
                "billing_address": {
                    "pk": res["billingAddress"]["id"],
                    "email": res["billingAddress"]["email"],
                    "phone_number": res["billingAddress"]["phone"],
                    "first_name": res["billingAddress"]["fullName"].split()[0],
                    "last_name": res["billingAddress"]["fullName"].split()[1],
                    "country": {},
                    "city": {},
                    "line": res["billingAddress"]["details"],
                    "title": None,
                    "township": {},
                    "district": {},
                    "postcode": res["billingAddress"]["zipPostalCode"],
                    "company_name": None,
                    "tax_office": None,
                    "tax_no": None,
                    "e_bill_taxpayer": False,
                    "address_type": None,
                    "extra_field": None,
                    "is_corporate": False,
                    "primary": False
                },
                "shipping_company": {},
                "tracking_url": None,
                "created_date": res["createdOn"],
                "number": res["orderId"],
                "amount": res["totalPrice"],
                "discount_amount": None,
                "shipping_amount": res["shippingCost"],
                "shipping_option_slug": None,
                "payment_option_slug": None
            }
            data.append(response_data)
        results = {"count": count, "results": data}
        response = requests.Response()
        response.status_code = 200
        response._content = json.dumps(results).encode()
        return response

    def order_search_by_id(self, request, order_id):
        """
        :param request:
        :return:
        """
        path = get_url_with_endpoint(f'/Order/search?orderIds={order_id}')
        response = requests.get(url=path, params=request.query_params, headers=self.headers)
        if response.status_code != 200:
            raise Exception(
                f"Error: API returned status code API: {response.status_code}")
        return response
