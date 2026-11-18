"""Shared contracts for adapters; no vendor assets are shipped."""
class PatchError(ValueError):
    pass

def validate_video_budget(value):
    if type(value) is not int or (value != 0 and not 16 <= value <= 256):
        raise PatchError("video_buffer_mib must be 0 (platform default) or 16..256")
    return value
