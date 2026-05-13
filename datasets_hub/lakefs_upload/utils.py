import base64
import binascii


def content_type_for_file_type(file_type: str) -> str:
    return {
        ".csv": "text/csv",
        ".parquet": "application/octet-stream",
    }.get(file_type, "application/octet-stream")


def extract_etag_from_response(headers) -> str:
    # prefer Content-MD5 if exists
    content_md5 = headers.get("Content-MD5")
    if content_md5 is not None and len(content_md5) > 0:
        try:  # decode base64, return as hex
            decode_md5 = base64.b64decode(content_md5)
            return binascii.hexlify(decode_md5).decode("utf-8")
        except binascii.Error:
            pass

    # fallback to ETag
    etag = headers.get("ETag", "").strip(' "')
    return etag