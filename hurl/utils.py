
import requests
from time import sleep

def get_hilltop_response(
    url, timeout=60
):
    ret_obj=None

    timeout = 60
    counter = [10, 20, 30, None]
    success = False
    for c in counter:
        try:
            with requests.get(url, timeout=timeout) as req:
                req.raise_for_status()
                if req.status_code == 200:
                    success = True
                    ret_obj = req.content
        except Exception as err:
            print(str(err))

            if c is None:
                raise err
            print("Trying again in " + str(c) + " seconds.")
            sleep(c)
            return success, err
    return success, ret_obj
