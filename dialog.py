from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout

class YesNoDialog(BoxLayout):
    question = StringProperty()
    yes = ObjectProperty(None)
    no = ObjectProperty(None)

class TerminalDialog(BoxLayout):
    """Dialog to display text in a similar way as a teminal window."""
    text = StringProperty()
    close = ObjectProperty()