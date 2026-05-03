import asyncio
import json

import httpx

from app.integrations.scanner import IntegrationScanner, scan_hosts


def test_scan_hosts_allows_private_single_host():
    hosts = scan_hosts("192.168.178.252/32")

    assert [str(host) for host in hosts] == ["192.168.178.252"]


def test_scan_hosts_rejects_public_network():
    try:
        scan_hosts("8.8.8.8/32")
    except ValueError as exc:
        assert "private" in str(exc)
    else:
        raise AssertionError("Expected public scan range to be rejected")


def test_scan_hosts_rejects_too_large_network():
    try:
        scan_hosts("192.168.0.0/16")
    except ValueError as exc:
        assert "too large" in str(exc)
    else:
        raise AssertionError("Expected large scan range to be rejected")


def test_scanner_detects_shelly_pro_3em_from_rpc():
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode("utf-8"))
        if payload["method"] == "Shelly.GetDeviceInfo":
            return httpx.Response(
                200,
                json={
                    "id": "shellypro3em-fce8c0db18b4",
                    "name": "Shelly Pro 3EM",
                    "model": "SPEM-003CEBEU",
                },
            )
        if payload["method"] == "EM.GetStatus":
            return httpx.Response(200, json={"total_act_power": 42.0})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    result = asyncio.run(
        IntegrationScanner(transport=transport, timeout_seconds=0.1).scan("192.168.178.252/32")
    )

    assert result.scanned_hosts == 1
    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert candidate.integration_type == "shelly_3em"
    assert candidate.generation == "gen2"
    assert candidate.supported is True
    assert candidate.unique_id == "shelly:shellypro3em-fce8c0db18b4"
    assert candidate.suggested_settings["shelly_3em_base_url"] == "http://192.168.178.252"


def test_scanner_detects_shelly_3em_gen1_from_rest():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/rpc":
            return httpx.Response(404)
        if request.url.path == "/shelly":
            return httpx.Response(200, json={"type": "SHEM-3", "name": "Shelly 3EM"})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    result = asyncio.run(
        IntegrationScanner(transport=transport, timeout_seconds=0.1).scan("192.168.178.253/32")
    )

    assert len(result.candidates) == 1
    assert result.candidates[0].generation == "gen1"
    assert result.candidates[0].supported is True


def test_scanner_marks_duplicate_shelly_ids_and_sorts_ips():
    def handler(request: httpx.Request) -> httpx.Response:
        host = request.url.host
        if host not in {"192.168.178.50", "192.168.178.252", "192.168.178.253"}:
            return httpx.Response(404)
        if request.url.path != "/rpc":
            return httpx.Response(404)
        payload = json.loads(request.content.decode("utf-8"))
        if payload["method"] == "Shelly.GetDeviceInfo":
            if host in {"192.168.178.252", "192.168.178.253"}:
                return httpx.Response(
                    200,
                    json={
                        "id": "shellypro3em-fce8c0db18b4",
                        "name": "Shelly Pro 3EM",
                        "model": "SPEM-003CEBEU",
                    },
                )
            return httpx.Response(
                200,
                json={
                    "id": "shellypmmini-543204b8c290",
                    "name": "Shelly PM Mini",
                    "model": "SNPM-001PCEU16",
                },
            )
        if payload["method"] == "EM.GetStatus":
            return httpx.Response(200, json={"total_act_power": 42.0})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    result = asyncio.run(
        IntegrationScanner(transport=transport, timeout_seconds=0.1).scan("192.168.178.0/24")
    )

    assert [candidate.ip_address for candidate in result.candidates] == [
        "192.168.178.50",
        "192.168.178.252",
        "192.168.178.253",
    ]
    assert result.candidates[1].supported is True
    assert result.candidates[2].status == "duplicate"
    assert result.candidates[2].supported is False
    assert result.candidates[2].duplicate_of == "192.168.178.252"
