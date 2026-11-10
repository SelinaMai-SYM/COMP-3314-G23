"""Downloader classification. No network."""

from experiments.v3_reproduction.resource_recovery import classify_payload


def test_html_is_not_saved_as_pdf() -> None:
    status = classify_payload(b"<html><body>access denied</body></html>", "pdf", "text/html")
    assert status == "ACCESS_DENIED_HTML"


def test_pdf_signature_is_accepted() -> None:
    assert classify_payload(b"%PDF-1.7\n", "pdf", "application/pdf") == "DOWNLOADED_VALID_FORMAT"


def test_mat_signature_is_accepted() -> None:
    assert classify_payload(b"MATLAB 5.0 MAT-file", "mat", "application/octet-stream") == "DOWNLOADED_VALID_FORMAT"
