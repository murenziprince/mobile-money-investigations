-- 01_schema.sql  (Section 2.1) - five tables, NOT NULL everywhere, PKs and CHECKs.
-- Foreign keys and secondary indexes are added AFTER the bulk load (03_constraints_indexes.sql)
-- so that "loading" and "index/constraint setup" can be timed separately.
-- Units: occurred_at = Unix seconds (UTC epoch); amount_rwf = whole Rwandan francs;
--        first_day/last_day = inclusive day numbers 0..29 counted from 1 Sep 2026 (CAT);
--        observations = number of times the device was observed for that account in the interval.

DROP TABLE IF EXISTS transfers, account_devices, accounts, devices, customers CASCADE;

CREATE TABLE customers (
    customer_id INTEGER NOT NULL PRIMARY KEY,
    region      TEXT    NOT NULL            -- Kigali | Northern | Southern | Eastern | Western
);

CREATE TABLE devices (
    device_id   INTEGER NOT NULL PRIMARY KEY,
    access_type TEXT    NOT NULL            -- handset | public_terminal
);

CREATE TABLE accounts (
    account_id  INTEGER NOT NULL PRIMARY KEY,
    customer_id INTEGER NOT NULL,           -- owner (FK added after load)
    role        TEXT    NOT NULL            -- person | merchant | agent
);

CREATE TABLE account_devices (
    account_id   INTEGER  NOT NULL,
    device_id    INTEGER  NOT NULL,
    first_day    SMALLINT NOT NULL,
    last_day     SMALLINT NOT NULL,
    observations INTEGER  NOT NULL CHECK (observations > 0),
    PRIMARY KEY (account_id, device_id),
    CONSTRAINT account_devices_days_ck CHECK (0 <= first_day AND first_day <= last_day AND last_day <= 29)
);

CREATE TABLE transfers (
    transfer_id BIGINT  NOT NULL PRIMARY KEY,
    sender_id   INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    occurred_at BIGINT  NOT NULL,
    amount_rwf  INTEGER NOT NULL CHECK (amount_rwf > 0)
);
