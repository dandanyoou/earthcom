from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ExternalIdentity:
    provider: str
    subject: str
    email: str


class IdentityProvider(Protocol):
    provider_name: str

    async def authenticate(self, assertion: str) -> ExternalIdentity: ...
