-- Invoice Test Data (10 records with mixed statuses)

INSERT INTO invoices (id, description, amount, status, due_date, created_at, ten_id, biz_id, b_int, b_str)
VALUES 
-- Paid invoices
('550e8400-e29b-41d4-a716-446655440001'::uuid, 'AWS Invoice - January 2026', 320.00, 'paid', '2026-02-15', '2026-01-25 10:30:00+00', NULL, NULL, 1, 'active'),
('550e8400-e29b-41d4-a716-446655440002'::uuid, 'Cloud Storage - Monthly Subscription', 120.00, 'paid', '2026-02-10', '2026-02-01 14:45:00+00', NULL, NULL, 1, 'active'),
('550e8400-e29b-41d4-a716-446655440003'::uuid, 'GitHub Enterprise License', 231.00, 'paid', '2026-01-31', '2026-01-20 09:15:00+00', NULL, NULL, 1, 'active'),
('550e8400-e29b-41d4-a716-446655440004'::uuid, 'Slack Workspace Annual Plan', 1200.00, 'paid', '2026-02-12', '2026-01-30 16:20:00+00', NULL, NULL, 1, 'active'),

-- Pending invoices
('550e8400-e29b-41d4-a716-446655440005'::uuid, 'Stripe Fees - February 2026', 58.00, 'pending', '2026-03-15', '2026-02-18 11:00:00+00', NULL, NULL, 1, 'active'),
('550e8400-e29b-41d4-a716-446655440006'::uuid, 'DataDog Monitoring Service', 450.75, 'pending', '2026-03-10', '2026-02-20 13:30:00+00', NULL, NULL, 1, 'active'),
('550e8400-e29b-41d4-a716-446655440007'::uuid, 'SendGrid Email API Credits', 175.50, 'pending', '2026-03-05', '2026-02-19 10:45:00+00', NULL, NULL, 1, 'active'),

-- Overdue invoices
('550e8400-e29b-41d4-a716-446655440008'::uuid, 'Twilio SMS Services - December 2025', 89.25, 'overdue', '2026-01-15', '2025-12-20 08:00:00+00', NULL, NULL, 1, 'active'),
('550e8400-e29b-41d4-a716-446655440009'::uuid, 'Auth0 Premium Subscription', 350.00, 'overdue', '2026-01-30', '2026-01-10 15:12:00+00', NULL, NULL, 1, 'active'),
('550e8400-e29b-41d4-a716-446655440010'::uuid, 'PostgreSQL Backup Service', 99.99, 'overdue', '2026-02-05', '2026-01-15 12:25:00+00', NULL, NULL, 1, 'active');
