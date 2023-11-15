"""
Module: Kivy popup widgets for the app
Program: Particle Deformation Analysis
Author: Haig Bishop (hbi34@uclive.ac.nz)
"""

# Kivy imports
from kivy.app import App
from kivy.uix.popup import Popup


class BackPopup(Popup):
    """A custom Popup object for going back a page"""

    def __init__(self, screen, **kwargs):
        """init method for BackPopup"""
        # The screen this popup will direct to
        self.screen = screen
        # Call Popup init method
        super(BackPopup, self).__init__(**kwargs)

    def on_answer(self, answer):
        """called when user presses 'yes' or 'no'"""
        # If they said "yes go back"
        if answer == "yes":
            # Get app object
            app = App.get_running_app()
            # Empty the job list
            app.clear_experiments()
            # Change screen
            app.root.current = self.screen
            app.root.transition.direction = "right"
            # Close popup
            self.dismiss()
        # If they said "no cancel"
        else:
            # Close popup
            self.dismiss()
