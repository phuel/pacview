from kivy.properties import ColorProperty
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.lang import Builder
from kivy.core.window import Window

# From: https://gist.github.com/terminak/ef3c34922a1fced048b1db8e0ec6837b

class HighlightLabel(Label):
    highlight_color = ColorProperty()

    def __init__(self, **kwargs):
        super(HighlightLabel, self).__init__(**kwargs)
        self.register_event_type('on_ref_clicked')
        Window.bind(mouse_pos=self.on_mouse_pos)
        self._instructions = []
        self._highlighted = None

    def on_touch_up(self, touch):
        pos = touch.pos
        if self.collide_point(*pos):
            tx, ty = pos
            tx -= self.center_x - self.texture_size[0] / 2.
            ty -= self.center_y - self.texture_size[1] / 2.
            ty = self.texture_size[1] - ty
            for uid, zones in self.refs.items():
                for zone in zones:
                    x, y, w, h = zone
                    if x <= tx <= w and y <= ty <= h:
                        self.ref_clicked(uid)
                        return True
        return super().on_touch_up(touch)

    def ref_clicked(self, uid):
        self.dispatch('on_ref_clicked', uid)

    def on_ref_clicked(self, ref_id):
        pass

    def reset(self):
        self._clear_instructions()

    def on_mouse_pos(self, *largs):
        pos = self.to_widget(*largs[1])
        if self.collide_point(*pos):
            tx, ty = pos
            tx -= self.center_x - self.texture_size[0] / 2.
            ty -= self.center_y - self.texture_size[1] / 2.
            ty = self.texture_size[1] - ty
            for uid, zones in self.refs.items():
                for zone in zones:
                    x, y, w, h = zone
                    if x <= tx <= w and y <= ty <= h:
                        self._highlight_ref(uid)
                        return
        if self._instructions:
            self._clear_instructions()
        
    def _highlight_ref(self, name):
        if self._highlighted == name:
            return
        if self._instructions:
            self._clear_instructions()
        self._highlighted = name
        store = self._instructions.append
        with self.canvas.before:
            store(Color(*self.highlight_color))

        for box in self.refs[name]:
            box_x = self.center_x - self.texture_size[0] * 0.5 + box[0]
            box_y = self.center_y + self.texture_size[1] * 0.5 - box[1]
            box_w = box[2] - box[0]
            box_h = box[1] - box[3]
            with self.canvas.before:
                store(Rectangle(
                    pos=(box_x, box_y), size=(box_w, box_h)))

    def _clear_instructions(self):
        rm = self.canvas.before.remove
        for instr in self._instructions:
            rm(instr)
        self._instructions = []
        self._highlighted = None
