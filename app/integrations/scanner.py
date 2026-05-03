from __future__ import annotations

import asyncio
import ipaddress
from dataclasses import asdict, dataclass
from typing import Any

import httpx


PRIVATE_SCAN_NETWORKS = (
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
)


@dataclass(frozen=True, slots=True)
class IntegrationCandidate:
    ip_address: str
    base_url: str
    integration_type: str
    name: str
    model: str | None
    generation: str | None
    status: str
    confidence: str
    source: str
    supported: bool
    suggested_settings: dict[str, Any]
    details: dict[str, Any]
    error_status: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class IntegrationScanResult:
    cidr: str
    scanned_hosts: int
    candidates: list[IntegrationCandidate]
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["candidates"] = [candidate.to_dict() for candidate in self.candidates]
        return payload


class IntegrationScanner:
    def __init__(
        self,
        *,
        timeout_seconds: float = 0.6,
        concurrency: int = 32,
        max_hosts: int = 254,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.concurrency = concurrency
        self.max_hosts = max_hosts
        self.transport = transport

    async def scan(self, cidr: str) -> IntegrationScanResult:
        hosts = scan_hosts(cidr, max_hosts=self.max_hosts)
        semaphore = asyncio.Semaphore(self.concurrency)
        errors: list[str] = []
        candidates: list[IntegrationCandidate] = []
        timeout = httpx.Timeout(self.timeout_seconds)

        async with httpx.AsyncClient(timeout=timeout, transport=self.transport) as client:
            tasks = [self._probe_limited(client, semaphore, str(host), errors) for host in hosts]
            for result in await asyncio.gather(*tasks):
                if result is not None:
                    candidates.append(result)

        candidates.sort(key=lambda candidate: candidate.ip_address)
        return IntegrationScanResult(
            cidr=str(ipaddress.ip_network(cidr, strict=False)),
            scanned_hosts=len(hosts),
            candidates=candidates,
            errors=errors,
        )

    async def _probe_limited(
        self,
        client: httpx.AsyncClient,
        semaphore: asyncio.Semaphore,
        ip_address: str,
        errors: list[str],
    ) -> IntegrationCandidate | None:
        async with semaphore:
            try:
                return await probe_host(client, ip_address)
            except Exception as exc:
                if len(errors) < 20:
                    errors.append(f"{ip_address}: {exc}")
                return None


def scan_hosts(cidr: str, *, max_hosts: int = 254) -> list[ipaddress.IPv4Address]:
    try:
        network = ipaddress.ip_network(cidr, strict=False)
    except ValueError as exc:
        raise ValueError(f"Invalid scan range: {cidr}") from exc

    if network.version != 4:
        raise ValueError("Only IPv4 scan ranges are supported")
    if not is_allowed_private_network(network):
        raise ValueError("Scan range must be a private local IPv4 network")

    hosts = list(network.hosts())
    if not hosts and network.num_addresses == 1:
        hosts = [network.network_address]
    if len(hosts) > max_hosts:
        raise ValueError(f"Scan range too large: {len(hosts)} hosts, maximum is {max_hosts}")
    return hosts


def is_allowed_private_network(network: ipaddress.IPv4Network) -> bool:
    return any(network.subnet_of(allowed) for allowed in PRIVATE_SCAN_NETWORKS)


async def probe_host(client: httpx.AsyncClient, ip_address: str) -> IntegrationCandidate | None:
    base_url = f"http://{ip_address}"
    candidate = await probe_shelly_gen2(client, ip_address, base_url)
    if candidate is not None:
        return candidate
    return await probe_shelly_gen1(client, ip_address, base_url)


async def probe_shelly_gen2(
    client: httpx.AsyncClient,
    ip_address: str,
    base_url: str,
) -> IntegrationCandidate | None:
    device_info = await post_rpc(client, base_url, "Shelly.GetDeviceInfo")
    if not isinstance(device_info, dict):
        return None

    em_status = await post_rpc(client, base_url, "EM.GetStatus", {"id": 0})
    model = string_or_none(device_info.get("model"))
    device_id = string_or_none(device_info.get("id"))
    name = string_or_none(device_info.get("name")) or device_id or ip_address
    is_3em = has_3em_hint(model, device_id, name) or is_em_status(em_status)

    return IntegrationCandidate(
        ip_address=ip_address,
        base_url=base_url,
        integration_type="shelly_3em" if is_3em else "shelly",
        name=name,
        model=model,
        generation="gen2",
        status="online",
        confidence="high" if is_3em else "medium",
        source="shelly_rpc",
        supported=is_3em,
        suggested_settings=shelly_settings(base_url, "gen2") if is_3em else {},
        details={
            "device_info": compact_dict(device_info),
            "em_status": compact_dict(em_status) if isinstance(em_status, dict) else None,
        },
    )


async def probe_shelly_gen1(
    client: httpx.AsyncClient,
    ip_address: str,
    base_url: str,
) -> IntegrationCandidate | None:
    try:
        response = await client.get(f"{base_url}/shelly")
    except httpx.HTTPError:
        return None
    if response.status_code >= 400:
        return None
    try:
        device_info = response.json()
    except ValueError:
        return None
    if not isinstance(device_info, dict):
        return None

    model = string_or_none(device_info.get("type")) or string_or_none(device_info.get("model"))
    name = string_or_none(device_info.get("name")) or string_or_none(device_info.get("id")) or ip_address
    is_3em = has_3em_hint(model, name, string_or_none(device_info.get("mac")))

    return IntegrationCandidate(
        ip_address=ip_address,
        base_url=base_url,
        integration_type="shelly_3em" if is_3em else "shelly",
        name=name,
        model=model,
        generation="gen1",
        status="online",
        confidence="high" if is_3em else "medium",
        source="shelly_rest",
        supported=is_3em,
        suggested_settings=shelly_settings(base_url, "gen1") if is_3em else {},
        details={"device_info": compact_dict(device_info)},
    )


async def post_rpc(
    client: httpx.AsyncClient,
    base_url: str,
    method: str,
    params: dict[str, Any] | None = None,
) -> Any:
    try:
        response = await client.post(
            f"{base_url}/rpc",
            json={"id": 1, "method": method, "params": params or {}},
        )
    except httpx.HTTPError:
        return None
    if response.status_code >= 400:
        return None
    try:
        payload = response.json()
    except ValueError:
        return None
    if isinstance(payload, dict) and "result" in payload and isinstance(payload["result"], dict):
        return payload["result"]
    return payload


def shelly_settings(base_url: str, generation: str) -> dict[str, Any]:
    return {
        "meter_provider": "shelly_3em",
        "shelly_3em_base_url": base_url,
        "shelly_3em_generation": generation,
        "meter_power_sign": "normal",
    }


def has_3em_hint(*values: str | None) -> bool:
    haystack = " ".join(value.lower() for value in values if value)
    return "3em" in haystack or "shem-3" in haystack or "pro3em" in haystack or "pro 3em" in haystack


def is_em_status(value: Any) -> bool:
    return isinstance(value, dict) and any(
        key in value
        for key in (
            "total_act_power",
            "a_current",
            "a_act_power",
            "b_act_power",
            "c_act_power",
        )
    )


def string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def compact_dict(value: dict[str, Any] | None) -> dict[str, Any]:
    if not value:
        return {}
    return {
        key: item
        for key, item in value.items()
        if isinstance(item, str | int | float | bool) or item is None
    }
