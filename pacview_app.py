import subprocess
import json

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.logger import Logger
from kivy.properties import BooleanProperty, ColorProperty, DictProperty, ListProperty, ObjectProperty, StringProperty
from kivy.uix.behaviors.focus import FocusBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior

from apprecycleview import AppRecycleView
from dialog import YesNoDialog, TerminalDialog
from pacviewmodel import PackageViewModel
from breadcrumb import BreadCrumbItem

class PackageItem(BreadCrumbItem):
    def __init__(self, package):
        self.package = package

    def get_display_name(self):
        return self.package['Name']

class WrapDescriptionRow(BoxLayout):
    pkg_data = ObjectProperty()
    desc = StringProperty()
    data = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type('on_ref_clicked')

    def on_ref_clicked(self, ref_id):
        pass

    def ref_clicked(self, ref_id):
        self.dispatch('on_ref_clicked', ref_id)

    def reset(self):
        self.pkg_data.reset()

class PackageView(BoxLayout):
    """A view that displays the details for the selected package."""
    package = DictProperty()
    highlight_labels = ListProperty()
    breadcrumb = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.package = PackageViewModel({}).to_dict()
        self.register_event_type('on_package_clicked')
        self.register_event_type('on_url_clicked')
        Clock.schedule_once(self._wire, 0)

    def _wire(self, _):
        self.breadcrumb.bind(on_item_selected=lambda _, pkg: self.show_package(pkg.package))

    def set_package(self, db_package, reset_stack):
        self.show_package(PackageViewModel(db_package).to_dict())
        if reset_stack:
            self.breadcrumb.set_item(PackageItem(self.package))
        else:
            self.breadcrumb.add_item(PackageItem(self.package))

    def show_package(self, package):
        self.package = package
        for label in self.highlight_labels:
            label.reset()

    def on_ref_clicked(self, prop, ref_id):
        if prop in ['DependsOn', 'RequiredBy', 'InstalledOptions', 'UninstalledOptions']:
            self.dispatch('on_package_clicked', ref_id)
        elif prop == 'URL': 
            self.dispatch('on_url_clicked', ref_id)

    def on_package_clicked(self, package_name):
        pass

    def on_url_clicked(self, url):
        pass

    def on_touch_down(self, touch):
        if touch.button == 'mouse5':
            self.breadcrumb.back()
        super().on_touch_down(touch)

    def on_key_down(self, keycode):
        if keycode[1] == 'backspace':
            self.breadcrumb.back()


class PackageListItem(RecycleDataViewBehavior, BoxLayout):
    """The individual entry in the package list."""
    selected = BooleanProperty()
    selectable = BooleanProperty()
    Name = StringProperty()
    Version = StringProperty()
    background_color = ColorProperty() 

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        self.data = data
        if index % 2 == 0:
            self.background_color = (0,0,0,1)
        else:
            self.background_color = (0.15,0.15,0.15,1)
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super().on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        if is_selected:
            rv.select(index)


class SelectableRecycleBoxLayout(LayoutSelectionBehavior,
                                 RecycleBoxLayout):
    ''' Adds selection behaviour to the view. '''


class PackageListView(FocusBehavior,AppRecycleView):
    """The list of packages."""
    title = StringProperty()
    child_layout = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.viewmodel = None
        self.layout = None
        self.filter_text = None
        self.selected_index = None

    def set_viewmodel(self, layout, viewmodel):
        self.layout = layout
        self.viewmodel = viewmodel
        self.packages = list(viewmodel.get_list())
        self.filter_packages(self.filter_text)
        if self.selected_index is not None:
            layout = self.children[0]
            layout.deselect_node(self.selected_index)
            self.selected_index = None
            self.layout.select(None)

    def select(self, index):
        self.selected_index = index
        self.layout.select(self.data[index])

    def move_selection(self, delta):
        if self.selected_index is None:
            return
        new_index = self.selected_index + delta
        if new_index < 0 or new_index >= len(self.data):
            return
        self.select(new_index)
        self.child_layout.select_node(new_index)
        self.scroll_to_index(new_index)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if keycode[1] == 'up':
            self.move_selection(-1)
        elif keycode[1] == 'down':
            self.move_selection(1)

    def filter_packages(self, text):
        self.filter_text = text
        if text is None:
            self.data = self.packages
        else:
            self.data = [pkg for pkg in self.packages if text in pkg['Name']]
        self.title = "{0} packages".format(len(self.data))


