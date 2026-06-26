from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_DYNAMIC_BASE_DAILY_EUR,
    ATTR_DYNAMIC_BASE_MONTHLY_EUR,
    ATTR_DYNAMIC_PRICE_CT,
    ATTR_LAST_DELTA_KWH,
    ATTR_LAST_METER_VALUE,
    ATTR_LAST_SPOT_VALUE,
    ATTR_STATIC_BASE_DAILY_EUR,
    ATTR_STATIC_BASE_MONTHLY_EUR,
    ATTR_STATIC_PRICE_CT,
    CONF_DYNAMIC_BASE_EUR_MONTH,
    CONF_GRID_FEE_CT,
    CONF_METER_ENTITY,
    CONF_SPOT_PRICE_ENTITY,
    CONF_SPOT_PRICE_INCLUDES_VAT,
    CONF_SPOT_PRICE_UNIT,
    CONF_STATIC_BASE_EUR_MONTH,
    CONF_STATIC_PRICE_CT,
    CONF_VAT_PERCENT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class TariffData:
    last_meter_value: float | None = None
    last_spot_raw: float | None = None
    dynamic_price_ct_kwh: float = 0.0
    static_price_ct_kwh: float = 0.0

    today_dynamic_energy_cost_eur: float = 0.0
    today_static_energy_cost_eur: float = 0.0
    today_dynamic_total_eur: float = 0.0
    today_static_total_eur: float = 0.0
    today_savings_eur: float = 0.0

    month_dynamic_energy_cost_eur: float = 0.0
    month_static_energy_cost_eur: float = 0.0
    month_dynamic_total_eur: float = 0.0
    month_static_total_eur: float = 0.0
    month_savings_eur: float = 0.0

    year_dynamic_energy_cost_eur: float = 0.0
    year_static_energy_cost_eur: float = 0.0
    year_dynamic_total_eur: float = 0.0
    year_static_total_eur: float = 0.0
    year_savings_eur: float = 0.0

    today_consumption_kwh: float = 0.0
    month_consumption_kwh: float = 0.0
    year_consumption_kwh: float = 0.0

    last_delta_kwh: float = 0.0
    last_reset_day: str | None = None
    last_reset_month: str | None = None
    last_reset_year: str | None = None
    updated_at: str | None = None

    def as_dict(self) -> dict:
        return {key: value for key, value in self.__dict__.items()}


