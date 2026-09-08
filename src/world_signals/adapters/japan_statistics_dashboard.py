from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re
from urllib.parse import urlencode

from .base import AdapterError, FetchSnapshot, fetch_bytes

JAPAN_STATISTICS_DASHBOARD_API_DOCS = "https://dashboard.e-stat.go.jp/en/static/api"
JAPAN_STATISTICS_DASHBOARD_DATA_API = "https://dashboard.e-stat.go.jp/api/1.0/Json/getData?"
JAPAN_HHSPEND_INDICATOR_CODE = "0704010101000010000"
JAPAN_HHSPEND_STAT_CODE = "00200561"
JAPAN_HHSPEND_REGION_CODE = "00000"
JAPAN_HHSPEND_CYCLE = "1"
JAPAN_HHSPEND_REGIONAL_RANK = "2"
JAPAN_HHSPEND_ORIGINAL_SERIES = "1"
JAPAN_HHSPEND_TIMEZONE = "Asia/Tokyo"
JAPAN_STATISTICS_DASHBOARD_ACCEPT = "application/json,*/*;q=0.1"
JAPAN_STATISTICS_DASHBOARD_NO_DATA_MESSAGE = "It ended normally but data did not exist."


@dataclass(frozen=True)
class JapanHouseholdSpendingValue:
    reference_period_code: str
    value: str
    is_provisional: bool
    indicator_code: str
    stat_code: str
    region_code: str
    cycle: str
    regional_rank: str
    original_or_seasonal_code: str
    unit_code: str | None

    def as_dict(self) -> dict:
        return asdict(self)


def _valid_month_code(value: str) -> bool:
    if not re.fullmatch(r"\d{6}00", value):
        return False
    month = int(value[4:6])
    return 1 <= month <= 12


def japan_household_spending_data_url(*, time_from: str, time_to: str) -> str:
    if not _valid_month_code(time_from) or not _valid_month_code(time_to):
        raise ValueError("Japan household-spending API time codes must be YYYYMM00")
    if time_from > time_to:
        raise ValueError("Japan household-spending API time_from must not exceed time_to")
    params = {
        "Lang": "EN",
        "IndicatorCode": JAPAN_HHSPEND_INDICATOR_CODE,
        "TimeFrom": time_from,
        "TimeTo": time_to,
        "Cycle": JAPAN_HHSPEND_CYCLE,
        "RegionalRank": JAPAN_HHSPEND_REGIONAL_RANK,
        "IsSeasonalAdjustment": JAPAN_HHSPEND_ORIGINAL_SERIES,
        "MetaGetFlg": "Y",
        "SectionHeaderFlg": "1",
    }
    return JAPAN_STATISTICS_DASHBOARD_DATA_API + urlencode(params)


def _result_status_and_message(get_stats: dict) -> tuple[int, str]:
    result = get_stats.get("RESULT")
    if not isinstance(result, dict):
        raise AdapterError("Japan Statistics Dashboard response missing GET_STATS.RESULT")
    raw = result.get("status", result.get("STATUS"))
    message = result.get("errorMsg", result.get("ERROR_MSG", ""))
    try:
        status = int(raw)
    except (TypeError, ValueError) as exc:
        raise AdapterError(f"invalid Japan Statistics Dashboard result status: {raw!r}") from exc
    if not isinstance(message, str):
        raise AdapterError(f"invalid Japan Statistics Dashboard result message: {message!r}")
    return status, message.strip()


def _data_objects(get_stats: dict) -> list[dict]:
    statistical = get_stats.get("STATISTICAL_DATA")
    if statistical is None:
        return []
    if not isinstance(statistical, dict):
        raise AdapterError("Japan Statistics Dashboard STATISTICAL_DATA is not an object")
    data_inf = statistical.get("DATA_INF")
    if data_inf is None:
        return []
    if not isinstance(data_inf, dict):
        raise AdapterError("Japan Statistics Dashboard DATA_INF is not an object")
    objects = data_inf.get("DATA_OBJ")
    if objects is None:
        return []
    if isinstance(objects, dict):
        return [objects]
    if isinstance(objects, list) and all(isinstance(row, dict) for row in objects):
        return objects
    raise AdapterError("Japan Statistics Dashboard DATA_OBJ has unexpected shape")