class PacView(FocusBehavior,BoxLayout):
    """The main view."""
    listview = ObjectProperty()
    view_selector = ObjectProperty()
    selected_package = ObjectProperty()
    filter_textbox = ObjectProperty()
    can_delete = BooleanProperty(False)

    def __init__(self, viewmodel, **kwargs):
        super().__init__(**kwargs)
        self.__viewmodel = viewmodel
        self.__list_viewmodel = None
        self.__package = None
        self.__popup = None
        self.__selection = None
        self.filter_textbox.bind(text=lambda _,text: self.on_filter_text(text))
        self.view_selector.bind(text=lambda _,text: self.select_package_list(text))
        self.selected_package.bind(on_package_clicked=self.package_clicked)
        self.selected_package.bind(on_url_clicked=self.url_clicked)
        self.view_selector.text = 'Explicit'

    def select_package_list(self, selection):
        self.__selection = selection
        if selection == 'Explicit':
            self.__list_viewmodel = self.__viewmodel.get_installed()
        elif selection == 'All':
            self.__list_viewmodel = self.__viewmodel.get_all()
        elif selection == 'Obsolete':
            self.__list_viewmodel = self.__viewmodel.get_obsolete()
        elif selection == 'Not Required':
            self.__list_viewmodel = self.__viewmodel.get_not_required()
        self.listview.set_viewmodel(self, self.__list_viewmodel)

    def select(self, package, reset_stack = True):
        self.__package = package
        self.selected_package.set_package(package, reset_stack)
        self.can_delete = self.__viewmodel.can_delete_package(package)

    def package_clicked(self, _, package_name):
        package = self.__list_viewmodel.get_package(package_name)
        if package is not None:
            self.select(package, False)
        return True

    def url_clicked(self, _, __):
        try:
            url = self.__package['URL']
            subprocess.Popen(['xdg-open', url])
        except OSError:
            Logger.warn('pacview: could not open url: ' + url)
        return True

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if keycode[1] == 'up':
            self.listview.move_selection(-1)
        elif keycode[1] == 'down':
            self.listview.move_selection(1)
        else:
            self.selected_package.on_key_down(keycode)

    def on_filter_text(self, text):
        self.listview.filter_packages(text)

    def delete_selected_package(self):
        Logger.info("pacview: Uninstall {0}".format(self.__package['Name']))
        if not self.__viewmodel.can_delete_package(self.__package):
            return
        name = self.__package['Name']
        dependent = self.__viewmodel.get_dependent(name)
        if len(dependent) > 0:
            question = "Uninstall the selected package '[b]{0}[/b]' and its depedents [b]{1}[/b] ?".format(name, ", ".join(dependent))
        else:
            question = "Uninstall the selected package '[b]{0}[/b]' ?".format(name)
        dependent.append(name)
        content = YesNoDialog(question=question, yes=lambda : self.__delete_package(dependent), no=self.__dismiss_popup)
        self.__popup = Popup(title="Delete Package", content=content, size_hint=(0.8, 0.8))
        self.__popup.open()

    def __delete_package(self, packages):
        self.__dismiss_popup()
        text = self.__viewmodel.delete_package(packages)
        content = TerminalDialog(text=text[0] + "\n\n" + text[1], close=self.__dismiss_popup)
        self.__popup = Popup(title="Result", content=content, size_hint=(0.8, 0.8))
        self.__popup.open()
        self.select_package_list(self.__selection)

    def __dismiss_popup(self):
        self.__popup.dismiss()


class PacViewApp(App):
    def __init__(self, settings, viewmodel, **kwargs):
        self.__settings = settings
        self.__viewmodel = viewmodel
        super().__init__(**kwargs)
        self.icon = 'img/arch_icon.png'

    def build(self):
        view = PacView(self.__viewmodel)
        if self.__viewmodel.database.remote is not None:
            Clock.schedule_once(lambda _: Window.set_title('PacView - ' + self.__viewmodel.database.remote))
        return view

    def on_stop(self):
        self.__settings.set_window_settings({
            'left': Window.left,
            'top': Window.top,
            'width': Window.width,
            'height': Window.height
        })
