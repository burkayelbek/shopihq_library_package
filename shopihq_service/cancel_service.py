import requests


class ShopihqCancelService:

    @staticmethod
    def test_request():
        result = requests.get('https://npiregistry.cms.hhs.gov/api/?version=2.1&number=1275768103')
        return result
