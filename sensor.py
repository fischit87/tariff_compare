from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_EURO
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TariffCompareCoordinator

SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="dynamic_price_ct_kwh",
        name="Aktueller dynamischer Preis inkl. Steuern",
        native_unit_of_measurement="ct/kWh",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:transmission-tower-export",
    ),
    SensorEntityDescription(
        key="today_dynamic_total_eur",
        name="Heute Kosten dynamisch",
        native_unit_of_measurement=CURRENCY_EURO,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:cash-clock",
    ),
    SensorEntityDescription(
        key="today_static_total_eur",
        name="Heute Kosten normal",
        native_unit_of_measurement=CURRENCY_EURO,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:cash",
    ),
    SensorEntityDescription(
        key="today_savings_eur",
        name="Heute Ersparnis im dynamischen Stromtarif",
        native_unit_of_measurement=CURRENCY_EURO,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:piggy-bank",
    ),
    SensorEntityDescription(
        key="month_dynamic_total_eur",
        name="Monat Kosten dynamisch",
        native_unit_of_measurement=CURRENCY_EURO,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:chart-line",
    ),
    SensorEntityDescription(
        key="month_static_total_eur",
        name="Monat Kosten normal",
        native_unit_of_measurement=CURRENCY_EURO,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:chart-box",
    ),
    SensorEntityDescription(
        key="month_savings_eur",
        name="Monat Ersparnis im dynamischen Stromtarif",
        native_unit_of_measurement=CURRENCY_EURO,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:cash-plus",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    coordinator: TariffCompareCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        TariffCompareSensor(entry, coordinator, description)
        for description in SENSORS
    ]

    async_add_entities(entities)


class TariffCompareSensor(CoordinatorEntity[TariffCompareCoordinator], SensorEntity): 
    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: TariffCompareCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)  # <<< NEW
        self.entity_description = description
        self._entry = entry

        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.name

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.title,
            manufacturer="Local",
            model="Tariff Compare",
        )

    @property
    def available(self) -> bool:
        return super().available  # <<< CHANGED

    @property
    def native_value(self) -> StateType:
        value = getattr(self.coordinator.data, self.entity_description.key, None)
        if isinstance(value, float):
            return round(value, 6)
        return value

    @property
    def extra_state_attributes(self) -> dict:
        return self.coordinator.extra_state_attributes()