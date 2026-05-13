from pydantic import BaseModel


class PresignedUrl(BaseModel):
    name: str
    physical_address: str
    physical_address_expiry: int
