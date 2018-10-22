# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
from octoprint.events import Events
import RPi.GPIO as GPIO
from time import sleep
from flask import jsonify

'''
Uses Pi's internal pullups.

GPIO states
Open    - HIGH
Closed  - LOW
'''

class JuliaTowerLightPlugin(octoprint.plugin.StartupPlugin,
                             octoprint.plugin.EventHandlerPlugin,
                             octoprint.plugin.TemplatePlugin,
                             octoprint.plugin.SettingsPlugin,
                             octoprint.plugin.AssetPlugin):

    '''
    Logging
    '''
    def log_info(self, txt):
        self._logger.info(txt)
        # self._plugin_manager.send_plugin_message(self._identifier, dict(type="popup", msgType="notice", msg=str(txt)))

    def log_error(self, txt):
        self._logger.error(txt)

    '''
    Settings
    '''
    @property
    def enabled(self):
        return int(self._settings.get(["enabled"]))

    @property
    def pin_red(self):
        return int(self._settings.get(["pin_red"]))

    @property
    def pin_green(self):
        return int(self._settings.get(["pin_green"]))

    @property
    def pin_yellow(self):
        return int(self._settings.get(["pin_yellow"]))

    '''
    Helpers
    '''
    def has_pin(self, pin):
        return pin != -1

    def light_set(self, pin, state=GPIO.LOW):
        if self.has_pin(pin):
            GPIO.output(pin, state)

    def reset_lights(self):
        self.light_set(self.pin_red)
        self.light_set(self.pin_green)
        self.light_set(self.pin_yellow)

    def navbar_status(self, color):
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="navbar_status", color=str(color)))

    '''
    Sensor Initialization
    '''
    def _init_gpio(self):
        try:
            if self.has_pin(self.pin_red) or self.has_pin(self.pin_green) or self.has_pin(pin_yellow):
                self.log_info("Setting up Tower Light GPIO.")
                GPIO.setmode(GPIO.BCM)

                if self.has_pin(self.pin_red):
                    GPIO.setup(self.pin_red, GPIO.OUT, initial=GPIO.LOW)

                if self.has_pin(self.pin_green):
                    GPIO.setup(self.pin_green, GPIO.OUT, initial=GPIO.LOW)

                if self.has_pin(self.pin_yellow):
                    GPIO.setup(self.pin_yellow, GPIO.OUT, initial=GPIO.LOW)

                self.reset_lights()
                self.navbar_status()

            else:
                self.log_info("Pins not configured, won't work unless configured!")

        except Exception as e:
            self.log_error(e)

    '''
    Callbacks
    '''
    def on_after_startup(self):
        self.log_info("JuliaTowerLight plugin started")
        self._init_gpio()

    def on_event(self, event, payload):
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="event", event=str(event)))
        self.reset_lights()

        # Red
        if event in (
            Events.ERROR,
            Events.DISCONNECTED,
            Events.PRINT_FAILED,
        ):
            self.light_set(self.pin_red, GPIO.HIGH)
            self.navbar_status("red")

        # Green
        elif event in (
            Events.PRINT_STARTED,
            Events.PRINT_RESUMED
        ):
            self.light_set(self.pin_green, GPIO.HIGH)
            self.navbar_status("green")
        # Yellow
        elif event in (
            Events.CONNECTED,
            Events.PRINT_PAUSED,
            Events.PRINT_DONE,
            Events.PRINT_CANCELLED
        ):
        # else:
            self.light_set(self.pin_yellow, GPIO.HIGH)
            self.navbar_status("yellow")

    '''
    Update Management
    '''
    def get_update_information(self):
        return dict(
            octoprint_filament=dict(
                displayName="Julia 2018 Filament Sensor",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="FracktalWorks",
                repo="OctoPrint-JuliaTowerLight",
                current=self._plugin_version,

                # update method: pip
                pip="https://github.com/FracktalWorks/OctoPrint-JuliaTowerLight/archive/{target_version}.zip"
            )
        )

    '''
    Plugin Management
    '''
    def initialize(self):
        self.log_info("Running RPi.GPIO version '{0}'".format(GPIO.VERSION))
        if GPIO.VERSION < "0.6":       # Need at least 0.6 for edge detection
            raise Exception("RPi.GPIO must be greater than 0.6")
        GPIO.setwarnings(False)        # Disable GPIO warnings
    
    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self._init_gpio()

    def get_assets(self):
        return dict(
            js=["js/JuliaTowerLight.js"],
            css=["css/style.css"]
        )
 
    def get_template_configs(self):
        return [dict(type="navbar", custom_bindings=True)]

    def get_settings_defaults(self):
        return dict(
            enabled = True,
            pin_red = -1,
            pin_green = -1,
            pin_yellow = -1
        )

__plugin_name__ = "Julia Tower Light"
__plugin_version__ = "1.0.0"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = JuliaTowerLightPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
}
