"""Google Sheets integration for nekonote scripts.

Usage::

    from nekonote import gsheets

    sheet = gsheets.open(spreadsheet_id="...", credentials="service_account.json")
    data = sheet.read("Sheet1!A1:D100")
    sheet.write("Sheet1!A1", [["Name", "Age"], ["Taro", 25]])
"""

from __future__ import annotations

from typing import Any


class Sheet:
    """Google Sheets wrapper."""

    def __init__(self, service: Any, spreadsheet_id: str):
        self._service = service
        self._spreadsheet_id = spreadsheet_id

    def read(self, range: str) -> list[list[Any]]:
        """Read values from a range."""
        result = (
            self._service.spreadsheets()
            .values()
            .get(spreadsheetId=self._spreadsheet_id, range=range)
            .execute()
        )
        return result.get("values", [])

    def write(self, range: str, values: list[list[Any]]) -> None:
        """Write values to a range."""
        self._service.spreadsheets().values().update(
            spreadsheetId=self._spreadsheet_id,
            range=range,
            valueInputOption="USER_ENTERED",
            body={"values": values},
        ).execute()

    def append(self, range: str, values: list[list[Any]]) -> None:
        """Append rows after the last row in range."""
        self._service.spreadsheets().values().append(
            spreadsheetId=self._spreadsheet_id,
            range=range,
            valueInputOption="USER_ENTERED",
            body={"values": values},
        ).execute()

    def clear(self, range: str) -> None:
        """Clear values in a range."""
        self._service.spreadsheets().values().clear(
            spreadsheetId=self._spreadsheet_id,
            range=range,
        ).execute()


def open(spreadsheet_id: str, *, credentials: str = "service_account.json") -> Sheet:
    """Open a Google Sheet.

    Args:
        spreadsheet_id: The ID from the Google Sheets URL.
        credentials: Path to a service account JSON key file.
    """
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build

    creds = Credentials.from_service_account_file(
        credentials,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    service = build("sheets", "v4", credentials=creds)
    return Sheet(service, spreadsheet_id)
