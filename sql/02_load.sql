-- 02_load.sql  (Section 2.2) - run from the PROJECT ROOT so the relative data/ paths resolve:
--   psql -d mobile_money -f sql/02_load.sql
-- Parents first: customers and devices, then accounts, account_devices and transfers.
\timing on
\copy customers       FROM 'data/customers.csv'       CSV HEADER
\copy devices         FROM 'data/devices.csv'         CSV HEADER
\copy accounts        FROM 'data/accounts.csv'        CSV HEADER
\copy account_devices FROM 'data/account_devices.csv' CSV HEADER
\copy transfers       FROM 'data/transfers.csv'       CSV HEADER
