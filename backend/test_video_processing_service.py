import os
import io
import subprocess
from pathlib import Path

import pytest
from backend.video_processing_service import transcode, generate_thumbnail, VideoProcessingError
from unittest import mock


@pytest.fixture
def dummy_video(tmp_path):
    vid = tmp_path / "dummy.mp4"
    vid.write_bytes(b"\x00\x00\x00\x18ftypmp42")  # minimal MP4 header
    return vid


@pytest.fixture
def mock_ffmpeg_success(monkeypatch):
    def _run(cmd, *args, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, stdout=b"", stderr=b"")
    monkeypatch.setattr(subprocess, "run", _run)


@pytest.fixture
def mock_ffmpeg_failure(monkeypatch):
    def _run(cmd, *args, **kwargs):
        raise subprocess.CalledProcessError(returncode=1, cmd=cmd)
    monkeypatch.setattr(subprocess, "run", _run)


def test_transcode_success(dummy_video, tmp_path, mock_ffmpeg_success):
    out = tmp_path / "out.mp4"
    transcode(str(dummy_video), str(out))
    assert out.exists()


def test_generate_thumbnail_success(dummy_video, tmp_path, mock_ffmpeg_success):
    out = tmp_path / "thumb.jpg"
    generate_thumbnail(str(dummy_video), 1.5, str(out))
    assert out.exists()


def test_transcode_unsupported_codec(dummy_video, tmp_path):
    with pytest.raises(ValueError):
        transcode(str(dummy_video), str(tmp_path / "out.mkv"), codec="vp9")


def test_transcode_zero_length(tmp_path):
    empty = tmp_path / "empty.mp4"
    empty.touch()
    with pytest.raises(VideoProcessingError):
        transcode(str(empty), str(tmp_path / "out.mp4"))


def test_transcode_ffmpeg_failure(dummy_video, tmp_path, mock_ffmpeg_failure):
    with pytest.raises(VideoProcessingError):
        transcode(str(dummy_video), str(tmp_path / "out.mp4"))


def test_generate_thumbnail_ffmpeg_failure(dummy_video, tmp_path, mock_ffmpeg_failure):
    with pytest.raises(VideoProcessingError):
        generate_thumbnail(str(dummy_video), 0.5, str(tmp_path / "thumb.jpg"))