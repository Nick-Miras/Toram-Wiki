def remove_empty_keys(dct: dict) -> dict:
    return {k: v for k, v in dct.items() if v is not None}
