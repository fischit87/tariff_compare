from __future__ import annotations

DOMAIN = "tariff_compare"

CONF_METER_ENTITY = "meter_entity"
CONF_SPOT_PRICE_ENTITY = "spot_price_entity"
CONF_SPOT_PRICE_UNIT = "spot_price_unit"
CONF_SPOT_PRICE_INCLUDES_VAT = "spot_price_includes_vat"
CONF_GRID_FEE_CT = "grid_fee_ct"
CONF_DYNAMIC_BASE_EUR_MONTH = "dynamic_base_eur_month"
CONF_STATIC_PRICE_CT = "static_price_ct"
CONF_STATIC_BASE_EUR_MONTH = "static_base_eur_month"
CONF_VAT_PERCENT = "vat_percent"
CONF_NAME = "name"

DEFAULT_NAME = "Stromtarif Vergleich"
DEFAULT_VAT_PERCENT = 19.0
DEFAULT_SPOT_PRICE_UNIT = "EUR_KWH"

SPOT_PRICE_UNITS = [
    "CT_KWH",
    "EUR_KWH",
]

ATTR_LAST_DELTA_KWH = "last_delta_kwh"
ATTR_DYNAMIC_PRICE_CT = "dynamic_price_ct_kwh"
ATTR_STATIC_PRICE_CT = "static_price_ct_kwh"
ATTR_DYNAMIC_BASE_DAILY_EUR = "dynamic_base_daily_eur"
ATTR_STATIC_BASE_DAILY_EUR = "static_base_daily_eur"
ATTR_DYNAMIC_BASE_MONTHLY_EUR = "dynamic_base_monthly_eur"
ATTR_STATIC_BASE_MONTHLY_EUR = "static_base_monthly_eur"
ATTR_LAST_METER_VALUE = "last_meter_value_kwh"
ATTR_LAST_SPOT_VALUE = "last_spot_raw"

PLATFORMS = ["sensor"]
