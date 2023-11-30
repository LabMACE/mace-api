from fastapi import HTTPException
import base64


def decode_base64(
    value: str,
    allowed_types: list = [],
) -> bytes:
    """Decode base64 string to csv bytes"""
    # Split the string using the comma as a delimiter

    data_parts = value.split(",")
    if data_parts[0] not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type.",
        )

    return base64.b64decode(data_parts[1])
