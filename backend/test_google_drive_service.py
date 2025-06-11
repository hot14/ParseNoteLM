"""
Tests use pytest with pytest-mock for mocking googleapiclient. No new dependencies introduced.
"""
import pytest
import googleapiclient.discovery
from googleapiclient.errors import HttpError
from unittest.mock import Mock
from backend.google_drive_service import upload_file, download_file, create_folder

@pytest.fixture(autouse=True)
def mock_drive_service(monkeypatch):
    mock_service = Mock()
    files = mock_service.files.return_value
    # Default behaviors: create returns a dummy ID, get_media returns empty bytes
    files.create.return_value.execute.return_value = {"id": "123"}
    files.get_media.return_value.execute.return_value = b""
    # Patch the discovery.build call to return our mock
    monkeypatch.setattr(googleapiclient.discovery, "build", lambda *args, **kwargs: mock_service)
    return mock_service

def test_upload_success(mock_drive_service, tmp_path):
    local_file = tmp_path / "foo.txt"
    local_file.write_text("hello")
    mock_drive_service.files.return_value.create.return_value.execute.return_value = {"id": "123"}
    file_id = upload_file(str(local_file))
    assert file_id == "123"
    mock_drive_service.files.return_value.create.assert_called_once()

def test_upload_quota_exceeded(mock_drive_service, tmp_path):
    local_file = tmp_path / "foo.txt"
    local_file.write_text("hello")
    error = HttpError(resp=Mock(status=403), content=b"Quota Exceeded")
    mock_drive_service.files.return_value.create.return_value.execute.side_effect = error
    with pytest.raises(HttpError):
        upload_file(str(local_file))

def test_download_success(mock_drive_service):
    mock_drive_service.files.return_value.get_media.return_value.execute.return_value = b"data"
    data = download_file("123")
    assert data == b"data"
    mock_drive_service.files.return_value.get_media.assert_called_once_with(fileId="123")

def test_download_not_found(mock_drive_service):
    error = HttpError(resp=Mock(status=404), content=b"Not Found")
    mock_drive_service.files.return_value.get_media.return_value.execute.side_effect = error
    with pytest.raises(HttpError):
        download_file("nonexistent")

def test_create_folder_success(mock_drive_service):
    mock_drive_service.files.return_value.create.return_value.execute.return_value = {"id": "folder123"}
    folder_id = create_folder("MyFolder")
    assert folder_id == "folder123"
    mock_drive_service.files.return_value.create.assert_called_once_with(
        body={"name": "MyFolder", "mimeType": "application/vnd.google-apps.folder"},
        fields="id"
    )

def test_create_folder_http_error(mock_drive_service):
    error = HttpError(resp=Mock(status=500), content=b"Server Error")
    mock_drive_service.files.return_value.create.return_value.execute.side_effect = error
    with pytest.raises(HttpError):
        create_folder("MyFolder")