# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
# from octoprint.events import Events
import RPi.GPIO as GPIO
from time import sleep
# from flask import jsonify
import threading


class StrobeLED(threading.Thread):
    DELAY_ON = 100
    DELAY_OFF = 200

    def __init__(self, pin, delay_on=DELAY_ON, delay_off=DELAY_OFF, fn_on=None, fn_off=None):
        super(StrobeLED, self).__init__()
        self.pin = pin
        self.delay_on = delay_on
        self.delay_off = delay_off
        self._stop_event = threading.Event()
        self.fn_on = fn_on
        self.fn_off = fn_off

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        while not self.stopped():
            try:
                GPIO.output(self.pin, GPIO.HIGH)
                if self.fn_on:
                    self.fn_on()
                sleep(self.delay_on / 1000.0)
                GPIO.output(self.pin, GPIO.LOW)
                if self.fn_off:
                    self.fn_off()
                sleep(self.delay_off / 1000.0)
            except:
                pass


class JuliaTowerLightPlugin(octoprint.plugin.StartupPlugin,
                            octoprint.plugin.EventHandlerPlugin,
                            octoprint.plugin.TemplatePlugin,
                            octoprint.plugin.SettingsPlugin,
                            octoprint.plugin.AssetPlugin):

    '''
    GPIO pin mapping
            BCM   BOARD
    '''
    PIN_R = 19  # 35
    PIN_Y = 16  # 36
    PIN_G = 20  # 38
    PIN_B = 21  # 40

    '''
    OctoPrint states
    '''
    STATE_OFFLINE = "Offline"
    STATE_PAUSED = "Paused"
    STATE_PRINTING = "Printing"
    STATE_OPERATIONAL = "Operational"
    AVAILABLE_STATES = [STATE_OFFLINE, STATE_PAUSED, STATE_PRINTING, STATE_OPERATIONAL]
    BLINK_STATES = [STATE_PAUSED, STATE_PRINTING, STATE_OPERATIONAL]

    '''
    Mapping
    '''
    MAP_LED_STATE = {
        STATE_OFFLINE: PIN_R,
        STATE_PAUSED: PIN_Y,
        STATE_PRINTING: PIN_G,
        STATE_OPERATIONAL: PIN_B
    }

    MAP_UI_STATE = {
        STATE_OFFLINE: "red",
        STATE_PAUSED: "yellow",
        STATE_PRINTING: "green",
        STATE_OPERATIONAL: "blue"
    }

    '''
    Global variables
    '''
    __thread_strobe = None
    __machine_state = None

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
        return self._settings.get_boolean(["tower_enabled"])

    @property
    def strobe(self):
        return self._settings.get_boolean(["strobe"])

    @property
    def delay_on(self):
        return self._settings.get_int(["delay_on"])

    @property
    def delay_off(self):
        return self._settings.get_int(["delay_off"])

    '''
    Thread
    '''

    def kill_thread_strobe(self):
        if self.__thread_strobe is not None and self.__thread_strobe.isAlive():
            self.__thread_strobe.stop()
        self.__thread_strobe = None

    def start_thread_strobe(self, pin):
        try:
            self.kill_thread_strobe()
            self.__thread_strobe = StrobeLED(pin, self.delay_on, self.delay_off, self.strobe_fn_on, self.strobe_fn_off)
            self.__thread_strobe.start()
        except Exception as e:
            self.log_error(e)

    '''
    Helpers
    '''
    def send_machine_state(self, color):
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="machine_state", machine_state=str(color)))

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

    def handle_machine_state(self):
        try:
            self.kill_thread_strobe()
        except Exception as e:
            self.log_error(e)
        self.reset_lights()

        if self.__machine_state not in self.AVAILABLE_STATES:
            return

        # self._plugin_manager.send_plugin_message(self._identifier, dict(type="event", event=str(self.__machine_state)))

        # if self.__machine_state == self.STATE_OFFLINE:
        #     self.set_light_state(self.PIN_R, GPIO.HIGH)
        # elif self.__machine_state == self.STATE_PAUSED:
        #     self.set_light_state(self.PIN_Y, GPIO.HIGH)
        # elif self.__machine_state == self.STATE_PRINTING:
        #     self.set_light_state(self.PIN_G, GPIO.HIGH)
        # elif self.__machine_state == self.STATE_OPERATIONAL:
        #     self.set_light_state(self.PIN_G, GPIO.HIGH)

        if self.strobe and self.__machine_state in self.BLINK_STATES:
            self.log_info("Strobe " + self.__machine_state)
            self.start_thread_strobe(self.MAP_LED_STATE[self.__machine_state])
        else:
            self.log_info("Static " + self.__machine_state)
            self.set_light_state(self.MAP_LED_STATE[self.__machine_state], GPIO.HIGH)
            self.send_machine_state(self.MAP_UI_STATE[self.__machine_state])

    def strobe_fn_on(self):
        # self.log_info("strobe_fn_on")
        self.send_machine_state(self.MAP_UI_STATE[self.__machine_state])

    def strobe_fn_off(self):
        # self.log_info("strobe_fn_off")
        self.send_machine_state("")

    '''
    Sensor Initialization
    '''
    def _gpio_clean_pin(self, pin):
        try:
            GPIO.cleanup(pin)
        except:
            pass

    def _gpio_setup(self):
        try:
            GPIO.setmode(GPIO.BCM)

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
    Plugin Management
    '''
    def on_after_startup(self):
        self.log_info("JuliaTowerLight plugin started")
        self._gpio_setup()

    def on_event(self, event, payload):
        # self._plugin_manager.send_plugin_message(self._identifier, dict(type="event", event=str(event)))
        if self.__machine_state == self._printer.get_state_string():
            return
        self.__machine_state = self._printer.get_state_string()
        self.handle_machine_state()

    def initialize(self):
        self.log_info("Running RPi.GPIO version '{0}'".format(GPIO.VERSION))
        if GPIO.VERSION < "0.6":       # Need at least 0.6 for edge detection
            raise Exception("RPi.GPIO must be greater than 0.6")
        GPIO.setwarnings(False)        # Disable GPIO warnings

    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self._gpio_setup()
        self.handle_machine_state()

    def get_assets(self):
        return dict(
            js=["js/JuliaTowerLight_navbar.js", "js/JuliaTowerLight_settings.js"],
            css=["css/style.css"]
        )

    def get_template_configs(self):
        return [dict(type="navbar", custom_bindings=True), dict(type="settings", custom_bindings=True)]

    def get_settings_defaults(self):
        return dict(tower_enabled=True,
                    strobe=True,
                    delay_on=100,
                    delay_off=1000)

    '''
    Update Management
    '''
    def get_update_information(self):
        return dict(
            octoprint_filament=dict(
                displayName="Julia Tower Light",
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


__plugin_name__ = "Julia Tower Light"
__plugin_version__ = "0.0.2"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = JuliaTowerLightPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
