import json
from contextlib import contextmanager
from unittest.mock import patch
import httpx

CLIENT = httpx.AsyncClient


def frame(content=None, finish=None, **extra):
    delta = {}
    if content is not None:
        delta['content'] = content
    return 'data: ' + json.dumps({
        'choices': [{'delta': delta, 'finish_reason': finish}], **extra
    }) + '\n\n'


def answer(text='Hello', finish='stop'):
    return frame(text) + frame(finish=finish) + 'data: [DONE]\n\n'


@contextmanager
def gateway(handler):
    transport = httpx.MockTransport(handler)
    with patch('src.features.operator.runtime.HERMES_API_KEY', 'test-key'), patch(
        'src.features.operator.runtime.httpx.AsyncClient',
        side_effect=lambda **kwargs: CLIENT(transport=transport, **kwargs),
    ):
        yield


def stream_response(text):
    return httpx.Response(200, text=text, headers={'content-type': 'text/event-stream'})