class TariffCompareCoordinator(DataUpdateCoordinator[TariffData]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
        )
        self.entry = entry
        self.data = TariffData()
        self._store = Store(hass, 1, f"{DOMAIN}_{entry.entry_id}")
        self._unsub_state = None

    @property
    def config(self) -> dict:
        return {**self.entry.data, **self.entry.options}

    async def async_setup(self) -> None:
        stored = await self._store.async_load()
        if stored:
            self.data = TariffData(**stored)

        now = dt_util.now()
        if self.data.last_reset_day is None:
            self.data.last_reset_day = now.date().isoformat()
        if self.data.last_reset_month is None:
            self.data.last_reset_month = f"{now.year}-{now.month:02d}"
        if self.data.last_reset_year is None:
            self.data.last_reset_year = f"{now.year}"

        entities = [
            self.config[CONF_METER_ENTITY],
            self.config[CONF_SPOT_PRICE_ENTITY],
        ]
        self._unsub_state = async_track_state_change_event(
            self.hass, entities, self._async_handle_source_change
        )

        await self.async_refresh_from_states()
        self.async_set_updated_data(self.data)

    async def async_unload(self) -> None:
        if self._unsub_state:
            self._unsub_state()
            self._unsub_state = None

        try:
            await self._store.async_save(self.data.as_dict())
            _LOGGER.debug("Coordinator state saved during unload")
        except Exception as err:
            _LOGGER.error("Error saving coordinator state during unload: %s", err)

    @callback
    async def _async_handle_source_change(
        self, event: Event[EventStateChangedData]
    ) -> None:
        await self.async_refresh_from_states()

    def _spot_to_ct_per_kwh(self, raw: float) -> float:
        unit_mode = self.config[CONF_SPOT_PRICE_UNIT]
        vat_percent = float(self.config[CONF_VAT_PERCENT])
        includes_vat = self.config[CONF_SPOT_PRICE_INCLUDES_VAT]

        if unit_mode == "EUR_KWH":
            ct_kwh = raw * 100.0
        else:
            ct_kwh = raw

        if not includes_vat:
            ct_kwh = ct_kwh * (1 + vat_percent / 100.0)

        return ct_kwh

    def _dynamic_total_price_ct(self, spot_raw: float) -> float:
        spot_ct = self._spot_to_ct_per_kwh(spot_raw)
        grid_fee_ct = float(self.config[CONF_GRID_FEE_CT])
        return spot_ct + grid_fee_ct

    def _days_in_current_month(self, now: datetime) -> int:
        if now.month == 12:
            next_month = datetime(now.year + 1, 1, 1, tzinfo=now.tzinfo)
        else:
            next_month = datetime(now.year, now.month + 1, 1, tzinfo=now.tzinfo)
        this_month = datetime(now.year, now.month, 1, tzinfo=now.tzinfo)
        return (next_month - this_month).days

    async def async_refresh_from_states(self) -> None:
        now = dt_util.now()

        meter_state = self.hass.states.get(self.config[CONF_METER_ENTITY])
        spot_state = self.hass.states.get(self.config[CONF_SPOT_PRICE_ENTITY])

        if meter_state is None or spot_state is None:
            return

        try:
            meter_value = float(meter_state.state)
            spot_raw = float(spot_state.state)
        except (TypeError, ValueError) as err:
            _LOGGER.warning("Invalid state for meter/spot entities: %s", err)
            return

        current_day = now.date().isoformat()
        current_month = f"{now.year}-{now.month:02d}"
        current_year = f"{now.year}"

        if self.data.last_reset_day != current_day:
            self.data.today_dynamic_energy_cost_eur = 0.0
            self.data.today_static_energy_cost_eur = 0.0
            self.data.today_consumption_kwh = 0.0
            self.data.last_reset_day = current_day

        if self.data.last_reset_month != current_month:
            self.data.month_dynamic_energy_cost_eur = 0.0
            self.data.month_static_energy_cost_eur = 0.0
            self.data.month_consumption_kwh = 0.0
            self.data.last_reset_month = current_month

        if self.data.last_reset_year != current_year:
            self.data.year_dynamic_energy_cost_eur = 0.0
            self.data.year_static_energy_cost_eur = 0.0
            self.data.year_consumption_kwh = 0.0
            self.data.last_reset_year = current_year

        dynamic_price_ct = self._dynamic_total_price_ct(spot_raw)
        static_price_ct = float(self.config[CONF_STATIC_PRICE_CT])

        delta_kwh = 0.0
        if self.data.last_meter_value is not None:
            diff = meter_value - self.data.last_meter_value
            if diff >= 0:
                delta_kwh = diff

        dynamic_delta_cost_eur = delta_kwh * dynamic_price_ct / 100.0
        static_delta_cost_eur = delta_kwh * static_price_ct / 100.0

        self.data.dynamic_price_ct_kwh = dynamic_price_ct
        self.data.static_price_ct_kwh = static_price_ct

        self.data.today_consumption_kwh += delta_kwh
        self.data.month_consumption_kwh += delta_kwh
        self.data.year_consumption_kwh += delta_kwh

        self.data.today_dynamic_energy_cost_eur += dynamic_delta_cost_eur
        self.data.today_static_energy_cost_eur += static_delta_cost_eur
        self.data.month_dynamic_energy_cost_eur += dynamic_delta_cost_eur
        self.data.month_static_energy_cost_eur += static_delta_cost_eur
        self.data.year_dynamic_energy_cost_eur += dynamic_delta_cost_eur
        self.data.year_static_energy_cost_eur += static_delta_cost_eur

        days_in_month = self._days_in_current_month(now)
        dynamic_base_daily_eur = (
            float(self.config[CONF_DYNAMIC_BASE_EUR_MONTH]) / days_in_month
        )
        static_base_daily_eur = (
            float(self.config[CONF_STATIC_BASE_EUR_MONTH]) / days_in_month
        )

        self.data.today_dynamic_total_eur = (
            self.data.today_dynamic_energy_cost_eur + dynamic_base_daily_eur
        )
        self.data.today_static_total_eur = (
            self.data.today_static_energy_cost_eur + static_base_daily_eur
        )
        self.data.today_savings_eur = (
            self.data.today_static_total_eur - self.data.today_dynamic_total_eur
        )

        self.data.month_dynamic_total_eur = (
            self.data.month_dynamic_energy_cost_eur
            + float(self.config[CONF_DYNAMIC_BASE_EUR_MONTH])
        )
        self.data.month_static_total_eur = (
            self.data.month_static_energy_cost_eur
            + float(self.config[CONF_STATIC_BASE_EUR_MONTH])
        )
        self.data.month_savings_eur = (
            self.data.month_static_total_eur - self.data.month_dynamic_total_eur
        )

        self.data.year_dynamic_total_eur = (
            self.data.year_dynamic_energy_cost_eur
            + (float(self.config[CONF_DYNAMIC_BASE_EUR_MONTH]) * now.month)
        )
        self.data.year_static_total_eur = (
            self.data.year_static_energy_cost_eur
            + (float(self.config[CONF_STATIC_BASE_EUR_MONTH]) * now.month)
        )
        self.data.year_savings_eur = (
            self.data.year_static_total_eur - self.data.year_dynamic_total_eur
        )

        self.data.last_meter_value = meter_value
        self.data.last_spot_raw = spot_raw
        self.data.last_delta_kwh = delta_kwh
        self.data.updated_at = now.isoformat()

        await self._store.async_save(self.data.as_dict())
        self.async_set_updated_data(self.data)

    def extra_state_attributes(self) -> dict:
        now = dt_util.now()
        days_in_month = self._days_in_current_month(now)
        return {
            ATTR_LAST_DELTA_KWH: round(self.data.last_delta_kwh, 2),
            ATTR_DYNAMIC_PRICE_CT: round(self.data.dynamic_price_ct_kwh, 2),
            ATTR_STATIC_PRICE_CT: round(self.data.static_price_ct_kwh, 2),
            ATTR_DYNAMIC_BASE_DAILY_EUR: round(
                float(self.config[CONF_DYNAMIC_BASE_EUR_MONTH]) / days_in_month, 2
            ),
            ATTR_STATIC_BASE_DAILY_EUR: round(
                float(self.config[CONF_STATIC_BASE_EUR_MONTH]) / days_in_month, 2
            ),
            ATTR_DYNAMIC_BASE_MONTHLY_EUR: float(
                self.config[CONF_DYNAMIC_BASE_EUR_MONTH]
            ),
            ATTR_STATIC_BASE_MONTHLY_EUR: float(
                self.config[CONF_STATIC_BASE_EUR_MONTH]
            ),
            ATTR_LAST_METER_VALUE: self.data.last_meter_value,
            ATTR_LAST_SPOT_VALUE: self.data.last_spot_raw,
            "meter_entity": self.config[CONF_METER_ENTITY],
            "spot_price_entity": self.config[CONF_SPOT_PRICE_ENTITY],
        }
