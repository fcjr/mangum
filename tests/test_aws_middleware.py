import base64
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from mangum.platforms.aws.middleware import AWSLambdaMiddleware


def test_aws_response(mock_data) -> None:
    def app(scope):
        async def asgi(receive, send):
            response = PlainTextResponse("Hello, world!")
            await response(receive, send)

        return asgi

    mock_event = mock_data.get_aws_event()
    handler = AWSLambdaMiddleware(app)
    response = handler(mock_event, {})

    assert response == {
        "statusCode": 200,
        "isBase64Encoded": False,
        "headers": {
            "content-length": "13",
            "content-type": "text/plain; charset=utf-8",
        },
        "body": "Hello, world!",
    }


def test_aws_response_with_body(mock_data) -> None:
    def app(scope):
        async def asgi(receive, send):
            request = Request(scope, receive)
            body = await request.body()
            response = PlainTextResponse(body)
            await response(receive, send)

        return asgi

    mock_event = mock_data.get_aws_event()
    handler = AWSLambdaMiddleware(app)
    response = handler(mock_event, {})

    assert response == {
        "statusCode": 200,
        "isBase64Encoded": False,
        "headers": {"content-length": "3", "content-type": "text/plain; charset=utf-8"},
        "body": "123",
    }


def test_aws_binary_response_with_body(mock_data) -> None:
    def app(scope):
        async def asgi(receive, send):
            message = await receive()
            body = message["body"]
            response = PlainTextResponse(body)
            await response(receive, send)

        return asgi

    mock_event = mock_data.get_aws_event()
    body = b"123"
    body_encoded = base64.b64encode(body)
    mock_event["body"] = body_encoded
    mock_event["isBase64Encoded"] = True
    handler = AWSLambdaMiddleware(app)
    response = handler(mock_event, {})

    assert response == {
        "statusCode": 200,
        "isBase64Encoded": True,
        "headers": {"content-length": "3", "content-type": "text/plain; charset=utf-8"},
        "body": body_encoded,
    }


def test_aws_debug(mock_data) -> None:
    def app(scope):
        async def asgi(receive, send):
            response = PlainTextResponse("Hello, world!")
            raise Exception("Error!")
            await response(receive, send)

        return asgi

    mock_event = mock_data.get_aws_event()
    handler = AWSLambdaMiddleware(app, debug=True)
    response = handler(mock_event, {})
    assert response == {
        "statusCode": 500,
        "isBase64Encoded": False,
        "headers": {},
        "body": "Error!",
    }


def test_starlette_aws_response(mock_data) -> None:

    mock_event = mock_data.get_aws_event()

    app = Starlette()

    @app.route(mock_event["path"])
    def homepage(request):
        return PlainTextResponse("Hello, world!")

    handler = AWSLambdaMiddleware(app)
    response = handler(mock_event, {})

    assert response == {
        "statusCode": 200,
        "isBase64Encoded": False,
        "headers": {
            "content-length": "13",
            "content-type": "text/plain; charset=utf-8",
        },
        "body": "Hello, world!",
    }
