import random
import string
import requests
from scrapy.utils.response import response_status_message
from scrapy.downloadermiddlewares.retry import RetryMiddleware, get_retry_request


class BaiduAOIMiddleware(RetryMiddleware):
    def get_proxy(self) -> str:
        """
        proxy pool is built with reference to https://github.com/jhao104/proxy_pool
        """
        proxy = requests.get('http://127.0.0.1:5000/get/').json()
        return f'http://{proxy["proxy"]}'

    def delete_proxy(self, proxy) -> None:
        requests.get(f'http://127.0.0.1:5000/delete/?proxy={proxy}')

    def get_cookie(self) -> str:
        """
        It is observed that `BAIDUID` cookie value
        is made up of 32 random numbers and letters.
        """
        def random_32_string():
            return ''.join(random.choice(string.ascii_uppercase[:6] + string.digits)
                           for _ in range(32))
        bd_id = random_32_string()
        return f'{bd_id}:FG=1'

    def alter_proxy_and_cookie(self, request):
        request.cookies['BAIDUID'] = self.get_cookie()
        if request.meta.get('proxy_enabled'):
            self.delete_proxy(request.meta['proxy'])
            request.meta['proxy'] = self.get_proxy()
        return request

    def process_request(self, request, spider):
        request.headers['Connection'] = 'close'
        request.meta['dont_redirect'] = True
        request.meta['download_timeout'] = 15
        request.cookies['BAIDUID'] = self.get_cookie()
        if request.meta.get('proxy_enabled'):
            request.meta['proxy'] = self.get_proxy()

    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response
        if response.status in [500, 502, 503, 504, 522, 524, 408, 403, 400, 302, 301]:
            request = self.alter_proxy_and_cookie(request)
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
        return response

    def process_exception(self, request, exception, spider):
        if (
            isinstance(exception, self.EXCEPTIONS_TO_RETRY)
            and not request.meta.get('dont_retry', False)
        ):
            request = self.alter_proxy_and_cookie(request)
            return self._retry(request, exception, spider)

    def _retry(self, request, reason, spider):
        max_retry_times = request.meta.get('max_retry_times', self.max_retry_times)
        priority_adjust = request.meta.get('priority_adjust', self.priority_adjust)
        retry_response = get_retry_request(
            request,
            reason=reason,
            spider=spider,
            max_retry_times=max_retry_times,
            priority_adjust=priority_adjust,
        )
        if request.meta.get('retry_times') >= max_retry_times and retry_response is None:
            raise Exception('Retry times exceeded')
