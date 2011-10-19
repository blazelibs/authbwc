Change Log
----------

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

* SECURITY FIX: fixed an issue with the way the HTTP session user permissions
    were loaded.  This vulnerability made it possible for a user to gain the
    permissions of the user logged in previously.  The user would have had
    to be sharing the same http session for this access to have been
    gained.

0.1.3 released 2010-11-24
=========================

* modifying after_login_url() to take script_name into account (requires BlazeWeb
    upgrade to 0.3.1)
