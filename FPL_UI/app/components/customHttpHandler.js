'use strict';

(function() {
	angular.module('custom.http.handler', [])

	.service('customHttpHandlerController',
			function($http) {

				return {
					//https://api.github.com/users/mojombo	
					"getRequestHandler" : function(url,params) {
						
							return $http.get(url,params);
						},
					"postRequestHandler" : function(url,params) {
						
						var header = {
								"Content-Type" : "application/json",
								"Accept" : "*/*"
							}
							return $http.post(url,params,header);
					}
					}
					
				})
})();