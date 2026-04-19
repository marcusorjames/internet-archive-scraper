import os
from unittest.mock import MagicMock, patch

import pytest

import scraper
from scraper import clean_staging, download_from_ia, is_remote, parse_ia_url, select_files, sync_to_dest

NIRVANA_ID = "ajc03187_nirvana-1989-09-30"
NIRVANA_FILE = "Nirvana1989-09-30t01.flac"
NIRVANA_URL = f"https://archive.org/details/{NIRVANA_ID}/{NIRVANA_FILE}"
NIRVANA_ALBUM_URL = f"https://archive.org/details/{NIRVANA_ID}"
TEST_STAGING_DIR = "/tmp/test-ia-staging"
TEST_OUTPUT_DIR = "remotehost:/path/to/media"

MOCK_FILES = [
    {"name": "track01.flac"},
    {"name": "track02.flac"},
    {"name": "track01.mp3"},
    {"name": "track02.mp3"},
    {"name": "cover.jpg"},
    {"name": "photo.png"},
    {"name": "item_meta.xml"},
]


def mock_item(files=MOCK_FILES):
    item = MagicMock()
    item.files = files
    return item


class TestParseIaUrl:
    def test_url_with_file(self):
        identifier, filename = parse_ia_url(NIRVANA_URL)
        assert identifier == NIRVANA_ID
        assert filename == NIRVANA_FILE

    def test_url_without_file(self):
        identifier, filename = parse_ia_url(NIRVANA_ALBUM_URL)
        assert identifier == NIRVANA_ID
        assert filename is None

    def test_url_with_trailing_slash(self):
        identifier, filename = parse_ia_url(NIRVANA_ALBUM_URL + "/")
        assert identifier == NIRVANA_ID
        assert filename is None

    def test_non_ia_url_raises(self):
        with pytest.raises(ValueError, match="Not an Internet Archive URL"):
            parse_ia_url("https://example.com/something")

    def test_ia_url_without_details_raises(self):
        with pytest.raises(ValueError, match="Cannot parse"):
            parse_ia_url("https://archive.org/search?q=nirvana")


class TestIsRemote:
    def test_ssh_path_is_remote(self):
        assert is_remote("remotehost:/path/to/media") is True

    def test_local_path_is_not_remote(self):
        assert is_remote("/local/path/to/media") is False


class TestSelectFiles:
    @patch("scraper.internetarchive.get_item")
    def test_flac_returns_flac_and_thumbs(self, mock_get_item):
        mock_get_item.return_value = mock_item()
        result = select_files(NIRVANA_ID, "flac")
        assert result == ["track01.flac", "track02.flac", "cover.jpg", "photo.png"]

    @patch("scraper.internetarchive.get_item")
    def test_flac_no_thumbs(self, mock_get_item):
        mock_get_item.return_value = mock_item()
        result = select_files(NIRVANA_ID, "flac", thumbs=False)
        assert result == ["track01.flac", "track02.flac"]

    @patch("scraper.internetarchive.get_item")
    def test_mp3_returns_mp3_and_thumbs(self, mock_get_item):
        mock_get_item.return_value = mock_item()
        result = select_files(NIRVANA_ID, "mp3")
        assert result == ["track01.mp3", "track02.mp3", "cover.jpg", "photo.png"]

    @patch("scraper.internetarchive.get_item")
    def test_mp3_no_thumbs(self, mock_get_item):
        mock_get_item.return_value = mock_item()
        result = select_files(NIRVANA_ID, "mp3", thumbs=False)
        assert result == ["track01.mp3", "track02.mp3"]

    @patch("scraper.internetarchive.get_item")
    def test_flac_falls_back_to_mp3_when_no_flac(self, mock_get_item):
        files = [{"name": "track01.mp3"}, {"name": "cover.jpg"}]
        mock_get_item.return_value = mock_item(files)
        result = select_files(NIRVANA_ID, "flac", thumbs=False)
        assert result == ["track01.mp3"]

    def test_all_returns_none(self):
        assert select_files(NIRVANA_ID, "all") is None


