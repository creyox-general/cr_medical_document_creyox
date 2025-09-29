=======================
LYG Withholding
=======================

This Module will help to manage withholding tax for Israel.

**Table of contents**

.. contents::
   :local:

Installation
============

To install this module you don't need to install any other dependency package

Configuration
=============

This module will work only with Israel company.
Supplier withholding :
    * Go to company ``> Add Withholding Tax rate for IL company.``
    * Go to Contacts
    * Choose partner's country as Israel
    * Withholding Page will be visible where user can see default rate, tax reason etc

Java Memory Settings
~~~~~~~~~~~~~~~~~~~~
N/A

Usage
=====
* Supplier Payment :
    1.1) ``Accounting >> Vendor >> Payment >> Create``
        - Before creating payment for supplier, supplier must have below configuration :
            - Country : israel
            - withholding tax rate must be added (default rate will come from company).
        - Once user create payment, it will auto calculate withholding amount for that payment based on the withholding tax rate of supplier.
        - It will modify odoo's standard Journal entries with withholding amount.
    1.2) ``Accounting >> Vendor >> Payment >> Edit``
        - Modify Payment amount it will also auto calculate withholding amount and update Journal entries for the same
* Vendor Bill :
    2.1) ``Accounting >> Vendor >> Bills >> Create >> Register Payment``
        - It will create payment with withholding entries based on withholding rate at supplier.
    Note : It will work along with write-off and keep open option (while doing register payment)
* Customer Invoice :
    3.1) ``Accounting >> Customers >> Invoices >> Create >> Register Payment >> Add Withholding Amount``
        - It will create payment along with withholding amount added by user and also with write-off and keep open option.
* Customer Invoice(HMK) :
    4.1) ``Accounting >> Configuration >> Journal >> Is HMk set as true``
    4.2) ``Accounting >> Customers >> Invoices >> Create >> Choose HMK Journal >> Add withholding amount``
        - It will create payment along with withholding amount added by user.
* Receipt :
    5.1) With Invoice : While adding payment lines user can add withholding amount and, it will create payment based on that withholding amount also, invoice will reconcile as per odoo's flow with withholding entries.
    5.2) Generic : User can create generic payment with withholding amount as well

Known issues / Roadmap
======================
N/A

Bug Tracker
===========
N/A

Credits
=======

Authors
~~~~~~~

* Yves Goldberg

Contributors
~~~~~~~~~~~~

* `Yves Goldberg (Ygol InternetWork) <http://www.ygol.com>`

Other credits
~~~~~~~~~~~~~
N/A
External utilities
++++++++++++++++++

N/A
Icon
++++
No Icon

Maintainers
~~~~~~~~~~~
This module is maintained by the Yves Goldberg