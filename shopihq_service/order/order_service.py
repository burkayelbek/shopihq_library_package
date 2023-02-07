import requests
import uuid
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
        parsed_json = response_json_cancel.get('data').get('reasonList') + response_json_refund.get('data').get(
            'reasonList')
        for index, res in enumerate(parsed_json, start=1):
            response_data = {
                "id": res['reasonId'],
                "cancellation_type": "cancel" if res.get("reasonId") not in [d["id"] for d in
                                                                             data] and res in response_json_cancel.get(
                    'data').get('reasonList') else "refund",
                "subject": res['reason'],
                "extra_information_needed": True if res.get("reasonId") == -1 else None,
                "order": index,

            }
            data.append(response_data)
        results = {"count": data.__len__(), "results": data}
        response = requests.Response()
        response.status_code = 200
        response._content = json.dumps(results).encode()
        return response

    def order_search(self, request):
        """
        :param request:
        :return:
        """
        path = get_url_with_endpoint('/Order/search')
        response = requests.get(url=path, params=request.query_params)
        return response