class TestSyncToDest:
    @patch("scraper.subprocess.run")
    def test_rsync_command(self, mock_run):
        sync_to_dest("/tmp/ia/my-item", TEST_OUTPUT_DIR)
        mock_run.assert_called_once_with(
            ["rsync", "-avz", "--no-times", "--no-perms", "--inplace", "--progress",
             "/tmp/ia/my-item/", f"{TEST_OUTPUT_DIR}/my-item/"],
            check=True,
        )


class TestCleanStaging:
    @patch("scraper.STAGING_DIR", TEST_STAGING_DIR)
    @patch("scraper.shutil.rmtree")
    @patch("scraper.os.path.exists", return_value=True)
    def test_clears_existing_staging_dir(self, mock_exists, mock_rmtree):
        clean_staging()
        mock_rmtree.assert_called_once_with(TEST_STAGING_DIR)

    @patch("scraper.STAGING_DIR", TEST_STAGING_DIR)
    @patch("scraper.shutil.rmtree")
    @patch("scraper.os.path.exists", return_value=False)
    def test_no_op_when_staging_dir_missing(self, mock_exists, mock_rmtree):
        clean_staging()
        mock_rmtree.assert_not_called()


class TestDownloadFromIa:
    @patch("scraper.STAGING_DIR", TEST_STAGING_DIR)
    @patch("scraper.OUTPUT_DIR", TEST_OUTPUT_DIR)
    @patch("scraper.shutil.rmtree")
    @patch("scraper.sync_to_dest")
    @patch("scraper.select_files", return_value=["track01.flac", "cover.jpg"])
    @patch("scraper.internetarchive.download")
    def test_uses_select_files_when_no_filename(self, mock_download, mock_select, mock_sync, mock_rmtree):
        download_from_ia(NIRVANA_ID, format_pref="flac", thumbs=True)
        mock_select.assert_called_once_with(NIRVANA_ID, "flac", True)
        mock_download.assert_called_once_with(
            NIRVANA_ID,
            files=["track01.flac", "cover.jpg"],
            destdir=TEST_STAGING_DIR,
            verbose=True,
        )

    @patch("scraper.STAGING_DIR", TEST_STAGING_DIR)
    @patch("scraper.OUTPUT_DIR", TEST_OUTPUT_DIR)
    @patch("scraper.shutil.rmtree")
    @patch("scraper.sync_to_dest")
    @patch("scraper.select_files")
    @patch("scraper.internetarchive.download")
    def test_ignores_format_when_filename_given(self, mock_download, mock_select, mock_sync, mock_rmtree):
        download_from_ia(NIRVANA_ID, filename=NIRVANA_FILE, format_pref="mp3")
        mock_select.assert_not_called()
        mock_download.assert_called_once_with(
            NIRVANA_ID, files=[NIRVANA_FILE], destdir=TEST_STAGING_DIR, verbose=True,
        )

    @patch("scraper.STAGING_DIR", TEST_STAGING_DIR)
    @patch("scraper.OUTPUT_DIR", TEST_OUTPUT_DIR)
    @patch("scraper.shutil.rmtree")
    @patch("scraper.sync_to_dest")
    @patch("scraper.select_files", return_value=None)
    @patch("scraper.internetarchive.download")
    def test_all_format_passes_none_files(self, mock_download, mock_select, mock_sync, mock_rmtree):
        download_from_ia(NIRVANA_ID, format_pref="all")
        mock_download.assert_called_once_with(
            NIRVANA_ID, files=None, destdir=TEST_STAGING_DIR, verbose=True,
        )

    @patch("scraper.STAGING_DIR", TEST_STAGING_DIR)
    @patch("scraper.OUTPUT_DIR", TEST_OUTPUT_DIR)
    @patch("scraper.shutil.rmtree")
    @patch("scraper.sync_to_dest")
    @patch("scraper.select_files", return_value=["track01.flac"])
    @patch("scraper.internetarchive.download")
    def test_staging_not_cleaned_up_on_failure(self, mock_download, mock_select, mock_sync, mock_rmtree):
        mock_download.side_effect = RuntimeError("network error")
        with pytest.raises(RuntimeError):
            download_from_ia(NIRVANA_ID)
        mock_rmtree.assert_not_called()
