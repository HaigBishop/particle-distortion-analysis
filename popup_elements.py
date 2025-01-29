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

    def __init__(self, from_screen, to_screen, **kwargs):
        """init method for BackPopup"""
        # The screen this popup will direct to and from
        self.from_screen = from_screen
        self.to_screen = to_screen
        # Call Popup init method
        super(BackPopup, self).__init__(**kwargs)

    def on_answer(self, answer):
        """called when user presses 'yes' or 'no'"""
        # If they said "yes go back"
        if answer == "yes":
            # Get app and screen objects
            app = App.get_running_app()
            from_screen = app.root.get_screen(self.from_screen)
            to_screen = app.root.get_screen(self.to_screen)
            # If IE1 -> main
            if self.from_screen == 'IE1' and self.to_screen == 'main':
                # Clear all experiments and their boxes
                app.clear_experiments(boxes_only=False)
                # Update the from screen
                from_screen.update_fields()
                # Change screen
                app.root.current = self.to_screen
                app.root.transition.direction = "right"
            # If IE3 -> IE1
            elif self.from_screen == 'IE3' and self.to_screen == 'IE1':
                # Clear all experiments, but not their boxes
                app.clear_experiments(boxes_only=True)
                # Update the from screen
                from_screen.update_fields()
                # Change screen
                app.root.current = self.to_screen
                app.root.transition.direction = "right"
                # Update the to screen
                to_screen.update_fields()
                # Manually update is_selected for boxes
                to_screen.exp_scroll.update_is_selected()
            # If TD1 -> main
            elif self.from_screen == 'TD1' and self.to_screen == 'main':
                # Clear all events and their boxes
                app.clear_events(boxes_only=False)
                # Also clear experiments now :)
                app.clear_experiments(boxes_only=False, all_screens=True)
                # Update the from screen
                from_screen.update_fields()
                # Change screen
                app.root.current = self.to_screen
                app.root.transition.direction = "right"
            # If TD2 -> TD1
            elif self.from_screen == 'TD2' and self.to_screen == 'TD1':
                # Clear all events, but not their boxes
                app.clear_events(boxes_only=True)
                # Update the from screen
                from_screen.update_fields()
                # Change screen
                app.root.current = self.to_screen
                app.root.transition.direction = "right"
                # Update the to screen
                to_screen.update_fields()
                # Manually update is_selected for boxes
                to_screen.evt_scroll.update_is_selected()
            # If TD3 -> TD2
            elif self.from_screen == 'TD3' and self.to_screen == 'TD2':
                # Clear all events, but not their boxes
                app.clear_events(boxes_only=True)
                # Update the from screen
                from_screen.update_fields()
                # Change screen
                app.root.current = self.to_screen
                app.root.transition.direction = "right"
                # Update the to screen
                to_screen.update_fields()
                # Manually update is_selected for boxes
                to_screen.evt_scroll.update_is_selected()
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


class ConfirmPopup(Popup):
    """A custom Popup object for displaying an confirmation for export of event csvs screen
    - the popup doesnt do anything, it just tells the user something"""

    def on_answer(self, answer):
        """called when user presses 'ok'"""
        if answer == "ok":
            # Close popup
            self.dismiss()
