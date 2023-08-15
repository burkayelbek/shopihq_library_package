import requests
import json
import re
from urllib.parse import urlparse, urlencode, urlunparse
from shopihq_service.helpers.utils import BasicAuthUtils
from shopihq_service.helpers.utils import (
    get_url_with_endpoint,
    get_order_status_mapping,
    check_full_name_compatibility,
    convert_to_int_and_remove_prefix
)
from shopihq_service.helpers.custom_exceptions import handle_request_exception


class ShopihqOrderService(object):
    auth = BasicAuthUtils()

    def __init__(self, username, password):
        self.headers = {"Content-Type": "application/json",
                        "Authorization": self.auth.basic_auth(username=username, password=password)}

    def get_reasons(self, request, lang_code):
        """
        Method: GET
        :param lang_code:
        :param request: Ex: ?type=0&language=1
        : type=0 -> Cancel, type=1 -> Refund, language=0 -> Turkish, language=1 -> English
        :return:
        """
        data = []
        path = get_url_with_endpoint('Order/reasons')
        if lang_code not in ["tr-tr", "tr", "tr-TR"]:
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
        parsed_json = response_json_cancel.get('data', {}).get('reasonList', []) + response_json_refund.get('data',
                                                                                                            {}).get(
            'reasonList', [])

        for index, res in enumerate(parsed_json, start=1):
            response_data = {
                "id": res['reasonId'],
                "cancellation_type": "cancel" if res.get("reasonId") not in [d["id"] for d in
                                                                             data] and res in response_json_cancel.get(
                    'data').get(
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
        """
        :param user_id:
        :param request:
        :return:
        """
        data = []

        page_number = int(request.query_params.get('page', 1))  # Default to 1 if not specified
        path = get_url_with_endpoint(
            f'Order/search?customerId={user_id}&SortDesc=true&pageNumber={page_number}&pageSize=4')
        try:
            response = requests.get(url=path, params=request.query_params, headers=self.headers)

        except requests.exceptions.RequestException as e:
            return handle_request_exception(e)

        response_json = json.loads(response.content.decode())
        count = response_json.get("data", {}).get("totalCount", 0)
        parsed_json = response_json.get("data", {}).get("results", [])

        if not parsed_json:
            response.status_code = response.status_code
            response.json = lambda: {}
            return response

        order_id_search = request.query_params.get("search", None)
        if order_id_search:
            page_number = request.query_params.get("page", 1)
            response = self.order_search_by_id(request=request, order_id=order_id_search, page_number=page_number)
            response_json = json.loads(response.content.decode())
            if response_json != []:
                response_json = [response_json]
            results = {"count": 1, "next": None, "previous": None, "results": response_json}
            response = requests.Response()
            response.status_code = 200
            response._content = json.dumps(results).encode()
            return response

        for res in parsed_json:
            orderitem_set = self._fill_orderitem_set(order_data=res),
            parent_status = self._get_parent_status(orderitem=orderitem_set[0])
            first_name, last_name = check_full_name_compatibility(
                full_name=res.get("billingAddress", {}).get("fullName", ""))

            response_data = {
                "id": convert_to_int_and_remove_prefix(res["orderId"]),
                "status": parent_status,
                "currency": {
                    "value": "try",
                    "label": "TL",
                },
                "orderitem_set": orderitem_set[0],
                "is_cancelled": True if res.get("items", [])[0].get("status") == 50 or res.get("items", [])[0].get(
                    "isRefunded") == True else False,
                "is_cancellable": res.get("items", [])[0].get("isCancelable", False),
                "is_refundable": res.get("items", [])[0].get("isReturnable", False),
                "shipping_address": {
                    "pk": int(res["items"][0].get("deliveryAddress", {}).get("id", 0)),
                    "email": res["items"][0].get("deliveryAddress", {}).get("email", ""),
                    "phone_number": res["items"][0].get("deliveryAddress", {}).get("phone", ""),
                    "first_name": first_name,
                    "last_name": last_name,
                    "country": {
                        "pk": 0,
                        "name": res["items"][0].get("deliveryAddress", {}).get("country", "")
                    },
                    "city": {
                        "pk": 0,
                        "name": res["items"][0].get("deliveryAddress", {}).get("city", "").upper(),
                        "country": 0
                    },
                    "line": res["items"][0].get("deliveryAddress", {}).get("details", ""),
                    "title": "",
                    "township": {
                        "pk": 0,
                        "name": res["items"][0].get("deliveryAddress", {}).get("town", ""),
                        "city": 0
                    },
                    "district": {
                        "pk": 0,
                        "name": res["items"][0].get("deliveryAddress", {}).get("district", ""),
                        "township": 0,
                        "city": 0
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
                    "pk": int(res.get("billingAddress", {}).get("id", 0)),
                    "email": res.get("billingAddress", {}).get("email", ""),
                    "phone_number": res.get("billingAddress", {}).get("phone", ""),
                    "first_name": first_name,
                    "last_name": last_name,
                    "country": {
                        "pk": 0,
                        "name": res.get("billingAddress", {}).get("country", "")
                    },
                    "city": {
                        "pk": 0,
                        "name": res.get("billingAddress", {}).get("city", "").upper(),
                        "country": 0
                    },
                    "line": res.get("billingAddress", {}).get("details", ""),
                    "title": "",
                    "township": {
                        "pk": 0,
                        "name": res.get("billingAddress", {}).get("town", ""),
                        "city": 0
                    },
                    "district": {
                        "pk": 0,
                        "name": res.get("billingAddress", {}).get("district", ""),
                        "township": 0,
                        "city": 0
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
                "tracking_url": res["items"][0].get("shipment", {}).get("trackingUrl", None),
                "created_date": res["createdOn"]+'Z',
                "number": res["orderId"],
                "amount": str(res["totalPrice"]),
                "discount_amount": "",
                "shipping_amount": str(res["shippingCost"]),
                "shipping_option_slug": None,
                "payment_option_slug": None,
                "amount_without_discount": res.get("subTotalPrice", 0),
                "installment_count": res["payments"][0].get("installmentCount", None),
                "payment_option": {
                    "name": "Kredi Kartı"
                }
            }
            data.append(response_data)

        base_url = request.build_absolute_uri()
        url_parts = list(urlparse(base_url))
        query_params = dict(request.query_params)
        if page_number > 1:
            query_params["format"] = "json"
            query_params['page'] = page_number - 1
            url_parts[4] = urlencode(query_params, doseq=True)
            prev_url = urlunparse(url_parts)
        else:
            prev_url = None

        # Each page has 10 order to show and calculate manually.
        if count > (page_number * 10):
            query_params["format"] = "json"
            query_params['page'] = page_number + 1
            url_parts[4] = urlencode(query_params, doseq=True)
            next_url = urlunparse(url_parts)
        else:
            next_url = None
        results = {"count": count, "next": next_url, "previous": prev_url, "results": data}
        response = requests.Response()
        response.status_code = 200
        response._content = json.dumps(results).encode()
        return response

    def order_search_by_id(self, request, order_id, **kwargs):
        """
        :param order_id:
        :param request:
        :return:
        """
        response_data = {}
        page_number = kwargs.get("page_number", 1)
        path = get_url_with_endpoint(f'Order/search?orderIds={order_id}&pageNumber={page_number}')
        try:
            response = requests.get(url=path, params=request.query_params, headers=self.headers)
            response.raise_for_status()

        except requests.exceptions.RequestException as e:
            return handle_request_exception(e)

        response_json = json.loads(response.content.decode())
        count = response_json.get("data", {}).get("totalCount")
        parsed_json = response_json.get("data", {}).get("results", [])

        # Mobile Search Control
        if int(page_number) > 1 and parsed_json == []:
            response = requests.Response()
            response.status_code = 200
            response._content = json.dumps(parsed_json).encode()
            return response

        if count == 0 and parsed_json == []:
            if order_id and order_id[0].isalpha():
                order_id = order_id[1:]
                try:
                    path = get_url_with_endpoint(f'Order/search?orderIds={order_id}')
                    response = requests.get(url=path, params=request.query_params, headers=self.headers)
                    response_json = json.loads(response.content.decode())
                    parsed_json = response_json.get("data", {}).get("results", [])
                    response.raise_for_status()

                except requests.exceptions.RequestException as e:
                    return handle_request_exception(e)

        if not parsed_json:
            response.status_code = 404
            response.json = lambda: {}
            return response

        orderitem_set = self._fill_orderitem_set(order_data=parsed_json)
        parent_status = self._get_parent_status(orderitem=orderitem_set)
        is_cancellable, is_refundable, is_cancelled = self._general_refund_cancel_statuses(order_item=orderitem_set)
        first_name, last_name = check_full_name_compatibility(
            full_name=parsed_json[0].get("billingAddress", {}).get("fullName", ""))

        for res in parsed_json:
            response_data = {
                "id": convert_to_int_and_remove_prefix(res["orderId"]),
                "status": parent_status,
                "currency": {
                    "value": "try",
                    "label": "TL",
                },
                "orderitem_set": orderitem_set,
                "is_cancelled": is_cancelled,
                "is_cancellable": is_cancellable,
                "is_refundable": is_refundable,
                "shipping_address": {
                    "pk": int(res["items"][0].get("deliveryAddress", {}).get("id", 0)),
                    "email": res["items"][0].get("deliveryAddress", {}).get("email", ""),
                    "phone_number": res["items"][0].get("deliveryAddress", {}).get("phone", ""),
                    "first_name": first_name,
                    "last_name": last_name,
                    "country": {
                        "pk": 0,
                        "name": res["items"][0].get("deliveryAddress", {}).get("country", "")
                    },
                    "city": {
                        "pk": 0,
                        "name": res["items"][0].get("deliveryAddress", {}).get("city", "").upper(),
                        "country": 0
                    },
                    "line": res["items"][0].get("deliveryAddress", {}).get("details", ""),
                    "title": "",
                    "township": {
                        "pk": 0,
                        "name": res["items"][0].get("deliveryAddress", {}).get("town", ""),
                        "city": 0
                    },
                    "district": {
                        "pk": 0,
                        "name": res["items"][0].get("deliveryAddress", {}).get("district", ""),
                        "township": 0,
                        "city": 0
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
                    "pk": int(res.get("billingAddress", {}).get("id", 0)),
                    "email": res.get("billingAddress", {}).get("email", ""),
                    "phone_number": res.get("billingAddress", {}).get("phone", ""),
                    "first_name": first_name,
                    "last_name": last_name,
                    "country": {
                        "pk": 0,
                        "name": res.get("billingAddress", {}).get("country", "")
                    },
                    "city": {
                        "pk": 0,
                        "name": res.get("billingAddress", {}).get("city", "").upper(),
                        "country": 0
                    },
                    "line": res.get("billingAddress", {})["details"],
                    "title": "",
                    "township": {
                        "pk": 0,
                        "name": res.get("billingAddress", {}).get("town", ""),
                        "city": 0
                    },
                    "district": {
                        "pk": 0,
                        "name": res.get("billingAddress", {}).get("district", ""),
                        "township": 0,
                        "city": 0
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
                "tracking_url": res["items"][0].get("shipment", {}).get("trackingUrl", None),
                "created_date": res["createdOn"]+'Z',
                "number": res["orderId"],
                "amount": str(res["totalPrice"]),
                "discount_amount": "",
                "shipping_amount": str(res["shippingCost"]),
                "shipping_option_slug": None,
                "payment_option_slug": None,
                "amount_without_discount": res.get("subTotalPrice", 0),
                "installment_count": res["payments"][0].get("installmentCount", None),
                "payment_option": {
                    "name": "Kredi Kartı"
                }
            }

        response = requests.Response()
        response.status_code = 200
        response._content = json.dumps(response_data).encode()
        return response

    def _fill_orderitem_set(self, order_data):
        if not isinstance(order_data, list):
            order_data = [order_data]
        acceptable_refund_statuses = [425, 540]
        not_acceptable_return_statuses = [2, 635]
        order_data = order_data[0]
        order_items = order_data.get("items", [])
        order_number = order_data.get("orderId", "")
        orderitem_refund_status_check = any(
            orderitem["status"] in acceptable_refund_statuses
            and len(orderitem["returnInfo"]) >= 1
            and not any(
                return_info.get("returnStatus") in not_acceptable_return_statuses
                for return_info in sorted(
                    orderitem.get("returnInfo", []), key=lambda x: x['returnStatus']
                )[-1:]
            )
            for orderitem in order_items
        )

        # cancellation_requests = {}
        orderitem_set = [{
            "id": int(orderitem.get("orderItemId")),
            "status": get_order_status_mapping(orderitem),
            "price_currency": {
                "value": "try",
                "label": "TL"
            },
            "product": {
                "pk": int(orderitem.get("orderItemId")),
                "sku": orderitem.get("productSku", ""),
                "base_code": orderitem.get("productBarcode", ""),
                "name": orderitem.get("productName", ""),
                "image": orderitem.get("productUrl", None),
                "absolute_url": "#",
                "attributes": {
                    "integration_sap_COLOR": orderitem.get("productColor", ""),
                    "integration_sap_SIZE1": orderitem.get("productSize", ""),
                    "integration_sap_BRAND": orderitem.get("productBrand", ""),
                },
                "attributes_kwargs": {
                    "integration_sap_COLOR": {
                        "label": orderitem.get("productColor", "")
                    },
                    "integration_sap_SIZE1": {
                        "label": orderitem.get("productSize", "")
                    },
                    "integration_sap_BRAND": {
                        "label": orderitem.get("productBrand", "")
                    }
                }
            },
            "is_cancelled": True if orderitem["status"] == 50 or orderitem["isRefunded"] == True else False,
            "is_cancellable": orderitem["isCancelable"],
            "is_refundable": orderitem["isReturnable"],
            "cancellationrequest_set": [],
            "active_cancellation_request": None,
            "shipping_company": {
                "name": None,
                "label": orderitem.get("shipment", {}).get("provider", None)
            },
            "tracking_url": orderitem.get("shipment", {}).get("trackingUrl", None),
            "tracking_number": orderitem.get("shipment", {}).get("trackingNumber", None),
            "price": str(orderitem["price"]),
            "tax_rate": str(orderitem["taxRate"])
        } for orderitem in order_data["items"]]

        if orderitem_refund_status_check:
            orderitem_set_map = {str(item["id"]): item for item in orderitem_set}
            grouped_return_info = {}

            grouped_return_info = {
                order_item['orderItemId']: [
                    info for info in sorted(
                        order_item.get("returnInfo", []), key=lambda x: x['returnStatus']
                    )
                    if info.get("returnStatus") not in not_acceptable_return_statuses
                ]
                for order_item in order_items
                if (
                        order_item["status"] in acceptable_refund_statuses
                        and any(info.get("returnStatus") not in not_acceptable_return_statuses
                                for info in order_item.get("returnInfo", []))
                )
            }

            for order_item_id, return_info_list in grouped_return_info.items():
                refund_status, easy_return_code = self._get_refund_status(return_info_list)
                cancellation_requests = {
                    "id": 0,
                    "cancellation_type": {
                        "value": "refund",
                        "label": "İade"
                    },
                    "status": {
                        "value": refund_status,
                        "label": refund_status
                    },
                    "easy_return": {
                        "code": easy_return_code,
                        "shipping_company": {
                            "value": "yurtici",
                            "label": "Yurtiçi Kargo"
                        }
                    },
                    "description": "",
                    "reason": "",
                    "order_item": order_item_id
                }

                if order_item_id in orderitem_set_map:
                    orderitem_set_item = orderitem_set_map[order_item_id]
                    orderitem_set_item["active_cancellation_request"] = cancellation_requests
                    orderitem_set_item.setdefault("cancellationrequest_set", []).append(cancellation_requests)

        return orderitem_set

    def _get_parent_status(self, orderitem):
        status_counts = {'100': 0, '450': 0, '500': 0, '550': 0, '600': 0, "400": 0}
        status_labels = {
            '100': 'İptal Edildi',
            '400': 'Onaylandı',
            '450': 'Hazırlanıyor',
            '500': 'Kargolandı',
            '550': 'Teslim Edildi',
            '600': 'İade Edildi'
        }

        if not isinstance(orderitem, list):
            orderitem = [orderitem]

        for oi in orderitem:
            status_value = oi['status'].get('value')
            if status_value in status_counts:
                status_counts[status_value] += 1

        num_items = len(orderitem)
        num_remaining = num_items - status_counts['100'] - status_counts['550'] - status_counts['600']

        if status_counts['450'] >= num_items or status_counts['450'] >= 1:
            return {'value': '450', 'label': status_labels['450']}
        elif status_counts['100'] == num_items:
            return {'value': '100', 'label': status_labels['100']}
        elif status_counts['550'] == num_items or (
                status_counts['100'] + status_counts['550'] == num_items - num_remaining + status_counts['600'] and
                status_counts['450'] == num_remaining):
            return {'value': '550', 'label': status_labels['550']}
        elif status_counts['500'] == num_items:
            return {'value': '500', 'label': status_labels['500']}
        elif status_counts['600'] == num_items:
            return {'value': '600', 'label': status_labels['600']}
        elif status_counts['600'] > status_counts["100"]:
            return {'value': '600', 'label': status_labels['600']}
        elif status_counts['100'] > status_counts["600"]:
            return {'value': '100', 'label': status_labels['100']}
        elif status_counts['100'] == status_counts["600"]:
            return {'value': '100', 'label': status_labels['100']}
        elif status_counts['400'] == num_items:
            return {'value': '100', 'label': status_labels['100']}
        else:
            return None

    def _get_refund_status(self, return_info):
        sorted_data = sorted(return_info, key=lambda x: x['returnStatus'])
        last_item = sorted_data[-1]
        first_item = sorted_data[0]

        if not sorted_data:
            refund_status = ""
            easy_return_code = ""
            return refund_status, easy_return_code

        if any(item['returnStatus'] == 0 for item in sorted_data) and last_item['returnStatus'] not in (2, 635):
            refund_status = "Waiting"
            easy_return_code = first_item.get("shipmentCode", "")
        else:
            refund_status = ""
            easy_return_code = ""
        return refund_status, easy_return_code

    def _general_refund_cancel_statuses(self, order_item):
        is_cancellable = any(orderitem.get("is_cancellable", False) for orderitem in order_item)
        is_refundable = any(orderitem.get("is_refundable", False) for orderitem in order_item)
        is_cancelled = all(orderitem.get("is_cancelled", False) for orderitem in order_item)

        return is_cancellable, is_refundable, is_cancelled
