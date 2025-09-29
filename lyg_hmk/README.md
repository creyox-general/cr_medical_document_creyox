LYG HMK
-----------------------
Go to Apps >> lyg_hmk (LYG HMK)

Version
--------
Odoo 17.0

## Functionality

1. Added New Journal for HMK Receipt
2. This Module is handling HMK type Invoice along with withholding process for HMK
3. Have added one flag at Journal "is_hmk" and once user will set is as true
   1. Create Invoice, It will showing Payment lines under invoice lines
   2. After adding Invoice lines, user need to confirm invoice and it will create
      payment and also reconcile that invoice with those payments
   3. If user want to create HMK type Invoice with withholding amount then they just
      need to add withholdiing amount in invoice and payment lines, once user confirm
      invoice it will create payment with withholding amount.
