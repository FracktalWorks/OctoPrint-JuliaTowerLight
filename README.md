# OctoPrint-JuliaTowerLight

[OctoPrint](http://octoprint.org/) plugin that integrates with a tower light hooked up to Raspberry Pi GPIO pins.

## Requirements

* Uses the GPIO.BCM numbering scheme.
* Tower light that can be actuated with 3.3V logic or through a complementary circuit.

## Features

* Configurable GPIO pins in *config.yaml*.
* Status indicator in OctoPrint navbar.

## Debug 

Run `tail -n 100 -f ~/.octoprint/logs/octoprint.log` on pi.

## Installation

* Manually using this URL: https://github.com/FracktalWorks/OctoPrint-JuliaTowerLight/archive/master.zip

## Configuration

From `config.yaml`
