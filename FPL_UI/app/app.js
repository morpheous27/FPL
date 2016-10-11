/**
 * @Created by Nitin Saxena
 * 
 * @Main Application module.
 */

'use strict';

// Declare app level module which depends on views, and components
angular.module('app', [ 'ngRoute', 'ngMaterial', 'custom.http.handler','app.signup'])

.controller(
		'appController',
		function($scope, $interval, customHttpHandlerController) {

			this.elevation = 10;
			this.showFrame = 3;
			$scope.data ="nitin";
			$scope.callAService = function() {
				customHttpHandlerController.getRequestHandler('service url')
						.then(function(response) {
							$scope.data = response;
						})
			}
			this.toggleFrame = function() {
				this.showFrame = this.showFrame == 3 ? -1 : 3;
			}
		}).config([ '$routeProvider', function($routeProvider) {
	$routeProvider.when('/login', 
	{
		templateUrl : 'loginScreen/Login.html',
		controller : 'appController'
	}).when('/signup', 
		{
		templateUrl : 'signUpScreen/SignUp.html',
		controller : 'signupCtrl'
	}).otherwise({
		redirectTo : '/login'
	});
} ]);