from app.http.request import HTTPRequest
from app.http.response import HTTPResponse


class RequestHandler:
    """ Analyze HTTPRequest-Objects and build proper HTTPResponse-Objects """

    @staticmethod
    def handle_request(request: HTTPRequest) -> HTTPResponse:
        """
        gets a HTTPRequest-Obj, analyze it, and build a proper HTTPResponse-Obj
        """
        if request.method.upper() == "HEAD":  # just send `Headers`
            response_obj = HTTPResponse(body=b"", is_for_head_method=True)
            return response_obj
        # elif ...:
        #   handle 'routing'
        #   handle "Expect: 100-continue"
        #   handle "provide chunk body transferring properly"
        #   etc...
        else:
            body = (
                f"<br>"
                f"<h1 style='text-align: center;'>"
                f"  I'm developing my own HTTPServer... :)))\n"
                f"You requested {request.path!r}\n"
                f"</h1>"
            ).encode("utf-8")
            response = HTTPResponse(body=body, mem_type="text/html")
            return response
