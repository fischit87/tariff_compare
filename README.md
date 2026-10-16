<h2>I am not a developer, so this is just for fun and for anyone who might have use of it. </h2>
<p>Anyone who would like to support this, please contact me.</p>

<h2>What is it</h2>
Tariff Compare is a Home Assistant custom integration that compares a dynamic electricity tariff with a regular tariff using existing sensor entities. It calculates current energy costs, daily and monthly totals, and the resulting savings based on your meter readings, spot price entity, VAT handling, grid fees, and fixed monthly base charges. 

The integration is designed for local use, stores its data persistently, and exposes clear sensor entities for monitoring electricity costs and tariff differences directly in Home Assistant.

<h2>What you need</h2>
Required entities: an electricity meter sensor and a spot price sensor i.e. from Nord Pool. The meter provides consumption deltas, while the spot price sensor provides the current dynamic electricity price needed to compare real dynamic tariff costs with a fixed-price tariff. 
<br><br>
<ul>
  <li>Electricity meter sensor: a cumulative, increasing energy reading in kWh, for example 13002.3 → 13002.4 → 13002.5 kWh. Steps of exactly 0.1 kWh are not required. Do not use instantaneous power (W/kW) or a daily resetting consumption sensor.</li>
  <li>Spot price sensor: a numeric price with a matching configured unit, for example 0.30 EUR/kWh with EUR_KWH, or 30.0 ct/kWh with CT_KWH. </li>
</ul>


For Germany, check the location- and contract-specific tariff components at [Tibber electricity prices](https://tibber.com/de/strompreise). See the setup guide below for how to enter them. 

## 📦 Manual Installation (without HACS)
1. Download or clone the repository (or download a release).
2. Create `custom_components/tariff_compare/` inside your Home Assistant configuration directory. Copy the integration's Python files, `manifest.json`, and the `translations/` directory into it. For example, the manifest must be at `custom_components/tariff_compare/manifest.json`.
3. Restart Home Assistant.
4. Follow the setup guide below to prepare Nord Pool and add Tariff Compare.

## Setup guide

### 1. Set up Nord Pool first

Follow the [official Nord Pool integration instructions](https://www.home-assistant.io/integrations/nordpool/) in Home Assistant. Select your market area and EUR as the currency, then find the **Current price** sensor for that area. Use the current price, not a daily average or tomorrow's price.

For this sensor, use `EUR_KWH` and leave `spot_price_includes_vat` enabled (`true`), because VAT should be included in the grid_fee_ct price. 

Have a cumulative electricity consumption sensor in kWh ready as well. Both selected sensors must have numeric states during setup; `unknown` and `unavailable` are rejected. The integration does not convert the meter's unit.

### 2. Add Tariff Compare

Go to **Settings → Devices & services → Add integration**, search for **Vergleich dynamischer Stromtarif vs. Normal** (the integration's current display name), and complete the form.

The table uses the field names from the code. Monthly fee fields end in `_month`, not `_monat`; the VAT field is `vat_percent`, not `vat`.

| Field | What to enter |
| --- | --- |
| `name` | Any descriptive name, such as `Tibber vs. fixed tariff`. |
| `meter_entity` | Your cumulative, increasing electricity consumption sensor in **kWh**. |
| `spot_price_entity` | The current Nord Pool price entity for your area, or a derived current-price sensor with known VAT treatment. |
| `spot_price_unit` | Keep **`EUR_KWH`** for prices in EUR/kWh. Select `CT_KWH` only if the entity reports cents/kWh. |
| `spot_price_includes_vat` | Set **`true` only when the entered value in grid_fee_ct includes VAT**. |
| `grid_fee_ct` | The additional consumption-based component of your dynamic tariff in **ct/kWh**, excluding the spot price and monthly base fee. For example, `18.85` means 18.85 ct/kWh. Check your own regional and contractual components at [Tibber electricity prices](https://tibber.com/de/strompreise) and in your contract; this is an illustrative value, not a universal or current rate. Include the applicable taxes, levies, grid charges, and other per-kWh additions not already included in your price entity. Enter the final VAT-inclusive amount: the integration adds this value unchanged. |
| `dynamic_base_eur_month` | Your Tibber/dynamic tariff's fixed monthly base charge in **EUR/month**, including VAT. Include applicable fixed monthly components once; do not put them in `grid_fee_ct`. |
| `static_price_ct` | The fixed tariff's final VAT-inclusive consumption price in **ct/kWh**. For example, enter `30.01` for **0.3001 EUR/kWh**. |
| `static_base_eur_month` | The fixed tariff's monthly base charge in **EUR/month**, including VAT. |
| `vat_percent` | Leave at `19` for a 19% VAT calculation. This is applied **only to the spot price**, and only when `spot_price_includes_vat` is `false`. With `true`, no additional VAT is added to the spot price. |

Examples use decimal points: `18.85` and `30.01` correspond to German decimal notation `18,85` and `30,01`.

### 3. Check the price calculation

For `EUR_KWH`, the integration calculates:

```text
spot price in ct/kWh = sensor value × 100
if spot_price_includes_vat is false:
    spot price in ct/kWh = spot price in ct/kWh × (1 + vat_percent / 100)

dynamic price in ct/kWh = spot price in ct/kWh + grid_fee_ct
```

For example, with a VAT-exclusive Nord Pool value of **0.10 EUR/kWh**, `vat_percent = 19`, `spot_price_includes_vat = false`, and `grid_fee_ct = 18.85`, the resulting dynamic price is **30.75 ct/kWh**: `10 × 1.19 + 18.85`.

If your selected entity already reports **0.119 EUR/kWh including VAT**, use `spot_price_includes_vat = true` to obtain the same result. Setting it to `true` for the raw VAT-exclusive sensor would omit VAT on the spot price. Avoid counting charges twice if a derived sensor already includes tariff additions.

The integration uses the static price, additional dynamic tariff component, and both base charges exactly as entered; `vat_percent` does not adjust these amounts.

### 4. Verify your sensors

After saving, check the dynamic price and cost sensors against your tariff. Energy costs accumulate from increases in the meter reading; on a fresh setup, the first reading establishes the baseline. Historical consumption is not imported. Frequent meter updates improve the comparison because each consumption delta is charged at the current spot price when processed.

Daily totals include the monthly base charge divided by the number of days in the current month. Monthly totals include the **full monthly base charge**, even when setup starts partway through a month. Yearly totals add the monthly base charge multiplied by the current calendar month number. Savings are calculated as **fixed-tariff total minus dynamic-tariff total**, so a positive value means the dynamic tariff is cheaper.

