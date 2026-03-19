# Customer 360 Field Mapping

This mapping documents where each requested field is stored for GPT Actions queries.

## Required fields

| Required field | Source |
|---|---|
| `customer_id` | `retail_core.customers.customer_id` |
| `loyalty_id` | `retail_core.customers.loyalty_id` |
| `first_name` | `retail_core.customers.first_name` |
| `last_name` | `retail_core.customers.last_name` |
| `tier` | `retail_core.customers.tier` |
| `preferred_store_id` | `retail_core.customers.preferred_store_id` |
| `preferred_sizes` | `retail_core.customer_preferences.preferred_sizes` |
| `preferred_colors` | `retail_core.customer_preferences.preferred_colors` |
| `preferred_brands` | `retail_core.customer_preferences.preferred_brands` |
| `shopping_occasions` | `retail_core.customer_preferences.shopping_occasions` |
| `recent_purchases` | `retail_analytics.customer_recent_purchases.recent_purchases` |
| `saved_items` | `retail_analytics.customer_saved_items_summary.saved_items` |
| `return_history_summary` | `retail_analytics.customer_return_history_summary.return_history_summary` |
| `stylist_notes` | `retail_core.customers.stylist_notes` |
| `lifetime_value_band` | `retail_core.customers.lifetime_value_band` |

## Derived projection for API consumers

All required fields are exposed in `retail_analytics.customer_360`, which joins:

- `retail_core.customers`
- `retail_core.customer_preferences`
- `retail_analytics.customer_recent_purchases`
- `retail_analytics.customer_saved_items_summary`
- `retail_analytics.customer_return_history_summary`
