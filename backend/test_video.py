import io
from fastapi.testclient import TestClient
import sys, os
sys.path.append(os.path.dirname(__file__))
from main import app

client = TestClient(app)

def test_video_summary_endpoint():
    # 1초짜리 무음 wav 파일 생성
    import wave
    with io.BytesIO() as buf:
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(b'\x00\x00'*16000)
        buf.seek(0)
        files = {'file': ('test.wav', buf.read(), 'audio/wav')}
    response = client.post('/api/videos/summary', files=files)
    assert response.status_code == 200
    data = response.json()
    assert 'transcript' in data
    assert 'summary' in data

import pytest

@pytest.fixture(scope="module")
def test_client():
    return TestClient(app)

@pytest.mark.parametrize(
    "payload, expected_status",
    [
        ({}, 422),  # No file
        ({"file": ("bad.txt", b"not audio", "text/plain")}, 415),  # wrong type
    ],
)
def test_video_summary_invalid_inputs(test_client, payload, expected_status):
    resp = test_client.post("/api/videos/summary", files=payload)
    assert resp.status_code == expected_status

def test_video_summary_empty_audio(test_client):
    import wave
    with io.BytesIO() as buf:
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(b"")   # no frames
        buf.seek(0)
        files = {"file": ("empty.wav", buf.read(), "audio/wav")}
    resp = test_client.post("/api/videos/summary", files=files)
    assert resp.status_code == 400

def test_video_summary_alt_sample_rate(test_client):
    import wave
    with io.BytesIO() as buf:
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(8000)
            wf.writeframes(b"\x00\x00" * 8000)
        buf.seek(0)
        files = {"file": ("alt.wav", buf.read(), "audio/wav")}
    resp = test_client.post("/api/videos/summary", files=files)
    assert resp.status_code == 200
    j = resp.json()
    assert set(j.keys()) == {"transcript", "summary"}
    assert isinstance(j["transcript"], str)
    assert isinstance(j["summary"], str)

def test_video_summary_large_file(test_client, monkeypatch):
    # patch any heavy processing to skip real work
    monkeypatch.setattr("main.speech_to_text", lambda *args, **kwargs: "mock transcript")
    import wave
    with io.BytesIO() as buf:
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(b"\x00\x00" * 16000 * 10)  # 10 seconds
        buf.seek(0)
        files = {"file": ("long.wav", buf.read(), "audio/wav")}
    resp = test_client.post("/api/videos/summary", files=files)
    assert resp.status_code == 200