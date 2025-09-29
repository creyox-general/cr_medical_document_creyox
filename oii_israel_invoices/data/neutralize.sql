-- deactivate taxes API authentication
UPDATE res_company
SET enable_taxes_integration = false,
    rt_taxes_host = 'https://openapi.taxes.gov.il/shaam/tsandbox/',
    rt_taxes_access_token = '',
    rt_taxes_refresh_token = ''
;

UPDATE ir_config_parameter
SET value = ''
WHERE key IN ('rt_taxes_client_id', 'rt_taxes_client_secret');
