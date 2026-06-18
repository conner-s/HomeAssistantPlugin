import sys
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

absolute_mock_path = str(Path(__file__).parent.parent.parent / "stream_controller_mock")
sys.path.insert(0, absolute_mock_path)

absolute_plugin_path = str(Path(__file__).parent.parent.parent.parent.parent.absolute())
sys.path.insert(0, absolute_plugin_path)

from HomeAssistantPlugin.actions.level_dial.level_dial import LevelDial


class TestLevelDialAdjustLevel(unittest.TestCase):

    def _make_instance(self, _, entity, step, state, batch_delay=0, unit="Auto"):
        """Helper to create a LevelDial with mocked dependencies."""
        settings_mock = Mock()
        settings_mock.get_entity = Mock(return_value=entity)
        settings_mock.get_step = Mock(return_value=step)
        settings_mock.get_batch_delay = Mock(return_value=batch_delay)
        settings_mock.get_unit = Mock(return_value=unit)

        backend_mock = Mock()
        backend_mock.get_entity = Mock(return_value=state)
        backend_mock.perform_action = Mock()

        plugin_base_mock = Mock()
        plugin_base_mock.backend = backend_mock

        instance = LevelDial()
        instance.initialized = True
        instance.settings = settings_mock
        instance.plugin_base = plugin_base_mock
        instance.set_center_label = Mock()
        return instance, backend_mock

    @patch('HomeAssistantPlugin.actions.level_dial.level_dial.CustomizationCore.__init__')
    def test_adjust_level_no_entity(self, _):
        settings_mock = Mock()
        settings_mock.get_entity = Mock(return_value="")

        backend_mock = Mock()
        plugin_base_mock = Mock()
        plugin_base_mock.backend = backend_mock

        instance = LevelDial()
        instance.initialized = True
        instance.settings = settings_mock
        instance.plugin_base = plugin_base_mock
        instance._adjust_level(1)

        backend_mock.get_entity.assert_not_called()
        backend_mock.perform_action.assert_not_called()

    @patch('HomeAssistantPlugin.actions.level_dial.level_dial.CustomizationCore.__init__')
    def test_adjust_level_unsupported_domain(self, _):
        settings_mock = Mock()
        settings_mock.get_entity = Mock(return_value="switch.kitchen")

        backend_mock = Mock()
        backend_mock.perform_action = Mock()
        plugin_base_mock = Mock()
        plugin_base_mock.backend = backend_mock

        instance = LevelDial()
        instance.initialized = True
        instance.settings = settings_mock
        instance.plugin_base = plugin_base_mock
        instance._adjust_level(1)

        backend_mock.perform_action.assert_not_called()

    @patch('HomeAssistantPlugin.actions.level_dial.level_dial.CustomizationCore.__init__')
    def test_adjust_level_no_state(self, _):
        settings_mock = Mock()
        settings_mock.get_entity = Mock(return_value="light.desk")
        settings_mock.get_step = Mock(return_value=10)

        backend_mock = Mock()
        backend_mock.get_entity = Mock(return_value=None)
        backend_mock.perform_action = Mock()
        plugin_base_mock = Mock()
        plugin_base_mock.backend = backend_mock

        instance = LevelDial()
        instance.initialized = True
        instance.settings = settings_mock
        instance.plugin_base = plugin_base_mock
        instance._adjust_level(1)

        backend_mock.perform_action.assert_not_called()

    @patch('HomeAssistantPlugin.actions.level_dial.level_dial.CustomizationCore.__init__')
    def test_adjust_level_light_cw_mid_range(self, mock_init):
        """Light at 50% brightness (128), step 10 CW -> ~60% (154)."""
        instance, backend = self._make_instance(
            mock_init,
            entity="light.desk",
            step=10,
            state={"attributes": {"brightness": 128}}
        )

        instance._adjust_level(1)

        backend.perform_action.assert_called_once()
        args = backend.perform_action.call_args
        self.assertEqual(args[0][0], "light")
        self.assertEqual(args[0][1], "turn_on")
        self.assertEqual(args[0][2], "light.desk")
        new_brightness = args[0][3]["brightness"]
        # 128 + (10/100 * 255) = 128 + 25.5 = 153.5 -> round to 154
        self.assertEqual(new_brightness, 154)

    @patch('HomeAssistantPlugin.actions.level_dial.level_dial.CustomizationCore.__init__')
    def test_adjust_level_light_ccw_mid_range(self, mock_init):
        """Light at 50% brightness (128), step 10 CCW -> ~40% (102)."""
        instance, backend = self._make_instance(
            mock_init,
            entity="light.desk",
            step=10,
            state={"attributes": {"brightness": 128}}
        )

        instance._adjust_level(-1)

        backend.perform_action.assert_called_once()
        new_brightness = backend.perform_action.call_args[0][3]["brightness"]
        # 128 - 25.5 = 102.5 -> round to 102
        self.assertEqual(new_brightness, 102)

    @patch('HomeAssistantPlugin.actions.level_dial.level_dial.CustomizationCore.__init__')
    def test_adjust_level_light_clamps_to_max(self, mock_init):
        """Light near max, step pushes above 255 -> clamped to 255."""
        instance, backend = self._make_instance(
            mock_init,
            entity="light.desk",
            step=10,
            state={"attributes": {"brightness": 250}}
        )

        instance._adjust_level(1)

        backend.perform_action.assert_called_once()
        new_brightness = backend.perform_action.call_args[0][3]["brightness"]
        self.assertEqual(new_brightness, 255)

    @patch('HomeAssistantPlugin.actions.level_dial.level_dial.CustomizationCore.__init__')
    def test_adjust_level_light_clamps_to_floor(self, mock_init):
        """Light at low brightness, step down clamps to 1% floor (not 0)."""
        instance, backend = self._make_instance(
            mock_init,
            entity="light.desk",
            step=10,
            state={"attributes": {"brightness": 5}}
        )

        instance._adjust_level(-1)

        backend.perform_action.assert_called_once()
        new_brightness = backend.perform_action.call_args[0][3]["brightness"]
        # floor = 0 + 255 * 0.01 = 2.55 -> round to 3
        self.assertEqual(new_brightness, 3)

    @patch('HomeAssistantPlugin.actions.level_dial.level_dial.CustomizationCore.__init__')
    def test_adjust_level_fine_grained_at_low_brightness(self, mock_init):
        """At <= 10%, step is reduced to 1% for fine control."""
        # 25/255 ≈ 9.8%, which is <= 10%, so effective_step = 1
        instance, backend = self._make_instance(
            mock_init,
            entity="light.desk",
            step=10,
            state={"attributes": {"brightness": 25}}
        )

        instance._adjust_level(1)

        backend.perform_action.assert_called_once()
        new_brightness = backend.perform_action.call_args[0][3]["brightness"]
        # native_step = 1/100 * 255 = 2.55, 25 + 2.55 = 27.55 -> round to 28
        self.assertEqual(new_brightness, 28)

    @patch('HomeAssistantPlugin.actions.level_dial.level_dial.CustomizationCore.__init__')
    def test_adjust_level_fine_grained_crossing_into_low(self, mock_init):
        """Stepping down from above 10% into the sub-10% zone uses 1% step."""
        # 28/255 ≈ 10.98%, but pct_after = 10.98 + (10 * -1) = 0.98 < 10
        # so effective_step = 1
        instance, backend = self._make_instance(
            mock_init,
            entity="light.desk",
            step=10,
            state={"attributes": {"brightness": 28}}
        )

        instance._adjust_level(-1)

        backend.perform_action.assert_called_once()
        new_brightness = backend.perform_action.call_args[0][3]["brightness"]
        # native_step = 1/100 * 255 = 2.55, 28 - 2.55 = 25.45 -> round to 25
        self.assertEqual(new_brightness, 25)

    @patch('HomeAssistantPlugin.actions.level_dial.level_dial.CustomizationCore.__init__')
    def test_adjust_level_fan_percentage(self, mock_init):
        """Fan domain uses percentage 0-100, step 10 CW from 50%."""
        instance, backend = self._make_instance(
            mock_init,
            entity="fan.bedroom",
            step=10,
            state={"attributes": {"percentage": 50}}
        )

        instance._adjust_level(1)

        backend.perform_action.assert_called_once()
        args = backend.perform_action.call_args[0]
        self.assertEqual(args[0], "fan")
        self.assertEqual(args[1], "set_percentage")
        self.assertEqual(args[2], "fan.bedroom")
        self.assertEqual(args[3]["percentage"], 60)

    @patch('HomeAssistantPlugin.actions.level_dial.level_dial.CustomizationCore.__init__')
    def test_adjust_level_media_player_volume(self, mock_init):
        """Media player uses volume_level 0.0-1.0."""
        instance, backend = self._make_instance(
            mock_init,
            entity="media_player.speaker",
            step=10,
            state={"attributes": {"volume_level": 0.5}}
        )

        instance._adjust_level(1)

        backend.perform_action.assert_called_once()
        args = backend.perform_action.call_args[0]
        self.assertEqual(args[0], "media_player")
        self.assertEqual(args[1], "volume_set")
        self.assertEqual(args[2], "media_player.speaker")
        # 0.5 + 0.1 = 0.6 (float, not rounded to int since level_max is float)
        self.assertAlmostEqual(args[3]["volume_level"], 0.6, places=5)

    @patch('HomeAssistantPlugin.actions.level_dial.level_dial.CustomizationCore.__init__')
    def test_adjust_level_cover_position(self, mock_init):
        """Cover domain uses position 0-100."""
        instance, backend = self._make_instance(
            mock_init,
            entity="cover.garage",
            step=10,
            state={"attributes": {"current_position": 70}}
        )

        instance._adjust_level(-1)

        backend.perform_action.assert_called_once()
        args = backend.perform_action.call_args[0]
        self.assertEqual(args[0], "cover")
        self.assertEqual(args[1], "set_cover_position")
        self.assertEqual(args[2], "cover.garage")
        self.assertEqual(args[3]["position"], 60)

    @patch('HomeAssistantPlugin.actions.level_dial.level_dial.CustomizationCore.__init__')
    def test_adjust_level_climate_cw(self, mock_init):
        """Climate adjusts target temperature using dynamic min/max from attributes."""
        instance, backend = self._make_instance(
            mock_init,
            entity="climate.living_room",
            step=10,
            state={"state": "heat", "attributes": {
                "temperature": 21, "min_temp": 7, "max_temp": 35, "target_temp_step": 0.5
            }}
        )

        instance._adjust_level(1)

        backend.perform_action.assert_called_once()
        args = backend.perform_action.call_args[0]
        self.assertEqual(args[0], "climate")
        self.assertEqual(args[1], "set_temperature")
        self.assertEqual(args[2], "climate.living_room")
        # 21 is 50% of 7..35; +10% -> 60% -> 7 + 0.6*28 = 23.8 -> snap to 0.5 -> 24.0
        self.assertEqual(args[3]["temperature"], 24.0)

    @patch('HomeAssistantPlugin.actions.level_dial.level_dial.CustomizationCore.__init__')
    def test_adjust_level_climate_ccw(self, mock_init):
        """Climate CCW lowers the target temperature."""
        instance, backend = self._make_instance(
            mock_init,
            entity="climate.living_room",
            step=10,
            state={"state": "heat", "attributes": {
                "temperature": 21, "min_temp": 7, "max_temp": 35, "target_temp_step": 0.5
            }}
        )

        instance._adjust_level(-1)

        backend.perform_action.assert_called_once()
        # 50% -10% -> 40% -> 7 + 0.4*28 = 18.2 -> snap to 0.5 -> 18.0
        self.assertEqual(backend.perform_action.call_args[0][3]["temperature"], 18.0)

    @patch('HomeAssistantPlugin.actions.level_dial.level_dial.CustomizationCore.__init__')
    def test_adjust_level_climate_dynamic_range(self, mock_init):
        """Per-entity min_temp/max_temp override the static config defaults."""
        instance, backend = self._make_instance(
            mock_init,
            entity="climate.bedroom",
            step=10,
            state={"state": "heat", "attributes": {
                "temperature": 20, "min_temp": 10, "max_temp": 30, "target_temp_step": 1
            }}
        )

        instance._adjust_level(1)

        backend.perform_action.assert_called_once()
        # 20 is 50% of 10..30; +10% -> 60% -> 10 + 0.6*20 = 22.0 -> snap to 1 -> 22.0
        self.assertEqual(backend.perform_action.call_args[0][3]["temperature"], 22.0)

    @patch('HomeAssistantPlugin.actions.level_dial.level_dial.CustomizationCore.__init__')
    def test_adjust_level_climate_step_fallback(self, mock_init):
        """When target_temp_step is absent, the config's value_step (0.5) is used."""
        instance, backend = self._make_instance(
            mock_init,
            entity="climate.living_room",
            step=10,
            state={"state": "heat", "attributes": {
                "temperature": 21, "min_temp": 7, "max_temp": 35
            }}
        )

        instance._adjust_level(1)

        backend.perform_action.assert_called_once()
        # 23.8 snapped to the 0.5 fallback step -> 24.0 (a multiple of 0.5)
        temperature = backend.perform_action.call_args[0][3]["temperature"]
        self.assertEqual(temperature, 24.0)
        self.assertEqual(temperature % 0.5, 0)

    @patch('HomeAssistantPlugin.actions.level_dial.level_dial.CustomizationCore.__init__')
    def test_adjust_level_climate_heat_cool_shifts_band_cw(self, mock_init):
        """heat_cool mode (no single setpoint) shifts the low/high band together."""
        instance, backend = self._make_instance(
            mock_init,
            entity="climate.living_room",
            step=10,
            state={"state": "heat_cool", "attributes": {
                "target_temp_low": 18, "target_temp_high": 24,
                "min_temp": 7, "max_temp": 35, "target_temp_step": 0.5,
            }}
        )

        instance._adjust_level(1)

        backend.perform_action.assert_called_once()
        args = backend.perform_action.call_args[0]
        self.assertEqual(args[0], "climate")
        self.assertEqual(args[1], "set_temperature")
        # midpoint 21 (50%) +10% -> 60% -> mid 23.8; band spread 6 preserved, snapped to 0.5
        self.assertEqual(args[3], {"target_temp_low": 21.0, "target_temp_high": 27.0})

    @patch('HomeAssistantPlugin.actions.level_dial.level_dial.CustomizationCore.__init__')
    def test_adjust_level_climate_heat_cool_shifts_band_ccw(self, mock_init):
        """heat_cool CCW lowers the whole band, keeping its spread."""
        instance, backend = self._make_instance(
            mock_init,
            entity="climate.living_room",
            step=10,
            state={"state": "heat_cool", "attributes": {
                "target_temp_low": 18, "target_temp_high": 24,
                "min_temp": 7, "max_temp": 35, "target_temp_step": 0.5,
            }}
        )

        instance._adjust_level(-1)

        backend.perform_action.assert_called_once()
        # midpoint 21 (50%) -10% -> 40% -> mid 18.2; spread 6 -> 15.0 / 21.0
        self.assertEqual(
            backend.perform_action.call_args[0][3],
            {"target_temp_low": 15.0, "target_temp_high": 21.0}
        )

    @patch('HomeAssistantPlugin.actions.level_dial.level_dial.CustomizationCore.__init__')
    def test_adjust_level_heat_cool_band_when_temperature_also_reported(self, mock_init):
        """heat_cool state uses the band even if a stale 'temperature' is also present."""
        instance, backend = self._make_instance(
            mock_init,
            entity="climate.living_room",
            step=10,
            state={"state": "heat_cool", "attributes": {
                "temperature": 21,  # stale single value some integrations still report
                "target_temp_low": 18, "target_temp_high": 24,
                "min_temp": 7, "max_temp": 35, "target_temp_step": 0.5,
            }}
        )

        instance._adjust_level(1)

        backend.perform_action.assert_called_once()
        # Must send the band, NOT {"temperature": ...} which HA ignores in heat_cool
        self.assertEqual(
            backend.perform_action.call_args[0][3],
            {"target_temp_low": 21.0, "target_temp_high": 27.0}
        )

    @patch('HomeAssistantPlugin.actions.level_dial.level_dial.CustomizationCore.__init__')
    def test_adjust_level_climate_fahrenheit_display(self, mock_init):
        """With unit=Fahrenheit the label converts °C→°F; the HA value stays native (°C)."""
        instance, backend = self._make_instance(
            mock_init,
            entity="climate.living_room",
            step=10,
            state={"state": "heat", "attributes": {
                "temperature": 21, "min_temp": 7, "max_temp": 35, "target_temp_step": 0.5,
            }},
            unit="Fahrenheit",
        )

        instance._adjust_level(1)

        # HA still receives the native Celsius value
        self.assertEqual(backend.perform_action.call_args[0][3], {"temperature": 24.0})
        # But the dial shows Fahrenheit: 24.0°C -> 75.2°F
        label = instance.set_center_label.call_args[0][0]
        self.assertEqual(label, "75.2°F")

    @patch('HomeAssistantPlugin.actions.level_dial.level_dial.CustomizationCore.__init__')
    def test_adjust_level_brightness_none_treated_as_zero(self, mock_init):
        """When brightness attr is None, it's treated as 0."""
        instance, backend = self._make_instance(
            mock_init,
            entity="light.desk",
            step=10,
            state={"attributes": {"brightness": None}}
        )

        instance._adjust_level(1)

        backend.perform_action.assert_called_once()
        new_brightness = backend.perform_action.call_args[0][3]["brightness"]
        # current=0 (None -> 0), pct_now=0 <= 10 so effective_step=1
        # native_step = 1/100 * 255 = 2.55, 0 + 2.55 = 2.55 -> round to 3
        # but floor = 2.55, max(2.55, 2.55) = 2.55 -> round to 3
        self.assertEqual(new_brightness, 3)

    @patch('HomeAssistantPlugin.actions.level_dial.level_dial.CustomizationCore.__init__')
    def test_adjust_level_integer_range_rounds(self, mock_init):
        """Integer-range domains (light, fan, cover) produce rounded integer values."""
        instance, backend = self._make_instance(
            mock_init,
            entity="light.desk",
            step=7,
            state={"attributes": {"brightness": 100}}
        )

        instance._adjust_level(1)

        backend.perform_action.assert_called_once()
        new_brightness = backend.perform_action.call_args[0][3]["brightness"]
        self.assertIsInstance(new_brightness, int)

    @patch('HomeAssistantPlugin.actions.level_dial.level_dial.CustomizationCore.__init__')
    def test_adjust_level_rapid_ticks_accumulate(self, mock_init):
        """Rapid CW ticks accumulate via _pending_level instead of re-reading stale state."""
        instance, backend = self._make_instance(
            mock_init,
            entity="light.desk",
            step=10,
            state={"attributes": {"brightness": 128}},
            batch_delay=0
        )

        # Simulate 3 rapid CW ticks — HA state stays at 128 (stale)
        instance._adjust_level(1)
        instance._adjust_level(1)
        instance._adjust_level(1)

        # batch_delay=0 fires immediately, so 3 commands
        self.assertEqual(backend.perform_action.call_count, 3)
        # Each tick should build on the previous pending pct, not re-read 128
        calls = backend.perform_action.call_args_list
        b1 = calls[0][0][3]["brightness"]
        b2 = calls[1][0][3]["brightness"]
        b3 = calls[2][0][3]["brightness"]
        # 128/255=50.2%, +10=60.2% -> round(60.2/100*255)=154
        self.assertEqual(b1, 154)
        # 60.2%+10=70.2% -> round(70.2/100*255)=179
        self.assertEqual(b2, 179)
        # 70.2%+10=80.2% -> round(80.2/100*255)=204
        self.assertEqual(b3, 204)

    @patch('HomeAssistantPlugin.actions.level_dial.level_dial.CustomizationCore.__init__')
    def test_adjust_level_batch_delay_debounces(self, mock_init):
        """With batch_delay > 0, rapid ticks only send the final command."""
        instance, backend = self._make_instance(
            mock_init,
            entity="light.desk",
            step=10,
            state={"attributes": {"brightness": 128}},
            batch_delay=150
        )

        instance._adjust_level(1)
        instance._adjust_level(1)
        instance._adjust_level(1)

        # No command sent yet — timer is pending
        backend.perform_action.assert_not_called()
        # Display was updated immediately each tick
        self.assertEqual(instance.set_center_label.call_count, 3)

        # Simulate timer firing
        instance._send_pending_command()

        # Only one command sent — with the final accumulated value
        backend.perform_action.assert_called_once()
        new_brightness = backend.perform_action.call_args[0][3]["brightness"]
        # 50.2% +10+10+10 = 80.2% -> round(80.2/100*255) = 204
        self.assertEqual(new_brightness, 204)

    @patch('HomeAssistantPlugin.actions.level_dial.level_dial.CustomizationCore.__init__')
    def test_adjust_level_display_updates_immediately(self, mock_init):
        """set_center_label is called on every tick regardless of batch_delay."""
        instance, backend = self._make_instance(
            mock_init,
            entity="light.desk",
            step=10,
            state={"attributes": {"brightness": 128}},
            batch_delay=150
        )

        instance._adjust_level(1)

        # Display updated immediately
        instance.set_center_label.assert_called_once_with(
            "60%", color=[255, 255, 255], font_size=28,
            outline_width=3, outline_color=[0, 0, 0]
        )
        # But no HA command yet
        backend.perform_action.assert_not_called()

    @patch.object(LevelDial, 'set_enabled_disabled')
    @patch.object(LevelDial, '_load_customizations')
    @patch('HomeAssistantPlugin.actions.level_dial.level_dial.CustomizationCore.__init__')
    def test_adjust_level_refresh_clears_pending(self, mock_init, _load_cust, _set_ed):
        """refresh() clears _pending_level so next tick re-syncs from HA state."""
        instance, backend = self._make_instance(
            mock_init,
            entity="light.desk",
            step=10,
            state={"attributes": {"brightness": 128}}
        )

        instance._adjust_level(1)
        self.assertIsNotNone(instance._pending_pct)

        # With batch_delay=0, _send_pending_command fires immediately,
        # clearing _batch_timer, so refresh() won't skip.
        instance.initialized = True
        instance.settings = Mock()
        instance.settings.get_entity = Mock(return_value="light.desk")
        instance.settings.get_label = Mock(return_value="Desk")
        instance.settings.get_customizations = Mock(return_value=[])
        instance.set_top_label = Mock()
        instance.set_center_label = Mock()
        instance.set_media = Mock()
        instance.refresh(state={"state": "on", "attributes": {"brightness": 154, "friendly_name": "Desk"}})

        self.assertIsNone(instance._pending_pct)