def parse_japan_household_spending_data_json(body: bytes | str) -> list[JapanHouseholdSpendingValue]:
    text = body.decode("utf-8-sig", errors="strict") if isinstance(body, bytes) else body
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AdapterError("Japan Statistics Dashboard response is not valid JSON") from exc
    get_stats = payload.get("GET_STATS") if isinstance(payload, dict) else None
    if not isinstance(get_stats, dict):
        raise AdapterError("Japan Statistics Dashboard response missing GET_STATS")
    status, message = _result_status_and_message(get_stats)
    if status == 1 and message == JAPAN_STATISTICS_DASHBOARD_NO_DATA_MESSAGE:
        if get_stats.get("STATISTICAL_DATA") is not None:
            raise AdapterError(
                "Japan Statistics Dashboard normal-no-data status unexpectedly carried STATISTICAL_DATA"
            )
        return []
    if status != 0:
        raise AdapterError(
            f"Japan Statistics Dashboard API returned result status {status}: {message!r}"
        )

    values: list[JapanHouseholdSpendingValue] = []
    seen: set[str] = set()
    for obj in _data_objects(get_stats):
        value = obj.get("VALUE")
        if not isinstance(value, dict):
            raise AdapterError("Japan Statistics Dashboard DATA_OBJ missing VALUE object")
        period = str(value.get("@time") or "")
        if not _valid_month_code(period):
            raise AdapterError(f"invalid household-spending reference-period code: {period!r}")
        if period in seen:
            raise AdapterError(f"duplicate household-spending reference-period row: {period}")
        seen.add(period)

        expected = {
            "@indicator": JAPAN_HHSPEND_INDICATOR_CODE,
            "@stat": JAPAN_HHSPEND_STAT_CODE,
            "@regionCode": JAPAN_HHSPEND_REGION_CODE,
            "@cycle": JAPAN_HHSPEND_CYCLE,
            "@regionRank": JAPAN_HHSPEND_REGIONAL_RANK,
            "@isSeasonal": JAPAN_HHSPEND_ORIGINAL_SERIES,
        }
        for key, wanted in expected.items():
            actual = str(value.get(key) or "")
            if actual != wanted:
                raise AdapterError(
                    f"household-spending API row {period} {key} mismatch: {actual!r} != {wanted!r}"
                )
        provisional = str(value.get("@isProvisional") or "")
        if provisional not in {"0", "1"}:
            raise AdapterError(
                f"household-spending API row {period} has invalid provisional flag {provisional!r}"
            )
        scalar = value.get("$")
        if scalar is None or str(scalar).strip() == "":
            raise AdapterError(f"household-spending API row {period} has empty value")
        values.append(
            JapanHouseholdSpendingValue(
                reference_period_code=period,
                value=str(scalar),
                is_provisional=provisional == "1",
                indicator_code=JAPAN_HHSPEND_INDICATOR_CODE,
                stat_code=JAPAN_HHSPEND_STAT_CODE,
                region_code=JAPAN_HHSPEND_REGION_CODE,
                cycle=JAPAN_HHSPEND_CYCLE,
                regional_rank=JAPAN_HHSPEND_REGIONAL_RANK,
                original_or_seasonal_code=JAPAN_HHSPEND_ORIGINAL_SERIES,
                unit_code=(str(value.get("@unit")) if value.get("@unit") is not None else None),
            )
        )
    return sorted(values, key=lambda row: row.reference_period_code)


def fetch_japan_household_spending_data(
    *, time_from: str, time_to: str, timeout: int = 30
) -> tuple[list[JapanHouseholdSpendingValue], FetchSnapshot]:
    url = japan_household_spending_data_url(time_from=time_from, time_to=time_to)
    body, snapshot = fetch_bytes(
        url,
        timeout=timeout,
        accept=JAPAN_STATISTICS_DASHBOARD_ACCEPT,
    )
    return parse_japan_household_spending_data_json(body), snapshot
