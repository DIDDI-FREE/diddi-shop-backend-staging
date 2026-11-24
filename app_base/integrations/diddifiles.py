from app_base.integrations.base import ServiceAdapter


class DiddiFilesAdapter(ServiceAdapter):
    async def create_upload_session(self, payload: dict) -> dict:
        response = await self.request("POST", "/v1/files/upload-session", json=payload)
        response.raise_for_status()
        return response.json()

    async def confirm_upload(self, file_id: str) -> dict:
        response = await self.request("POST", f"/v1/files/{file_id}/confirm")
        response.raise_for_status()
        return response.json()

    async def metadata(self, file_id: str) -> dict:
        response = await self.request("GET", f"/v1/files/{file_id}")
        response.raise_for_status()
        return response.json()

    async def download_url(self, file_id: str) -> str:
        response = await self.request("POST", f"/v1/files/{file_id}/download-url")
        response.raise_for_status()
        return response.json()["download_url"]

    async def public_or_signed_url(self, file_id: str) -> str:
        response = await self.request("GET", f"/v1/files/{file_id}/public-url")
        response.raise_for_status()
        data = response.json()
        return data.get("url", data.get("public_url"))
