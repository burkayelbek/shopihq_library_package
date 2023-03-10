import requests
import json
import re
from shopihq_service.utils import get_url_with_endpoint, get_order_status_mapping
from shopihq_service.utils import BasicAuthUtils


class ShopihqOrderService(object):
    auth = BasicAuthUtils()

    def __init__(self, username, password):
        self.headers = {"Content-Type": "application/json", "Authorization": self.auth.basic_auth(username=username, password=password)}

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
            response = requests.Response()
            response.status_code = refund_response.status_code
            return response
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
        path = get_url_with_endpoint(f'/Order/search?customerId={user_id}&SortDesc=true')
        response = requests.get(url=path, params=request.query_params, headers=self.headers)
        if response.status_code != 200:
            new_response = requests.Response()
            new_response.status_code = response.status_code
            new_response._content = response
            return new_response
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
                "orderitem_set": self._fill_orderitem_set(res),
                "is_cancelled": None,
                "is_cancellable": None,
                "is_refundable": None,
                "shipping_address": {
                    "pk": res["items"][0].get("deliveryAddress", {})["id"],
                    "email": res["items"][0].get("deliveryAddress", {})["email"],
                    "phone_number": res["items"][0].get("deliveryAddress", {})["phone"],
                    "first_name": res["items"][0].get("deliveryAddress", {})["fullName"].split()[0],
                    "last_name": res["items"][0].get("deliveryAddress", {})["fullName"].split()[1],
                    "country": {
                        "name": res["items"][0].get("deliveryAddress", {}).get("country", "")
                    },
                    "city": {
                        "name": res["items"][0].get("deliveryAddress", {}).get("city", "").upper()
                    },
                    "line": res["items"][0].get("deliveryAddress", {})["details"],
                    "title": None,
                    "township": {
                        "name": res["items"][0].get("deliveryAddress", {}).get("township", "")
                    },
                    "district": {
                        "name": res["items"][0].get("deliveryAddress", {}).get("district", "")
                    },
                    "postcode": res["items"][0].get("deliveryAddress", {}).get("zipPostalCode", ""),
                    "company_name": "",
                    "tax_office": "",
                    "tax_no": "",
                    "e_bill_taxpayer": False,
                    "address_type": None,
                    "extra_field": None,
                    "is_corporate": False,
                    "primary": False
                },
                "billing_address": {
                    "pk": res.get("billingAddress", {})["id"],
                    "email": res.get("billingAddress", {})["email"],
                    "phone_number": res.get("billingAddress", {})["phone"],
                    "first_name": res.get("billingAddress", {})["fullName"].split()[0],
                    "last_name": res.get("billingAddress", {})["fullName"].split()[1],
                    "country": {
                        "name": res.get("billingAddress", {}).get("country", "")
                    },
                    "city": {
                        "name": res.get("billingAddress", {}).get("city", "").upper()
                    },
                    "line": res.get("billingAddress", {})["details"],
                    "title": None,
                    "township": {
                        "name": res.get("billingAddress", {}).get("township", "")
                    },
                    "district": {
                        "name": res.get("billingAddress", {}).get("district", "")
                    },
                    "postcode": res.get("billingAddress", {}).get("zipPostalCode", ""),
                    "company_name": "",
                    "tax_office": "",
                    "tax_no": "",
                    "e_bill_taxpayer": False,
                    "address_type": None,
                    "extra_field": None,
                    "is_corporate": False,
                    "primary": False
                },
                "shipping_company": {},
                "tracking_url": res["items"][0].get("shipment", {}).get("labelUrl", None),
                "created_date": res["createdOn"],
                "number": res["orderId"],
                "amount": res["totalPrice"],
                "discount_amount": None,
                "shipping_amount": res["shippingCost"],
                "shipping_option_slug": None,
                "payment_option_slug": None,
                "amount_without_discount": res.get("subTotalPrice", 0),
                "installment_count": res["payments"][0].get("installmentCount", None),
                "payment_option": {
                    "name": res["payments"][0].get("paymentType", None)
                }
            }
            data.append(response_data)
        results = {"count": count, "results": data}
        response = requests.Response()
        response.status_code = 200
        response._content = json.dumps(results).encode()
        return response

    def order_search_by_id(self, request, order_id):
        """
        :param order_id:
        :param request:
        :return:
        """
        response_data = {}
        path = get_url_with_endpoint(f'/Order/search?orderIds={order_id}')
        response = requests.get(url=path, params=request.query_params, headers=self.headers)
        if response.status_code != 200:
            new_response = requests.Response()
            new_response.status_code = response.status_code
            new_response._content = response
            return new_response
        response_json = json.loads(response.content.decode())
        parsed_json = response_json.get("data", {}).get("results", [])
        orderitem_set = self._fill_orderitem_set(parsed_json)

        for res in parsed_json:
            response_data = {
                "id": res["orderId"],
                "status": {},
                "currency": {
                    "value": "try",
                    "label": "TL",
                },
                "orderitem_set": orderitem_set,
                "is_cancelled": None,
                "is_cancellable": None,
                "is_refundable": None,
                "shipping_address": {
                    "pk": res["items"][0].get("deliveryAddress", {})["id"],
                    "email": res["items"][0].get("deliveryAddress", {})["email"],
                    "phone_number": res["items"][0].get("deliveryAddress", {})["phone"],
                    "first_name": res["items"][0].get("deliveryAddress", {})["fullName"].split()[0],
                    "last_name": res["items"][0].get("deliveryAddress", {})["fullName"].split()[1],
                    "country": {
                        "name": res["items"][0].get("deliveryAddress", {}).get("country", "")
                    },
                    "city": {
                        "name": res["items"][0].get("deliveryAddress", {}).get("city", "").upper()
                    },
                    "line": res["items"][0].get("deliveryAddress", {})["details"],
                    "title": None,
                    "township": {
                        "name": res["items"][0].get("deliveryAddress", {}).get("township", "")
                    },
                    "district": {
                        "name": res["items"][0].get("deliveryAddress", {}).get("district", "")
                    },
                    "postcode": res["items"][0].get("deliveryAddress", {}).get("zipPostalCode", ""),
                    "company_name": "",
                    "tax_office": "",
                    "tax_no": "",
                    "e_bill_taxpayer": False,
                    "address_type": None,
                    "extra_field": None,
                    "is_corporate": False,
                    "primary": False
                },
                "billing_address": {
                    "pk": res.get("billingAddress", {})["id"],
                    "email": res.get("billingAddress", {})["email"],
                    "phone_number": res.get("billingAddress", {})["phone"],
                    "first_name": res.get("billingAddress", {})["fullName"].split()[0],
                    "last_name": res.get("billingAddress", {})["fullName"].split()[1],
                    "country": {
                        "name": res.get("billingAddress", {}).get("country", "")
                    },
                    "city": {
                        "name": res.get("billingAddress", {}).get("city", "").upper()
                    },
                    "line": res.get("billingAddress", {})["details"],
                    "title": None,
                    "township": {
                        "name": res.get("billingAddress", {}).get("township", "")
                    },
                    "district": {
                        "name": res.get("billingAddress", {}).get("district", "")
                    },
                    "postcode": res.get("billingAddress", {}).get("zipPostalCode", ""),
                    "company_name": "",
                    "tax_office": "",
                    "tax_no": "",
                    "e_bill_taxpayer": False,
                    "address_type": None,
                    "extra_field": None,
                    "is_corporate": False,
                    "primary": False
                },
                "shipping_company": {},
                "tracking_url": res["items"][0].get("shipment", {}).get("labelUrl", None),
                "created_date": res["createdOn"],
                "number": res["orderId"],
                "amount": res["totalPrice"],
                "discount_amount": None,
                "shipping_amount": res["shippingCost"],
                "shipping_option_slug": None,
                "payment_option_slug": None,
                "amount_without_discount": res.get("subTotalPrice", 0),
                "installment_count": res["payments"][0].get("installmentCount", None),
                "payment_option": {
                    "name": res["payments"][0].get("paymentType", None)
                }
            }

        response = requests.Response()
        response.status_code = 200
        response._content = json.dumps(response_data).encode()
        return response

    def _fill_orderitem_set(self, order_data):
        if not isinstance(order_data, list):
            order_data = [order_data]
        order_number = order_data[0].get("orderId", None)
        orderitem_status_check = any(orderitem["status"] == 50 for order in order_data for orderitem in order["items"])
        orderitem_set = [{
            "id": orderitem["orderItemId"],
            "status": get_order_status_mapping(orderitem),
            "price_currency": {
                "value": "try",
                "label": "TL"
            },
            "product": {
                "pk": orderitem["orderItemId"],
                # "sku": orderitem["productSku"],
                "sku": orderitem["productBarcode"],
                "base_code": orderitem["productBarcode"],
                "name": orderitem["productName"],
                "image": orderitem.get("productUrl", None),
                "absolute_url": "#",
                "attributes": {
                    "integration_sap_COLOR": orderitem.get("productColor", None),
                    "integration_sap_SIZE1": orderitem.get("productSize", None),
                    "integration_sap_BRAND": orderitem.get("productBrand", None),
                },
                "attributes_kwargs": {}
            },
            "is_cancelled": True if orderitem["status"] == 50 else False,
            "is_cancellable": orderitem["isCancelable"],
            "is_refundable": orderitem["isRefunded"],
            "active_cancellation_request": None,
            "shipping_company": {
                "name": None,
                "label": orderitem.get("shipment", {}).get("provider", None)
            },
            "tracking_url": orderitem.get("shipment", {}).get("labelUrl", None),
            "price": orderitem["price"],
            "tax_rate": orderitem["taxRate"]
        } for order in order_data for orderitem in order["items"]]

        if orderitem_status_check:
            path = get_url_with_endpoint(f'/Order/isCancelable/{order_number}')
            response = requests.get(url=path, headers=self.headers)
            response_dict = json.loads(response.text)
            cancellable_items = response_dict.get('data').get('cancelableModel')

            matches_non_cancellable_items = [roi for roi in order_data[0]['items'] if
                                             any(order_item['orderItemId'] == roi['orderItemId'] and order_item['isCancelable'] == False and
                                                 roi["status"] == 50 for order_item in cancellable_items)]

            cancellation_requests = {}
            for orderitem in matches_non_cancellable_items:
                cancellation_requests = {
                    "cancellation_type": {
                        "value": "cancel",
                        "label": "??ptal"
                    },
                    "status": {
                        "value": "Completed",
                        "label": "Completed"
                    },
                    "easy_return": None,
                    "description": "",
                    "reason": next(roi["reasonForNonCancelable"][0] for roi in cancellable_items if roi['orderItemId'] == orderitem["orderItemId"]),
                    "order_item": orderitem.get("orderItemId", None)
                }

            for orderitem in orderitem_set:
                if orderitem["is_cancelled"]:
                    orderitem["active_cancellation_request"] = cancellation_requests

        return orderitem_set
