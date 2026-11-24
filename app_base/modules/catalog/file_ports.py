from typing import Protocol


class ProductFilePort(Protocol):
    async def metadata(self, file_id: str) -> dict: ...

    async def public_or_signed_url(self, file_id: str) -> str: ...
