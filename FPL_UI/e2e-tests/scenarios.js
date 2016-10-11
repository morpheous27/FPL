'use strict';

/* Created by Nitin Saxena to test Login page */

describe('app', function() {


  it('should automatically redirect to /login when location does not match to any option', function() {
    browser.get('index.html');
    expect(browser.getLocationAbsUrl()).toMatch("/login");
  });


  describe('loginScreen', function() {

    beforeEach(function() {
      browser.get('index.html#!/login');
    });


    it('should render login screen when user navigates to /login', function() {
      expect(element.all(by.css('[ng-view] p')).first().getText()).
        toMatch(/partial for view 1/);
    });

  });

});
