import json
from insite_plugin import InsitePlugin
from ipg_nat_6 import IPGNAT6


class Plugin(InsitePlugin):
    def can_group(self):
        return False

    def fetch(self, hosts):

        host = hosts[-1]

        try:

            self.ipx

        except Exception:

            params = {"address": host}

            self.nat6 = IPGNAT6(**params)

        documents = []

        for _, params in self.nat6.collect.items():

            document = {"fields": params, "host": host, "name": "core"}

            documents.append(document)

        return json.dumps(documents)
