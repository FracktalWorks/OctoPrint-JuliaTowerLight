$(function() {
	function JuliaTowerLight_VM(parameters) {
		var self = this;

		self.settingsViewModel = parameters[0];

		self.onBeforeBinding = function() {
			console.log('Binding JuliaTowerLight_VM')

			self.config = self.settingsViewModel.settings.plugins.JuliaTowerLight;
		}

		self.onDataUpdaterPluginMessage = function(plugin, data) {
			if (plugin != "JuliaTowerLight") {
				// console.log('Ignoring '+plugin);
				return;
			}

			$("#JuliaTowerLight_status").removeClass();

			console.log(data);

			if (data.type != "navbar_status" || !data.color)
				return;

			$("#JuliaTowerLight_status").addClass(data.color)
		}
	}


	// This is how our plugin registers itself with the application, by adding some configuration
	// information to the global variable OCTOPRINT_VIEWMODELS
	ADDITIONAL_VIEWMODELS.push([
		// This is the constructor to call for instantiating the plugin
		JuliaTowerLight_VM,

		// This is a list of dependencies to inject into the plugin, the order which you request
		// here is the order in which the dependencies will be injected into your view model upon
		// instantiation via the parameters argument
		["settingsViewModel"],

		// Finally, this is the list of selectors for all elements we want this view model to be bound to.
		["#JuliaTowerLight_status"]
	]);
});