import requests

class Error(Exception):
    """Base class for other exceptions"""
    pass

class NoCustomDomainsExistError(Error):
    """Raised when there are no custom domains to select from on Rebrandly account"""
    pass

class AmbiguousCustomDomainError(Error):
    """Raised when unable to auto-detect a custom domain on Rebrandly account"""
    pass

class Rebrandly(object):
    api_key = ''
    base_uri = 'https://api.rebrandly.com/v1'
    domains = []
    default_domain = None

    def __init__(self, api_key):
        self.api_key = api_key
        self._fetch_domains()

    def _build_url(self, path):
        return self.base_uri + path

    def _fetch_domains(self):
        r = self.get('/domains')
        self.domains = r.json()

    def get(self, path, data={}):
        if self.default_domain:
            data.update({})
        url = self._build_url(path)
        headers = { 'apikey': self.api_key }
        r = requests.get(url,
                         data,
                         headers=headers)

        if r.status_code != requests.codes.ok:
            raise

        return r

    def get_custom_domains(self):
        # Ignore service shortlink domains like rebrand.ly itself.
        my_domains = [d for d in self.domains if d['type'].lower() != 'service']
        return my_domains

    def set_domain_by_name(self, domain_name):
        my_domain = [d for d in self.domains if d['fullName'] == domain_name]
        if my_domain:
            return my_domain.pop()

        return None

    def autodetect_domain(self):
        my_domains = self.get_custom_domains()
        if len(my_domains) > 1:
            # TODO: Echo domains.
            raise AmbiguousCustomDomainError
        elif not my_domains:
            raise NoCustomDomainsExistError
        else:
            # Found the domain, and set.
            self.default_domain = my_domains.pop()
