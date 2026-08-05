# App wrapper to enable Asteroids to run on the Tildagon using my hardware
# abstraction framework and hardware independant game code.
#
# Copyright (c) 2026 Paul Fretwell - aka 'Footleg'
#
# Released under the [GPL-3.0 License](https://opensource.org/license/gpl-3.0).

import app
from apps.Footleg_tildagon_asteroids.tildagon_wrapper import Hardware_Wrapper
from apps.Footleg_tildagon_asteroids.asteroids import AsteroidsGame
from events.input import Buttons, BUTTON_TYPES
from app_components import clear_background

class AsteroidsApp(app.App):
    def __init__(self):
        self.first_draw = True
        self.button_states = Buttons(self)

        # Create the display device (hardware)
        display = Hardware_Wrapper()

        # Create the app instance with the display
        self.myapp = AsteroidsGame(display)

        # Initialize the app
        self.myapp.initialize()

    def update(self, delta):
        if self.button_states.get(BUTTON_TYPES["CANCEL"]):
            self.minimise()
        else:
            self.myapp.display.setBtnStates(self.button_states)
            self.myapp.update()

    def draw(self, ctx):
        if self.first_draw:
            ctx.font = ctx.get_font_name(0)
            ctx.font_size = 6
            self.first_draw = False
        if self.myapp.game_mode == 2:
            ctx.gray(0.0)
            ctx.rectangle(-120, -120, 240, 240).fill()
        self.myapp.display.drawFromCaches(ctx)
        
__app_export__ = AsteroidsApp