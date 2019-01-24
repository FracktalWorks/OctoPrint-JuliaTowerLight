# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
from octoprint.events import Events
import RPi.GPIO as GPIO
# from time import sleep
# from flask import jsonify

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
            BCM   BOARD
    PIN_R   19    35
    PIN_Y   16    36
    PIN_G   20    38
    PIN_B   21    40
    '''

    PIN_R = 19
    PIN_Y = 16
    PIN_G = 20
    PIN_B = 21

    '''
    Logging
    '''
    def log_info(self, txt):
        self._logger.info(txt)

    def log_error(self, txt):
        self._logger.error(txt)

    '''
    Settings
    '''
    @property
    def tower_enabled(self):
        return int(self._settings.get(["tower_enabled"]))

    '''
    Helpers
    '''

    def set_light_state(self, pin, state=GPIO.LOW):
        try:
            GPIO.output(pin, state)
        except Exception as e:
            self.log_error(e)

    def reset_lights(self):
        self.set_light_state(self.PIN_R)
        self.set_light_state(self.PIN_Y)
        self.set_light_state(self.PIN_G)
        self.set_light_state(self.PIN_B)

    def navbar_status(self, color):
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="navbar_status", color=str(color)))

    '''
    Sensor Initialization
    '''
    def _gpio_clean_pin(self, pin):
        try:
            GPIO.cleanup(pin)
        except:
            pass

    def _gpio_setup(self):
        self.log_info("_gpio_setup")
        try:
            # mode = GPIO.getmode()
            # if mode is None or mode is GPIO.UNKNOWN:
            #     GPIO.setmode(GPIO.BCM)
            #     mode = GPIO.getmode()
            GPIO.setmode(GPIO.BCM)

            # self._gpio_pinout(mode)

            self._gpio_clean_pin(self.PIN_R)
            self._gpio_clean_pin(self.PIN_Y)
            self._gpio_clean_pin(self.PIN_G)
            self._gpio_clean_pin(self.PIN_B)

            if self.tower_enabled:
                self.log_info("Tower Light GPIO setup")
                GPIO.setup(self.PIN_R, GPIO.OUT, initial=GPIO.LOW)
                GPIO.setup(self.PIN_Y, GPIO.OUT, initial=GPIO.LOW)
                GPIO.setup(self.PIN_G, GPIO.OUT, initial=GPIO.LOW)
                GPIO.setup(self.PIN_B, GPIO.OUT, initial=GPIO.LOW)

                self.reset_lights()

            else:
                self.log_info("Tower Light disabled")
        except Exception as e:
            self.log_error(e)
            # self.popup_error(e)

    '''
    Callbacks
    '''
    def on_after_startup(self):
        self.log_info("JuliaTowerLight plugin started")
        self._gpio_setup()

    def on_event(self, event, payload):
        # self._plugin_manager.send_plugin_message(self._identifier, dict(type="event", event=str(event)))
        self.reset_lights()

        status = self._printer.get_state_string()

        # Red
        # if event in (
        #     Events.ERROR,
        #     Events.DISCONNECTED,
        #     Events.PRINT_FAILED,
        # ):
        if status == "Offline":
            self.set_light_state(self.PIN_R, GPIO.HIGH)
            self.navbar_status("red")

        # Yellow
        # elif event in (
        #     Events.CONNECTED,
        #     Events.PRINT_PAUSED,
        #     Events.PRINT_DONE,
        #     Events.PRINT_CANCELLED
        # ):
        elif status == "Paused":
            # else:
            self.set_light_state(self.PIN_Y, GPIO.HIGH)
            self.navbar_status("yellow")

        # Green
        # elif event in (
        #     Events.PRINT_STARTED,
        #     Events.PRINT_RESUMED
        # ):
        elif status == "Printing":
            self.set_light_state(self.PIN_G, GPIO.HIGH)
            self.navbar_status("green")

        # Green
        # elif event in (
        #     Events.OP,
        #     Events.PRINT_RESUMED
        # ):
        elif status == "Operational":
            self.set_light_state(self.PIN_G, GPIO.HIGH)
            self.navbar_status("green")
        

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
        self._gpio_setup()

    def get_assets(self):
        return dict(
            js=["js/JuliaTowerLight.js"],
            css=["css/style.css"]
        )
 
    def get_template_configs(self):
        return [dict(type="navbar", custom_bindings=True)]

    def get_settings_defaults(self):
        return dict(tower_enabled=True,
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
