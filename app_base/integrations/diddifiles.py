from app_base.integrations.base import ServiceAdapter


class DiddiFilesAdapter(ServiceAdapter):
    async def metadata(self, file_id: str) -> dict:
        response = await self.request("GET", f"/v1/files/{file_id}")
        response.raise_for_status()
        return response.json()

    async def public_or_signed_url(self, file_id: str) -> str:
        response = await self.request("GET", f"/v1/files/{file_id}/public-url")
        response.raise_for_status()
        return response.json()["url"]
