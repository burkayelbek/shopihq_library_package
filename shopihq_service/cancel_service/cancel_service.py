import requests
from shopihq_service.settings import Settings as settings


class ShopihqCancelService(object):
    @staticmethod
    def test_request():
        response = requests.get('https://npiregistry.cms.hhs.gov/api/?version=2.1&number=1275768103')
        return response

    @staticmethod
    def _get_url_with_endpoint(endpoint):
        shopi_url = getattr(settings, 'SHOPIHQ_URL')
        return f"{shopi_url}{endpoint}"

    def get_reasons(self, request):
        path = self._get_url_with_endpoint('/Order/reasons')
        response = requests.get(url=path, params=request.query_params)
        if response.status_code == 200:
            return response
        else:
            return False

    def is_cancellable(self, order_number):
        path = self._get_url_with_endpoint(f'/Order/isCancelable/{order_number}')
        response = requests.get(url=path)
        return response
