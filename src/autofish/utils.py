from datetime import datetime


def print_timestamped(string):
    print(str(datetime.now()).ljust(30) + "\t" + string)


def error_msg(response):
    """Return a pretty error message from a response"""
    return (
        f"Request to {response.url} failed with status code {response.status_code}. "
        f"The response content was: '{response.text}'"
    )
