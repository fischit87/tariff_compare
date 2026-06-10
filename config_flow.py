from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_DYNAMIC_BASE_EUR_MONTH,
    CONF_GRID_FEE_CT,
    CONF_METER_ENTITY,
    CONF_NAME,
    CONF_SPOT_PRICE_ENTITY,
    CONF_SPOT_PRICE_INCLUDES_VAT,
    CONF_SPOT_PRICE_UNIT,
    CONF_STATIC_BASE_EUR_MONTH,
    CONF_STATIC_PRICE_CT,
    CONF_VAT_PERCENT,
    DEFAULT_NAME,
    DEFAULT_SPOT_PRICE_UNIT,
    DEFAULT_VAT_PERCENT,
    DOMAIN,
    SPOT_PRICE_UNITS,
)


def _schema_with_defaults(user_input: dict | None = None) -> vol.Schema:
    user_input = user_input or {}

    return vol.Schema(
        {
            vol.Required(
                CONF_NAME, default=user_input.get(CONF_NAME, DEFAULT_NAME)
            ): selector.TextSelector(),
            vol.Required(
                CONF_METER_ENTITY, default=user_input.get(CONF_METER_ENTITY)
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["sensor"])
            ),
            vol.Required(
                CONF_SPOT_PRICE_ENTITY, default=user_input.get(CONF_SPOT_PRICE_ENTITY)
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["sensor"])
            ),
            vol.Required(
                CONF_SPOT_PRICE_UNIT,
                default=user_input.get(CONF_SPOT_PRICE_UNIT, DEFAULT_SPOT_PRICE_UNIT),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SPOT_PRICE_UNITS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_SPOT_PRICE_INCLUDES_VAT,
                default=user_input.get(CONF_SPOT_PRICE_INCLUDES_VAT, False),
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_GRID_FEE_CT, default=user_input.get(CONF_GRID_FEE_CT, 0.0)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=-100.0, max=100.0, step=0.001, mode=selector.NumberSelectorMode.BOX
                )
            ),
            vol.Required(
                CONF_DYNAMIC_BASE_EUR_MONTH,
                default=user_input.get(CONF_DYNAMIC_BASE_EUR_MONTH, 0.0),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0.0, max=1000.0, step=0.01, mode=selector.NumberSelectorMode.BOX
                )
            ),
            vol.Required(
                CONF_STATIC_PRICE_CT, default=user_input.get(CONF_STATIC_PRICE_CT, 0.0)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0.0, max=200.0, step=0.001, mode=selector.NumberSelectorMode.BOX
                )
            ),
            vol.Required(
                CONF_STATIC_BASE_EUR_MONTH,
                default=user_input.get(CONF_STATIC_BASE_EUR_MONTH, 0.0),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0.0, max=1000.0, step=0.01, mode=selector.NumberSelectorMode.BOX
                )
            ),
            vol.Required(
                CONF_VAT_PERCENT,
                default=user_input.get(CONF_VAT_PERCENT, DEFAULT_VAT_PERCENT),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0.0, max=50.0, step=0.1, mode=selector.NumberSelectorMode.BOX
                )
            ),
        }
    )


class TariffCompareConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_schema_with_defaults(),
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return TariffCompareOptionsFlow()


class TariffCompareOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input: dict | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        merged = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=_schema_with_defaults(merged),
        )
