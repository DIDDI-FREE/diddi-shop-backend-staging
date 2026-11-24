from typing import Literal

DIDDI_CURRENCY: Literal["XOF"] = "XOF"


def require_xof(currency: str) -> Literal["XOF"]:
    if currency != DIDDI_CURRENCY:
        raise ValueError("DiddiFree financial contracts only support XOF")
    return DIDDI_CURRENCY
