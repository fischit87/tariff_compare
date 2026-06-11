<h2>I am not a developer, so this is just for fun and for anyone who might have use of it. </h2>
<p>Anyone who would like to support, please contact me.</p>

<h2>What is it</h2>
Tariff Compare is a Home Assistant custom integration that compares a dynamic electricity tariff with a regular tariff using existing sensor entities. It calculates current energy costs, daily and monthly totals, and the resulting savings based on your meter readings, spot price entity, VAT handling, grid fees, and fixed monthly base charges. 

The integration is designed for local use, stores its data persistently, and exposes clear sensor entities for monitoring electricity costs and tariff differences directly in Home Assistant.

<h2>What you need</h2>
Required entities: an electricity meter sensor and a spot price sensor i.e. from Nord Pool. The meter provides consumption deltas, while the spot price sensor provides the current dynamic electricity price needed to compare real dynamic tariff costs with a fixed-price tariff. 
<br><br>
<ul>
  <li>Eelectricity meter sensor expects a total increasing sensor where every 0.1kWh is measured i.e. 13002,3 kWh -> 13002,4 kWh -> 13002,5 kWh</li>
  <li>Spotprice is expected in format 0,30€ </li>
</ul>


For Germany Grid fees can be found here: https://tibber.com/de/strompreise 

## 📦 Manual Installation (without HACS)
1. Download or clone latest release
2. Copy it to your custom_components folder
3. Restart Homeassistant
4. In Home Assistant, go to Settings → Integration → Add Integration
