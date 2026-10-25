-- 03_constraints_indexes.sql  (Sections 2.1 + 2.2) - validated FKs, required indexes, BRIN, ANALYZE.
\timing on

-- Foreign keys: ownership, device use, both transfer endpoints (validated against loaded rows)
ALTER TABLE accounts        ADD CONSTRAINT accounts_customer_fk  FOREIGN KEY (customer_id) REFERENCES customers (customer_id);
ALTER TABLE account_devices ADD CONSTRAINT ad_account_fk         FOREIGN KEY (account_id)  REFERENCES accounts (account_id);
ALTER TABLE account_devices ADD CONSTRAINT ad_device_fk          FOREIGN KEY (device_id)   REFERENCES devices (device_id);
ALTER TABLE transfers       ADD CONSTRAINT transfers_sender_fk   FOREIGN KEY (sender_id)   REFERENCES accounts (account_id);
ALTER TABLE transfers       ADD CONSTRAINT transfers_receiver_fk FOREIGN KEY (receiver_id) REFERENCES accounts (account_id);

-- Required indexes
CREATE INDEX accounts_customer_idx        ON accounts (customer_id, account_id);
CREATE INDEX account_devices_device_idx   ON account_devices (device_id, account_id);
CREATE INDEX transfers_sender_time_idx    ON transfers (sender_id, occurred_at)   INCLUDE (receiver_id, amount_rwf, transfer_id);
CREATE INDEX transfers_receiver_time_idx  ON transfers (receiver_id, occurred_at) INCLUDE (sender_id, amount_rwf, transfer_id);
CREATE INDEX transfers_time_brin          ON transfers USING BRIN (occurred_at);

ANALYZE;
