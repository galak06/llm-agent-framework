"""Run a healthcheck against the running API."""

from __future__ import annotations

import sys

import httpx


def main() -> None:
    try:
        response = httpx.get('http://localhost:8000/api/v1/health', timeout=10)
        data = response.json()
        print(f'Status: {data["status"]}')
        for service, status in data.get('checks', {}).items():
            print(f'  {service}: {status}')
        if data['status'] != 'ok':
            sys.exit(1)
    except Exception as e:
        print(f'Healthcheck failed: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
