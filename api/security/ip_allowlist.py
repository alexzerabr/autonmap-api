from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from ipaddress import ip_address, ip_network
from typing import Set

from ..config import settings

class IPAllowlistMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.allowed_ips: Set[ip_network] = self._parse_ips(settings.GLOBAL_IP_ALLOWLIST)

    def _parse_ips(self, ip_list_str: str) -> Set[ip_network]:
        if not ip_list_str:
            return set()
        
        allowed_set = set()
        for ip_str in ip_list_str.split(','):
            try:
                allowed_set.add(ip_network(ip_str.strip()))
            except ValueError:
                pass
        return allowed_set

    async def dispatch(self, request: Request, call_next):
        if not self.allowed_ips:
            return await call_next(request)

        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            client_ip_str = forwarded_for.split(',')[0].strip()
        else:
            client_ip_str = request.client.host

        try:
            client_ip = ip_address(client_ip_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid client IP address")

        is_allowed = any(client_ip in network for network in self.allowed_ips)

        if not is_allowed:
            raise HTTPException(status_code=403, detail=f"IP address {client_ip_str} is not allowed.")
        
        return await call_next(request)
