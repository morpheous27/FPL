'use strict';

(function() {

	var app = angular.module('custom.button', [ 'custom.http.handler' ]);
	app.controller('customButtonController', function($scope)
			{
					
			});

	
	app.directive('customButton', function() {
		return {
			restrict : 'E',
			/*scope : {
				id : "@",
				label : "@"
			},*/
			template : "<input type=\"button\" value='{{label}}' ng-click='doLogin()'></input>"
			
		};
	});

})();