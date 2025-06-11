#!/usr/bin/env python3
"""YouTube 요약 API 테스트"""
import requests

import os
JWT_TOKEN = os.getenv("JWT_TOKEN", "your-jwt-token")


def test_youtube_summary():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    resp = requests.post(
        "http://localhost:8000/api/media/youtube/summary",
        json={"url": url},
        headers={"Authorization": f"Bearer {JWT_TOKEN}"},
        timeout=30,
    )
    print("Status:", resp.status_code)
    if resp.status_code == 200:
        data = resp.json()
        print("Summary length:", len(data.get("summary", "")))
    else:
        print(resp.text)

if __name__ == "__main__":
    test_youtube_summary()
