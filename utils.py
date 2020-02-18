from datetime import datetime
from json import JSONDecodeError


def print_timestamped(string):
    print(str(datetime.now()).ljust(30) + "\t" + string)


def get_JSON(response):
    try:
        data = response.json()
    except JSONDecodeError as e:
        error(request)
    return data


def error_msg(response):
    """Return a pretty error message from a response"""
    return (
        f"Request to {response.url} failed with status code {response.status_code}. "
        f"The response content was: '{response.text}'"
    )
