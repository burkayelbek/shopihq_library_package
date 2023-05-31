import requests
import json
import re
from urllib.parse import urlparse, urlencode, urlunparse
from shopihq_service.utils import get_url_with_endpoint, get_order_status_mapping, check_full_name_compatibility
from shopihq_service.utils import BasicAuthUtils


class ShopihqOrderService(object):
    auth = BasicAuthUtils()

    def __init__(self, username, password):
        self.headers = {"Content-Type": "application/json",
                        "Authorization": self.auth.basic_auth(username=username, password=password)}

    def get_reasons(self, request):
        """
        Method: GET
        :param request: Ex: ?type=0&language=1
        : type=0 -> Cancel, type=1 -> Refund, language=0 -> Turkish, language=1 -> English
        :return:
        """
        data = []
        path = get_url_with_endpoint('/Order/reasons')
        website_url = request.META.get('HTTP_REFERER')
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
            f'/Order/search?customerId={user_id}&SortDesc=true&pageNumber={page_number}&pageSize=10')

        response = requests.get(url=path, params=request.query_params, headers=self.headers)

        if response.status_code != 200:
            response_error = requests.Response()
            response_error.status_code = response.status_code
            response_error._content = response
            return response_error

        response_json = json.loads(response.content.decode())
        count = response_json.get("data", {})["totalCount"]
        parsed_json = response_json.get("data", {}).get("results", [])

        for res in parsed_json:
            orderitem_set = self._fill_orderitem_set(order_data=res),
            parent_status = self._get_parent_status(orderitem=orderitem_set[0])
            first_name, last_name = check_full_name_compatibility(
                full_name=res["items"][0].get("deliveryAddress", {})["fullName"])
            response_data = {
                "id": res["orderId"],
                "status": parent_status,
                "currency": {
                    "value": "try",
                    "label": "TL",
                },
                "orderitem_set": orderitem_set[0],
                "is_cancelled": None,
                "is_cancellable": None,
                "is_refundable": None,
                "shipping_address": {
                    "pk": res["items"][0].get("deliveryAddress", {})["id"],
                    "email": res["items"][0].get("deliveryAddress", {})["email"],
                    "phone_number": res["items"][0].get("deliveryAddress", {})["phone"],
                    "first_name": first_name,
                    "last_name": last_name,
                    "country": {
                        "name": res["items"][0].get("deliveryAddress", {}).get("country", "")
                    },
                    "city": {
                        "name": res["items"][0].get("deliveryAddress", {}).get("city", "").upper()
                    },
                    "line": res["items"][0].get("deliveryAddress", {})["details"],
                    "title": None,
                    "township": {
                        "name": res["items"][0].get("deliveryAddress", {}).get("town", "")
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
                    "first_name": first_name,
                    "last_name": last_name,
                    "country": {
                        "name": res.get("billingAddress", {}).get("country", "")
                    },
                    "city": {
                        "name": res.get("billingAddress", {}).get("city", "").upper()
                    },
                    "line": res.get("billingAddress", {})["details"],
                    "title": None,
                    "township": {
                        "name": res.get("billingAddress", {}).get("town", "")
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
                "tracking_url": res["items"][0].get("shipment", {}).get("trackingLink", None),
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
            response_error = requests.Response()
            response_error.status_code = response.status_code
            response_error._content = response
            return response_error
        response_json = json.loads(response.content.decode())
        parsed_json = response_json.get("data", {}).get("results", [])
        orderitem_set = self._fill_orderitem_set(order_data=parsed_json)
        parent_status = self._get_parent_status(orderitem=orderitem_set)
        first_name, last_name = check_full_name_compatibility(full_name=parsed_json[0]["items"][0].get("deliveryAddress", {})["fullName"])


        for res in parsed_json:
            response_data = {
                "id": res["orderId"],
                "status": parent_status,
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
                    "first_name": first_name,
                    "last_name": last_name,
                    "country": {
                        "name": res["items"][0].get("deliveryAddress", {}).get("country", "")
                    },
                    "city": {
                        "name": res["items"][0].get("deliveryAddress", {}).get("city", "").upper()
                    },
                    "line": res["items"][0].get("deliveryAddress", {})["details"],
                    "title": None,
                    "township": {
                        "name": res["items"][0].get("deliveryAddress", {}).get("town", "")
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
                    "first_name": first_name,
                    "last_name": last_name,
                    "country": {
                        "name": res.get("billingAddress", {}).get("country", "")
                    },
                    "city": {
                        "name": res.get("billingAddress", {}).get("city", "").upper()
                    },
                    "line": res.get("billingAddress", {})["details"],
                    "title": None,
                    "township": {
                        "name": res.get("billingAddress", {}).get("town", "")
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
                "tracking_url": res["items"][0].get("shipment", {}).get("trackingLink", None),
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
        order_data = order_data[0]
        order_number = order_data.get("orderId", "")
        orderitem_refund_status_check = any(orderitem["status"] == 540 and len(orderitem["returnInfo"]) >= 1
                                            and any(return_info.get("returnStatus") != 2
                                                    for return_info in orderitem.get("returnInfo", []))
                                            for orderitem in order_data["items"])

        cancellation_requests = {}
        orderitem_set = [{
            "id": orderitem["orderItemId"],
            "status": get_order_status_mapping(orderitem),
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
                "absolute_url": "#",
                "attributes": {
                    "integration_sap_COLOR": orderitem.get("productColor", None),
                    "integration_sap_SIZE1": orderitem.get("productSize", None),
                    "integration_sap_BRAND": orderitem.get("productBrand", None),
                },
                "attributes_kwargs": {}
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
            "tracking_url": orderitem.get("shipment", {}).get("trackingLink", None),
            "tracking_number": orderitem.get("invoiceNumber", None),
            "price": orderitem["price"],
            "tax_rate": orderitem["taxRate"]
        } for orderitem in order_data["items"]]

        if orderitem_refund_status_check:
            orderitem_set_map = {item["id"]: item for item in orderitem_set}
            grouped_return_info = {}

            grouped_return_info = {
                roi['orderItemId']: [info for info in roi.get("returnInfo", []) if info.get("returnStatus") != 2]
                for roi in order_data['items']
                if roi["status"] == 540 and any(info.get("returnStatus") != 2 for info in roi.get("returnInfo", []))
            }

            for order_item_id, return_info_list in grouped_return_info.items():
                refund_status, easy_return_code = self._get_refund_status(return_info_list)
                cancellation_requests = {
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
        if not isinstance(orderitem, list):
            orderitem = [orderitem]
        num_items = len(orderitem)
        num_canceled = sum(1 for oi in orderitem if oi['status'].get('value') == '100')
        num_delivered = sum(1 for oi in orderitem if oi['status'].get('value') == '550')
        num_preparing = sum(1 for oi in orderitem if oi['status'].get('value') == '450')
        num_shipped = sum(1 for oi in orderitem if oi['status'].get('value') == '500')
        num_refunded = sum(1 for oi in orderitem if oi['status'].get('value') == '600')
        num_remaining = num_items - num_canceled - num_delivered - num_refunded

        if num_preparing >= (num_canceled + num_delivered + num_refunded) and num_preparing >= 1:
            return {'value': '450', 'label': 'Hazırlanıyor'}
        elif num_canceled == num_items:
            return {'value': '100', 'label': 'İptal Edildi'}
        elif num_delivered == num_items or (
                num_canceled + num_delivered == num_items - num_remaining + num_refunded and num_preparing == num_remaining):
            return {'value': '550', 'label': 'Teslim Edildi'}
        elif num_shipped == num_items:
            return {'value': '500', 'label': 'Kargolandı'}
        elif num_refunded == num_items:
            return {'value': '600', 'label': 'İade Edildi'}
        else:
            return None

    def _get_refund_status(self, return_info):
        sorted_data = sorted(return_info, key=lambda x: x['returnStatus'])
        last_item = sorted_data[-1]

        if last_item.get("returnStatus") == 2:
            refund_status = ""
            easy_return_code = ""
        elif last_item.get("returnStatus") == 635:
            refund_status = "Completed"
            easy_return_code = last_item.get("shipmentCode", "")
        else:
            refund_status = "Waiting"
            easy_return_code = last_item.get("shipmentCode", "")
        return refund_status, easy_return_code
