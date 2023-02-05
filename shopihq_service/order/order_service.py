import requests
import uuid
import json
import re
from shopihq_service.utils import get_url_with_endpoint


class ShopihqOrderService(object):
    def __init__(self):
        self.headers = {"Content-Type": "application/json"}

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
        params = {'type': 0, 'language': language}
        response = requests.get(url=path, params=params)
        if response.status_code != 200:
            raise Exception("Error: API returned status code {}".format(response.status_code))
        response_json = json.loads(response.content.decode())
        parsed_json = response_json.get('data').get('reasonList')
        for index, res in enumerate(parsed_json, start=1):
            response_data = {
                "cancellation_type": "cancel",
                "created_date": None,
                "modified_date": None,
                "extra_information_needed": None,
                "id": res['reasonId'],
                "is_active": True,
                "order": index,
                "subject": res['reason'],
                "translations": None,
                "uuid": str(uuid.uuid4())
            }
            data.append(response_data)
        results = {"results": data}
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
