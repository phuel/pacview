from kivy.uix.boxlayout import BoxLayout
from kivy.properties import BooleanProperty, StringProperty
from kivy.utils import escape_markup

class BreadCrumbItem():
    """Interface to be implemented by items to be added to the breadcrumb control."""
    def get_display_name(self) -> str:
        pass

class BreadCrumb(BoxLayout):
    """A breadcrumb view with a stack of clickable items and a back button."""
    item_stack = StringProperty()
    can_go_back = BooleanProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type('on_item_selected')
        self.stack = []

    def on_item_selected(self, item):
        pass

    def set_item(self, item):
        """Sets the specified item, replacing the current stack of items."""
        self.stack = [ item ]
        self._show_stack(self.stack)

    def add_item(self, item):
        """Appends the specified item to the stack of items."""
        self.stack.append(item)
        self._show_stack(self.stack)

    def back(self):
        """Remove the last item and acivate the previous, if possible."""
        if len(self.stack) > 1:
            self.stack.pop()
            self.dispatch('on_item_selected', self.stack[-1])
            self._show_stack(self.stack)

    def _on_back_ref_clicked(self, index):
        """Handler for clicks of the back button."""
        stack_index = int(index)
        if stack_index < 0 or stack_index >= len(self.stack) - 1:
            return
        self.stack = self.stack[0:stack_index+1]
        self.dispatch('on_item_selected', self.stack[-1])
        self._show_stack(self.stack)

    def _show_stack(self, stack):
        """Show the stack of items as clickable references."""
        self.item_stack = " ".join([self._make_ref(str(i), stack[i].get_display_name()) for i in range(len(stack))])
        self.can_go_back = len(stack) > 1

    @staticmethod
    def _make_ref(id, text):
        """Creates a refernce from the specified id and the text."""
        return '[u][ref={0}]{1}[/ref][/u]'.format(escape_markup(id), escape_markup(text))
