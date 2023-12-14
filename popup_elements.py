"""
Module: Kivy popup widgets for the app
Program: Particle Deformation Analysis
Author: Haig Bishop (hbi34@uclive.ac.nz)
"""

# Kivy imports
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.floatlayout import FloatLayout


class BackPopup(Popup):
    """A custom Popup object for going back a page"""

    def __init__(self, screen_id, **kwargs):
        """init method for BackPopup"""
        # The screen this popup will direct to
        self.screen_id = screen_id
        # Call Popup init method
        super(BackPopup, self).__init__(**kwargs)

    def on_answer(self, answer):
        """called when user presses 'yes' or 'no'"""
        # If they said "yes go back"
        if answer == "yes":
            # Get app object
            app = App.get_running_app()
            # Empty the job list for IE3 (boxes only if not going to main)
            going_to_main = self.screen_id == 'main'
            app.clear_experiments(boxes_only=not going_to_main)
            # Change screen
            app.root.current = self.screen_id
            app.root.transition.direction = "right"
            # Deselect experiments
            app.deselect_all_experiments()
            # Update the current screen if not going to main
            if not going_to_main:
                app.root.get_screen(app.root.current).update_fields()
            # Close popup
            self.dismiss()
        # If they said "no cancel"
        else:
            # Close popup
            self.dismiss()


class ErrorPopup(Popup):
    """A custom Popup object for displaying an error screen
    - this is just for invalid data
    - the popup doesnt do anything, it just tells the user something"""

    def on_answer(self, answer):
        """called when user presses 'ok'"""
        if answer == "ok":
            # Close popup
            self.dismiss()
