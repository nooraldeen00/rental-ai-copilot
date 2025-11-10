INSERT INTO inventory (sku,name,location,on_hand,committed,attributes) VALUES
('LT-LED','LED Light Tower','Dallas',12,2,JSON_OBJECT('watts', '1000W', 'fuel', 'diesel')),
('GEN-20K','Generator 20kW','Dallas',6,1,JSON_OBJECT('phase','single','fuel','diesel')),
('SS-70','Skid Steer 70HP','Austin',3,0,JSON_OBJECT('bucket','standard'));

INSERT INTO rates (sku,daily,weekly,monthly,damage_waiver_pct,delivery_fee_base) VALUES
('LT-LED', 95.00, 500.00, 1700.00, 10.00, 85.00),
('GEN-20K',180.00, 900.00, 3000.00, 12.00,120.00),
('SS-70', 250.00,1200.00, 3800.00, 10.00,160.00);

INSERT INTO customers (name,tier,default_location) VALUES
('Acme Builders','B','Dallas'),
('Sunrise Events','A','Austin');

INSERT INTO policies (key_name,value_json) VALUES
('weekend_delivery', JSON_OBJECT('surcharge', 75)),
('min_rental_days',  JSON_OBJECT('default', 1, 'SS-70', 2)),
('damage_waiver',    JSON_OBJECT('default_pct', 0.10, 'tier_overrides', JSON_OBJECT('A', 0.05, 'B', 0.08, 'C', 0.10)));
