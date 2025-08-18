"""Constants"""
# import voluptuous as vol
# from enum import Enum

# from homeassistant.helpers.config_validation import make_entity_service_schema
# import homeassistant.helpers.config_validation as cv

DOMAIN = "generic_bt"
DEVICE_STARTUP_TIMEOUT_SECONDS = 30


CONF_CALC_BODY_METRICS = "calculate body metrics"
CONF_SEX = "sex"
CONF_HEIGHT = "height"
CONF_BIRTHDATE = "birthdate"

CONF_FEET = "feet"
CONF_INCHES = "inches"

# class Schema(Enum):
#     """General used service schema definition"""

#     WRITE_GATT = make_entity_service_schema(
#         {
#             vol.Required("target_uuid"): cv.string,
#             vol.Required("data"): cv.string
#         }
#     )
#     READ_GATT = make_entity_service_schema(
#         {
#             vol.Required("target_uuid"): cv.string
#         }
#     )
