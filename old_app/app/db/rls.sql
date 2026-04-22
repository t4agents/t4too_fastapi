-- Tenant-only RLS policies.
-- Application must set: SET LOCAL t4rls.tid = '<tenant-uuid>'

-- **********   ZMe , no rls   ************

-- zme	users	user_clients	biz_entities

-- Register
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE biz_entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_clients ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON users FOR ALL
USING (ten_id = current_setting('t4rls.tid')::uuid)
WITH CHECK (ten_id = current_setting('t4rls.tid')::uuid);

CREATE POLICY tenant_isolation ON biz_entities FOR ALL
USING (ten_id = current_setting('t4rls.tid')::uuid)
WITH CHECK (ten_id = current_setting('t4rls.tid')::uuid);

CREATE POLICY tenant_isolation ON user_clients FOR ALL
USING (ten_id = current_setting('t4rls.tid')::uuid)
WITH CHECK (ten_id = current_setting('t4rls.tid')::uuid);
------------------ Register






ALTER TABLE employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE payroll_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE payroll_periods ENABLE ROW LEVEL SECURITY;
ALTER TABLE payroll_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation ON users;
DROP POLICY IF EXISTS tenant_isolation ON zme;
DROP POLICY IF EXISTS tenant_isolation ON biz_entities;
DROP POLICY IF EXISTS tenant_isolation ON user_clients;
DROP POLICY IF EXISTS tenant_isolation ON employees;
DROP POLICY IF EXISTS tenant_isolation ON payroll_schedules;
DROP POLICY IF EXISTS tenant_isolation ON payroll_periods;
DROP POLICY IF EXISTS tenant_isolation ON payroll_entries;
DROP POLICY IF EXISTS tenant_isolation ON invoices;

CREATE POLICY tenant_isolation ON users
FOR ALL
USING (ten_id = current_setting('t4rls.tid')::uuid)
WITH CHECK (ten_id = current_setting('t4rls.tid')::uuid);

CREATE POLICY tenant_isolation ON biz_entities
FOR ALL
USING (ten_id = current_setting('t4rls.tid')::uuid)
WITH CHECK (ten_id = current_setting('t4rls.tid')::uuid);

CREATE POLICY tenant_isolation ON user_clients
FOR ALL
USING (ten_id = current_setting('t4rls.tid')::uuid)
WITH CHECK (ten_id = current_setting('t4rls.tid')::uuid);

CREATE POLICY tenant_isolation ON employees
FOR ALL
USING (ten_id = current_setting('t4rls.tid')::uuid)
WITH CHECK (ten_id = current_setting('t4rls.tid')::uuid);

CREATE POLICY tenant_isolation ON payroll_schedules
FOR ALL
USING (ten_id = current_setting('t4rls.tid')::uuid)
WITH CHECK (ten_id = current_setting('t4rls.tid')::uuid);

CREATE POLICY tenant_isolation ON payroll_periods
FOR ALL
USING (ten_id = current_setting('t4rls.tid')::uuid)
WITH CHECK (ten_id = current_setting('t4rls.tid')::uuid);

CREATE POLICY tenant_isolation ON payroll_entries
FOR ALL
USING (ten_id = current_setting('t4rls.tid')::uuid)
WITH CHECK (ten_id = current_setting('t4rls.tid')::uuid);

CREATE POLICY tenant_isolation ON invoices
FOR ALL
USING (ten_id = current_setting('t4rls.tid')::uuid)
WITH CHECK (ten_id = current_setting('t4rls.tid')::uuid);

-- App role privileges (adjust role name if your app uses a different DB role).
GRANT USAGE ON SCHEMA public TO t4user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE users TO t4user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE biz_entities TO t4user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE user_clients TO t4user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE employees TO t4user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE payroll_schedules TO t4user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE payroll_periods TO t4user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE payroll_entries TO t4user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE invoices TO t4user;



ALTER TABLE payroll ENABLE ROW LEVEL SECURITY;
ALTER TABLE payroll_periods ENABLE ROW LEVEL SECURITY;



-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO my_app_role;

-- CREATE POLICY tenant_biz_isolation
-- ON employees
-- USING (
--     ten_id = current_setting('t4rls.tid', true)::uuid
--     AND
--     biz_id = current_setting('app.zbid', true)::uuid
-- );

-- await session.execute(text("SET LOCAL t4rls.tid = :t"), {"t": tenant_id})
-- await session.execute(text("SET LOCAL app.zbid = :b"), {"b": biz_id})