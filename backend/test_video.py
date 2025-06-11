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
