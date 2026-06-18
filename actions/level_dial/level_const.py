"""Constants for the Level Dial action."""

EMPTY_STRING = ""
LEVEL_DIAL = "Level Dial"

LABEL_LEVEL_STEP = "actions.home_assistant.level.step.label"
LABEL_LEVEL_LABEL = "actions.home_assistant.level.label.label"
LABEL_LEVEL_NO_ENTITY = "actions.home_assistant.level.no_entity.label"

SETTING_LEVEL = "level"
SETTING_STEP = "step"
SETTING_LABEL = "label"
SETTING_LEVEL_STEP = f"{SETTING_LEVEL}.{SETTING_STEP}"
SETTING_LEVEL_LABEL = f"{SETTING_LEVEL}.{SETTING_LABEL}"

DEFAULT_STEP = 10
DEFAULT_LABEL = ""
DEFAULT_BATCH_DELAY = 150
MIN_STEP = 1
MAX_STEP = 50
MIN_BATCH_DELAY = 0
MAX_BATCH_DELAY = 500

SETTING_BATCH_DELAY = "batch_delay"
SETTING_LEVEL_BATCH_DELAY = f"{SETTING_LEVEL}.{SETTING_BATCH_DELAY}"
LABEL_LEVEL_BATCH_DELAY = "actions.home_assistant.level.batch_delay.label"

# Temperature unit display (climate). "Auto" follows Home Assistant's own unit.
SETTING_UNIT = "unit"
SETTING_LEVEL_UNIT = f"{SETTING_LEVEL}.{SETTING_UNIT}"
LABEL_LEVEL_UNIT = "actions.home_assistant.level.unit.label"
UNIT_AUTO = "Auto"
UNIT_CELSIUS = "Celsius"
UNIT_FAHRENHEIT = "Fahrenheit"
UNIT_OPTIONS = [UNIT_AUTO, UNIT_CELSIUS, UNIT_FAHRENHEIT]
DEFAULT_UNIT = UNIT_AUTO

# Icon colors (hex)
COLOR_ON = "#ffdd00"
COLOR_OFF = "#666666"
DEFAULT_ICON = "tune"

# Customization constants
CUSTOM_ICON = "icon"
CUSTOM_COLOR = "color"

CUSTOMIZATION_WINDOW_TITLE = "actions.home_assistant.customization.level_title.label"
LABEL_LEVEL_ICON = "actions.home_assistant.level.icon.label"
LABEL_LEVEL_COLOR = "actions.home_assistant.level.color.label"

DEFAULT_ICON_COLOR = [255, 221, 0, 255]

ERROR = "error"

# Domain configurations: how to read level, set level, and toggle for each domain.
# step is always treated as percentage points (0-100), converted to native range.
DOMAIN_CONFIGS = {
    "light": {
        "level_attr": "brightness",
        "level_min": 0,
        "level_max": 255,
        "set_service": "turn_on",
        "set_param": "brightness",
        "toggle_service": "toggle",
        "fallback_icon": "lightbulb",
    },
    "fan": {
        "level_attr": "percentage",
        "level_min": 0,
        "level_max": 100,
        "set_service": "set_percentage",
        "set_param": "percentage",
        "toggle_service": "toggle",
        "fallback_icon": "fan",
    },
    "cover": {
        "level_attr": "current_position",
        "level_min": 0,
        "level_max": 100,
        "set_service": "set_cover_position",
        "set_param": "position",
        "toggle_service": "toggle",
        "fallback_icon": "window-shutter",
    },
    "media_player": {
        "level_attr": "volume_level",
        "level_min": 0.0,
        "level_max": 1.0,
        "set_service": "volume_set",
        "set_param": "volume_level",
        "toggle_service": "media_play_pause",
        "fallback_icon": "speaker",
    },
    "climate": {
        "level_attr": "temperature",      # writable target temperature
        "level_min": 7,                   # fallback if min_temp attr absent
        "level_max": 35,                  # fallback if max_temp attr absent
        "level_min_attr": "min_temp",     # read dynamic min from attributes
        "level_max_attr": "max_temp",     # read dynamic max from attributes
        "set_service": "set_temperature",
        "set_param": "temperature",
        # heat_cool / auto modes have no single setpoint — they use a low/high band.
        "range_low_attr": "target_temp_low",
        "range_high_attr": "target_temp_high",
        "range_low_param": "target_temp_low",
        "range_high_param": "target_temp_high",
        "range_states": ["heat_cool", "auto"],  # hvac states that use the band
        "is_temperature": True,                 # eligible for the °C/°F display setting
        "value_step_attr": "target_temp_step",  # quantize result to this step
        "value_step": 0.5,                # fallback step when attr absent
        "display_value": True,            # show absolute value, not percent
        "display_suffix": "°",            # appended to displayed value
        "toggle_service": None,           # no plain toggle; short press cycles fan modes
        "cycle_attr": "fan_mode",         # current selection attribute
        "cycle_options_attr": "fan_modes",  # list of selectable options
        "cycle_service": "set_fan_mode",  # service to set the selection
        "cycle_param": "fan_mode",        # param name for the service
        "fallback_icon": "thermostat",
    },
}
