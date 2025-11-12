""" ... """

STATUS_MESSAGES = {
    # 1** : Informational
    100: "Continue",
    # 2** : Successful
    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",
    # 3** : Redirection
    301: "Moved Permanently",
    307: "Temporary Redirect",
    308: "Permanent Redirect",
    # 4** : Client Error
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    411: "Length Required",
    413: "Content Too Large",
    429: "Too Many Requests",
    # 5** : Server Error
    500: "Internal Server Error",
}
