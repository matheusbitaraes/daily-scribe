import pytest
from src.components.summarizer import Summarizer

class DummyConfig:
    api_key = "dummy"

def make_summarizer():
    return Summarizer(DummyConfig())

def test_extract_wait_time_retry_delay():
    s = make_summarizer()
    msg = '... retry_delay { seconds: 25 } ...'
    assert s._extract_wait_time(msg) == 25

def test_extract_wait_time_retry_delay_whitespace():
    s = make_summarizer()
    msg = '... retry_delay {\n  seconds: 42\n} ...'
    assert s._extract_wait_time(msg) == 42

def test_extract_wait_time_retry_after():
    s = make_summarizer()
    msg = 'Please retry after 17 seconds.'
    assert s._extract_wait_time(msg) == 17

def test_extract_wait_time_wait_seconds():
    s = make_summarizer()
    msg = 'You must wait 33 seconds before retrying.'
    assert s._extract_wait_time(msg) == 33

def test_extract_wait_time_none():
    s = make_summarizer()
    msg = 'No wait time info here.'
    assert s._extract_wait_time(msg) is None
