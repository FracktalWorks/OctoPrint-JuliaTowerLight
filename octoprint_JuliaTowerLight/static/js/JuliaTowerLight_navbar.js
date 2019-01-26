$(function() {
    function VM_JuliaTowerLight_navbar(parameters) {
        var self = this;

        self.Config = undefined;
        self.VM_settings = parameters[0];

        self.towerEnabled = ko.observable(false);

        self.onBeforeBinding = function() {
            console.log('Binding VM_JuliaTowerLight_navbar')

            self.Config = self.VM_settings.settings.plugins.JuliaTowerLight;

            self.Config.tower_enabled.subscribe(function(value) {
                self.towerEnabled(value == 1);
            });
            self.towerEnabled(self.Config.tower_enabled() == 1);
        }

        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin != "JuliaTowerLight") {
                // console.log('Ignoring '+plugin);
                return;
            }

            if (data.type == "machine_state") {
                var led = $("#machine_state");
                led.removeClass();

                if (!self.Config.tower_enabled()) {
                    led.hide();
                    return;
                } else {
                    led.show()
                }

                if (!data.machine_state)
                    return;
                led.addClass(data.machine_state);
            } else {
                console.log(data);
            }
        }
    }


    // This is how our plugin registers itself with the application, by adding some configuration
    // information to the global variable OCTOPRINT_VIEWMODELS
    ADDITIONAL_VIEWMODELS.push([
        // This is the constructor to call for instantiating the plugin
        VM_JuliaTowerLight_navbar,

        // This is a list of dependencies to inject into the plugin, the order which you request
        // here is the order in which the dependencies will be injected into your view model upon
        // instantiation via the parameters argument
        ["settingsViewModel"],

        // Finally, this is the list of selectors for all elements we want this view model to be bound to.
        ["#machine_state"]
    ]);
});