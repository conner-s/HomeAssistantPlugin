class EntryRow:

    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs

    def get_text(self) -> str:
        return ""

    def set_value(self, value: str) -> None:
        pass

    def set_ui_value(self, value: str) -> None:
        pass

    def _value_changed(self, entry_row: 'EntryRow'):
        pass

    @property
    def widget(self):
        return self