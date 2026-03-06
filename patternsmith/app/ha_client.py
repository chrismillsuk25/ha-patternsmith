import requests


class HomeAssistantClient(object):
    def __init__(self, base_url, token, timeout=10):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": "Bearer {0}".format(token),
            "Content-Type": "application/json",
        })
        self.timeout = timeout

    def get_states(self):
        url = "{0}/states".format(self.base_url)
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def get_events(self):
        url = "{0}/events".format(self.base_url)
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def get_entity_state(self, entity_id):
        url = "{0}/states/{1}".format(self.base_url, entity_id)
        resp = self.session.get(url, timeout=self.timeout)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
