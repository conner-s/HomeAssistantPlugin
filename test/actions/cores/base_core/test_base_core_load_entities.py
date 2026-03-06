import sys
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

absolute_mock_path = str(Path(__file__).parent.parent.parent.parent / "stream_controller_mock")
sys.path.insert(0, absolute_mock_path)

absolute_plugin_path = str(Path(__file__).parent.parent.parent.parent.parent.parent.absolute())
sys.path.insert(0, absolute_plugin_path)

from HomeAssistantPlugin.actions.cores.base_core.base_core import BaseCore


class TestBaseCoreLoadEntities(unittest.TestCase):

    @patch.object(BaseCore, "_create_ui_elements")
    @patch.object(BaseCore, "_create_event_assigner")
    def test_load_entities_entity_not_in_entities(self, _, __):
        domain = "light"
        entities = ["light.kitchen", "light.bedroom"]
        entity = "light.living_room"
        entities_sorted = sorted(entities + [entity])

        settings_mock = Mock()
        settings_mock.get_entity = Mock(return_value=entity)

        domain_combo_mock = Mock()
        domain_combo_mock.get_selected_item = Mock(return_value=domain)

        entity_search_entry_mock = Mock()
        entity_search_entry_mock.get_text.return_value = ""

        entity_combo_mock = Mock()
        entity_combo_mock.populate = Mock()
        entity_combo_mock.get_item_amount.return_value = 0

        instance = BaseCore(Mock(), True)
        instance.initialized = True
        instance.settings = settings_mock
        instance.domain_combo = domain_combo_mock
        instance.entity_search_entry = entity_search_entry_mock
        instance.entity_combo = entity_combo_mock
        instance._all_entities = []
        instance.plugin_base.backend.get_entities.return_value = entities
        assert entity not in entities
        instance._load_entities()

        settings_mock.get_entity.assert_called_once()
        domain_combo_mock.get_selected_item.assert_called_once()
        instance.plugin_base.backend.get_entities.assert_called_once_with(domain)
        entity_combo_mock.populate.assert_called_once_with(entities_sorted, entity, trigger_callback=False)

    @patch.object(BaseCore, "_create_ui_elements")
    @patch.object(BaseCore, "_create_event_assigner")
    def test_load_entities_success(self, _, __):
        domain = "light"
        entities = ["light.living_room", "light.kitchen", "light.bedroom"]
        entities_sorted = sorted(entities)
        entity = "light.living_room"

        settings_mock = Mock()
        settings_mock.get_entity = Mock(return_value=entity)

        domain_combo_mock = Mock()
        domain_combo_mock.get_selected_item = Mock(return_value=domain)

        entity_search_entry_mock = Mock()
        entity_search_entry_mock.get_text.return_value = ""

        entity_combo_mock = Mock()
        entity_combo_mock.populate = Mock()
        entity_combo_mock.get_item_amount.return_value = 0

        instance = BaseCore(Mock(), True)
        instance.initialized = True
        instance.settings = settings_mock
        instance.domain_combo = domain_combo_mock
        instance.entity_search_entry = entity_search_entry_mock
        instance.entity_combo = entity_combo_mock
        instance._all_entities = []
        instance.plugin_base.backend.get_entities.return_value = entities
        instance._load_entities()

        settings_mock.get_entity.assert_called_once()
        domain_combo_mock.get_selected_item.assert_called_once()
        instance.plugin_base.backend.get_entities.assert_called_once_with(domain)
        entity_combo_mock.populate.assert_called_once_with(entities_sorted, entity, trigger_callback=False)


    @patch.object(BaseCore, "_create_ui_elements")
    @patch.object(BaseCore, "_create_event_assigner")
    def test_load_entities_with_none_entity(self, _, __):
        domain = "light"
        entities = ["light.kitchen", "light.bedroom"]
        entity = None
        entities_sorted = sorted(entities)

        settings_mock = Mock()
        settings_mock.get_entity = Mock(return_value=entity)

        domain_combo_mock = Mock()
        domain_combo_mock.get_selected_item = Mock(return_value=domain)

        entity_search_entry_mock = Mock()
        entity_search_entry_mock.get_text.return_value = ""

        entity_combo_mock = Mock()
        entity_combo_mock.populate = Mock()
        entity_combo_mock.get_item_amount.return_value = 0

        instance = BaseCore(Mock(), True)
        instance.initialized = True
        instance.settings = settings_mock
        instance.domain_combo = domain_combo_mock
        instance.entity_search_entry = entity_search_entry_mock
        instance.entity_combo = entity_combo_mock
        instance._all_entities = []
        instance.plugin_base.backend.get_entities.return_value = entities
        instance._load_entities()

        entity_combo_mock.populate.assert_called_once_with(entities_sorted, entity, trigger_callback=False)

    @patch.object(BaseCore, "_create_ui_elements")
    @patch.object(BaseCore, "_create_event_assigner")
    def test_load_entities_no_update_needed(self, _, __):
        domain = "light"
        entities = ["light.bedroom", "light.kitchen", "light.living_room"]
        entity = "light.living_room"

        settings_mock = Mock()
        settings_mock.get_entity = Mock(return_value=entity)

        domain_combo_mock = Mock()
        domain_combo_mock.get_selected_item = Mock(return_value=domain)

        entity_search_entry_mock = Mock()
        entity_search_entry_mock.get_text.return_value = ""

        entity_combo_mock = Mock()
        entity_combo_mock.populate = Mock()
        entity_combo_mock.get_item_amount.return_value = 3
        entity_combo_mock.get_item_at.side_effect = ["light.bedroom", "light.kitchen", "light.living_room"]

        instance = BaseCore(Mock(), True)
        instance.initialized = True
        instance.settings = settings_mock
        instance.domain_combo = domain_combo_mock
        instance.entity_search_entry = entity_search_entry_mock
        instance.entity_combo = entity_combo_mock
        instance._all_entities = []
        instance.plugin_base.backend.get_entities.return_value = entities
        instance._load_entities()

        entity_combo_mock.populate.assert_not_called()

    @patch.object(BaseCore, "_create_ui_elements")
    @patch.object(BaseCore, "_create_event_assigner")
    def test_load_entities_with_search_filter(self, _, __):
        """Test that entity search filters entities by substring match."""
        domain = "switch"
        entities = ["switch.wyze_plug_1", "switch.wyze_light_2", "switch.bedroom_fan"]
        entity = "switch.wyze_plug_1"

        settings_mock = Mock()
        settings_mock.get_entity = Mock(return_value=entity)

        domain_combo_mock = Mock()
        domain_combo_mock.get_selected_item = Mock(return_value=domain)

        entity_search_entry_mock = Mock()
        entity_search_entry_mock.get_text.return_value = "wyze"

        entity_combo_mock = Mock()
        entity_combo_mock.populate = Mock()
        entity_combo_mock.get_item_amount.return_value = 0

        instance = BaseCore(Mock(), True)
        instance.initialized = True
        instance.settings = settings_mock
        instance.domain_combo = domain_combo_mock
        instance.entity_search_entry = entity_search_entry_mock
        instance.entity_combo = entity_combo_mock
        instance._all_entities = []
        instance.plugin_base.backend.get_entities.return_value = entities
        instance._load_entities()

        expected_filtered = sorted(["switch.wyze_plug_1", "switch.wyze_light_2"])
        entity_combo_mock.populate.assert_called_once_with(expected_filtered, entity, trigger_callback=False)

    @patch.object(BaseCore, "_create_ui_elements")
    @patch.object(BaseCore, "_create_event_assigner")
    def test_apply_entity_filter_substring_match(self, _, __):
        """Test that _apply_entity_filter uses substring (not prefix) matching."""
        entity = "switch.wyze_plug_1"

        settings_mock = Mock()
        settings_mock.get_entity = Mock(return_value=entity)

        entity_combo_mock = Mock()
        entity_combo_mock.populate = Mock()
        entity_combo_mock.get_item_amount.return_value = 0

        instance = BaseCore(Mock(), True)
        instance.initialized = True
        instance.settings = settings_mock
        instance.entity_combo = entity_combo_mock
        instance._all_entities = ["switch.wyze_plug_1", "switch.wyze_light_2", "switch.bedroom_fan"]

        instance._apply_entity_filter("plug")

        expected_filtered = ["switch.wyze_plug_1"]
        entity_combo_mock.populate.assert_called_once_with(expected_filtered, entity, trigger_callback=False)

    @patch.object(BaseCore, "_create_ui_elements")
    @patch.object(BaseCore, "_create_event_assigner")
    def test_apply_entity_filter_empty_search(self, _, __):
        """Test that empty search shows all entities."""
        entity = "switch.wyze_plug_1"

        settings_mock = Mock()
        settings_mock.get_entity = Mock(return_value=entity)

        entity_combo_mock = Mock()
        entity_combo_mock.populate = Mock()
        entity_combo_mock.get_item_amount.return_value = 0

        instance = BaseCore(Mock(), True)
        instance.initialized = True
        instance.settings = settings_mock
        instance.entity_combo = entity_combo_mock
        instance._all_entities = ["switch.bedroom_fan", "switch.wyze_light_2", "switch.wyze_plug_1"]

        instance._apply_entity_filter("")

        entity_combo_mock.populate.assert_called_once_with(
            ["switch.bedroom_fan", "switch.wyze_light_2", "switch.wyze_plug_1"],
            entity, trigger_callback=False
        )

    @patch.object(BaseCore, "_create_ui_elements")
    @patch.object(BaseCore, "_create_event_assigner")
    def test_apply_entity_filter_case_insensitive(self, _, __):
        """Test that entity search is case-insensitive."""
        entity = "switch.wyze_plug_1"

        settings_mock = Mock()
        settings_mock.get_entity = Mock(return_value=entity)

        entity_combo_mock = Mock()
        entity_combo_mock.populate = Mock()
        entity_combo_mock.get_item_amount.return_value = 0

        instance = BaseCore(Mock(), True)
        instance.initialized = True
        instance.settings = settings_mock
        instance.entity_combo = entity_combo_mock
        instance._all_entities = ["switch.wyze_plug_1", "switch.wyze_light_2", "switch.bedroom_fan"]

        instance._apply_entity_filter("WYZE")

        expected_filtered = ["switch.wyze_plug_1", "switch.wyze_light_2"]
        entity_combo_mock.populate.assert_called_once_with(expected_filtered, entity, trigger_callback=False)

    @patch.object(BaseCore, "_create_ui_elements")
    @patch.object(BaseCore, "_create_event_assigner")
    def test_on_entity_search_changed_calls_apply_filter(self, _, __):
        """Test that _on_entity_search_changed calls _apply_entity_filter."""
        instance = BaseCore(Mock(), True)
        instance.initialized = True
        instance.settings = Mock()
        instance.settings.get_entity.return_value = None

        entity_combo_mock = Mock()
        entity_combo_mock.get_item_amount.return_value = 0
        instance.entity_combo = entity_combo_mock
        instance._all_entities = ["switch.wyze_plug_1", "switch.bedroom_fan"]

        instance._on_entity_search_changed(None, "wyze", None)

        entity_combo_mock.populate.assert_called_once_with(
            ["switch.wyze_plug_1"], None, trigger_callback=False
        )
