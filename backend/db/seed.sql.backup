-- INVENTORY ---------------------------------------------------------
INSERT INTO inventory (sku, name, location, on_hand, committed, attributes) VALUES
('CHAIR-FOLD', 'Plastic Folding Chair - White', 'Plano, TX', 500, 0, JSON_OBJECT('type','chair','color','white')),
('TENT-20x20', 'Tent 20x20 (High Peak)', 'Dallas, TX', 12, 0, JSON_OBJECT('type','tent','dimensions','20x20')),
('TABLE-8FT', '8ft Banquet Table', 'Plano, TX', 120, 0, JSON_OBJECT('type','table','length','8ft'))
ON DUPLICATE KEY UPDATE name = VALUES(name);

-- RATES --------------------------------------------------------------
INSERT INTO rates (sku, daily, weekly, monthly, damage_waiver_pct, delivery_fee_base) VALUES
('CHAIR-FOLD', 1.50, 7.00, 20.00, 10.00, 25.00),
('TENT-20x20', 150.00, 700.00, 2000.00, 10.00, 120.00),
('TABLE-8FT', 10.00, 45.00, 120.00, 10.00, 25.00)
ON DUPLICATE KEY UPDATE daily = VALUES(daily);

-- CUSTOMERS ---------------------------------------------------------
INSERT INTO customers (name, tier, default_location) VALUES
('Walk-In Customer', 'C', 'Plano, TX'),
('VIP Client', 'A', 'Dallas, TX')
ON DUPLICATE KEY UPDATE tier = VALUES(tier);

-- POLICIES ----------------------------------------------------------
INSERT INTO policies (key_name, value_json) VALUES
('tax_rate', JSON_OBJECT('pct', 8.25)),
('default_damage_waiver', JSON_OBJECT('pct', 10.0))
ON DUPLICATE KEY UPDATE value_json = VALUES(value_json);
