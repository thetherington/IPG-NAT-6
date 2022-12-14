import copy
import json

import requests


class IPGNAT6:
    def __init__(self, **kwargs):
        self.address = None

        self.wan_port_status = {
            "id": "300.<replace>.0@i",
            "type": "integer",
            "name": "s_wan_port_status",
        }
        self.lan_port_status = {
            "id": "300.<replace>.1@i",
            "type": "integer",
            "name": "s_lan_port_status",
        }
        self.wan_rx_rate = {
            "id": "302.<replace>.0@i",
            "type": "integer",
            "name": "l_wan_rx_rate",
        }
        self.wan_tx_rate = {
            "id": "305.<replace>.0@i",
            "type": "integer",
            "name": "l_wan_tx_rate",
        }
        self.lan_rx_rate = {
            "id": "302.<replace>.1@i",
            "type": "integer",
            "name": "l_lan_rx_rate",
        }
        self.lan_tx_rate = {
            "id": "305.<replace>.1@i",
            "type": "integer",
            "name": "l_lan_tx_rate",
        }

        self.parameters = []

        self.fetch = self.fetch_nat6

        for key, value in kwargs.items():

            if "address" in key and value:
                self.address = value

        for core in [1, 2, 3, 4, 5, 6]:

            for param in [
                self.wan_port_status,
                self.lan_port_status,
                self.wan_rx_rate,
                self.wan_tx_rate,
                self.lan_rx_rate,
                self.lan_tx_rate,
            ]:

                template_copy = copy.deepcopy(param)
                template_copy["id"] = template_copy["id"].replace(
                    "<replace>", str(core - 1)
                )

                self.parameters.append(template_copy)

        # print(json.dumps(self.parameters, indent=1))

    def fetch_nat6(self, parameters):

        try:

            with requests.Session() as session:

                ## get the session ID from accessing the login.php site
                resp = session.get(
                    "http://%s/login.php" % self.address,
                    verify=False,
                    timeout=30.0,
                )

                session_id = resp.headers["Set-Cookie"].split(";")[0]

                payload = {
                    "jsonrpc": "2.0",
                    "method": "get",
                    "params": {"parameters": parameters},
                    "id": 1,
                }

                url = "http://%s/cgi-bin/cfgjsonrpc" % (self.address)

                headers = {
                    "content_type": "application/json",
                    "Cookie": session_id + "; webeasy-loggedin=true",
                }

                response = session.post(
                    url,
                    headers=headers,
                    data=json.dumps(payload),
                    verify=False,
                    timeout=30.0,
                )

                return json.loads(response.text)

        except Exception as error:
            print(error)
            return error

    @property
    def collect(self):

        results = self.fetch(self.parameters)

        cores = {}

        for result in results["result"]["parameters"]:

            # seperate "240.1.1@i" to "[240.1.1, @i]"
            _id = result["id"].split("@")[0]

            # split the instance and type notation, then convert the
            # instance back to base 1 for port number
            _core_instance = _id.split(".")[1]
            _core_instance = int(_core_instance) + 1

            key = result["name"]

            if "port_status" in key:

                lookup = {0: "DOWN", 1: "UP"}
                result["value"] = lookup[result["value"]]

            if "rate" in key:
                result["value"] = result["value"] * 1000

            # create port key and object if doesn't exist, otherwise update existing key/object
            if _core_instance not in cores.keys():

                cores.update(
                    {
                        _core_instance: {
                            key: result["value"],
                            "as_id": [result["id"]],
                            "i_core": _core_instance,
                        }
                    }
                )

            else:

                cores[_core_instance].update({key: result["value"]})
                cores[_core_instance]["as_id"].append(result["id"])

        return cores


def main():

    params = {"address": "127.48.70.253"}

    nat6 = IPGNAT6(**params)

    for _, items in nat6.collect.items():
        print(json.dumps(items, indent=1))


if __name__ == "__main__":
    main()
