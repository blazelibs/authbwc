Change Log
----------

0.1.10 released ???
=========================

* ???

0.1.9 released 2011-12-13
=========================

* (MAJOR) fix bug that was causing groups to be deleted when a user is deleted.  Make
  sure that you run the fix-group-fk task to shore up the DB constraints.
* make User.testing_create() more robust
* fix bug in user permission map template that was causing exceptions if a user
  was assigned to a group with permissions
* add console command to add administrative user

0.1.8 released 2011-11-09
=========================

* **BC BREAK**: change test_create() methods to testing_create()

0.1.7 released 2011-10-31
=========================

* fix user message css styling issue on password reset page

0.1.6 released 2011-10-19
=========================

* fix manage pages when used with MSSQL

0.1.5 released 2011-06-11
=========================

* use Form from CommonBWC since it handles SAValidation errors now
* fix bug in UserFormBase.add_field_errors()
* Add UserMixin permission related methods

0.1.4 released 2011-01-07
=========================

* (SECURITY FIX) fixed an issue with the way the HTTP session user permissions
  were loaded.  This vulnerability made it possible for a user to gain the
  permissions of the user logged in previously.  The user would have had
  to be sharing the same http session for this access to have been
  gained.

0.1.3 released 2010-11-24
=========================

* modifying after_login_url() to take script_name into account (requires BlazeWeb
  upgrade to 0.3.1)
