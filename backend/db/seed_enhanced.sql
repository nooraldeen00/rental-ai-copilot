-- =====================================================================
-- RENTALAI COPILOT - ENHANCED SEED DATA
-- =====================================================================
-- This seed file contains realistic rental inventory across multiple
-- categories to demonstrate the full capabilities of RentalAI Copilot.
-- =====================================================================

-- INVENTORY ============================================================
-- Categories: Event/Party, Audio/Visual, Construction, Heavy Equipment
-- =====================================================================

INSERT INTO inventory (sku, name, location, on_hand, committed, attributes) VALUES
-- EVENT / PARTY RENTALS (Budget to Mid-range) -------------------------
('CHAIR-FOLD-WHT', 'Folding Chair - White Plastic', 'Plano, TX', 500, 0,
    JSON_OBJECT('category','event','type','chair','color','white','weight_lbs',8)),
('CHAIR-CHIAVARI', 'Chiavari Chair - Gold', 'Dallas, TX', 150, 0,
    JSON_OBJECT('category','event','type','chair','color','gold','weight_lbs',9)),
('TABLE-6FT-RECT', '6ft Rectangular Banquet Table', 'Plano, TX', 80, 0,
    JSON_OBJECT('category','event','type','table','size','6ft','weight_lbs',45)),
('TABLE-8FT-RECT', '8ft Rectangular Banquet Table', 'Plano, TX', 120, 0,
    JSON_OBJECT('category','event','type','table','size','8ft','weight_lbs',55)),
('TABLE-60RND', '60" Round Table', 'Dallas, TX', 60, 0,
    JSON_OBJECT('category','event','type','table','size','60in','weight_lbs',50)),
('LINEN-120RND-WHT', '120" Round Tablecloth - White', 'Plano, TX', 200, 0,
    JSON_OBJECT('category','event','type','linen','size','120in','color','white')),
('LINEN-120RND-BLK', '120" Round Tablecloth - Black', 'Plano, TX', 150, 0,
    JSON_OBJECT('category','event','type','linen','size','120in','color','black')),
('TENT-10x10', '10x10 Pop-Up Tent - White', 'Fort Worth, TX', 25, 0,
    JSON_OBJECT('category','event','type','tent','size','10x10','weight_lbs',80)),
('TENT-20x20', '20x20 Frame Tent - White', 'Dallas, TX', 12, 0,
    JSON_OBJECT('category','event','type','tent','size','20x20','weight_lbs',450)),
('TENT-40x60', '40x60 Pole Tent - White', 'Arlington, TX', 5, 0,
    JSON_OBJECT('category','event','type','tent','size','40x60','weight_lbs',1200)),
('STAGE-4x8', '4x8 Stage Platform - 2ft Height', 'Plano, TX', 30, 0,
    JSON_OBJECT('category','event','type','stage','size','4x8','height_ft',2)),

-- AUDIO / VISUAL EQUIPMENT (Mid to Premium) ----------------------------
('SPEAKER-PA-BASIC', 'PA Speaker System - 500W', 'Dallas, TX', 15, 0,
    JSON_OBJECT('category','av','type','speaker','watts',500)),
('SPEAKER-PA-PRO', 'Professional PA System - 2000W', 'Dallas, TX', 8, 0,
    JSON_OBJECT('category','av','type','speaker','watts',2000)),
('MIC-WIRELESS-HH', 'Wireless Handheld Microphone', 'Plano, TX', 40, 0,
    JSON_OBJECT('category','av','type','microphone','wireless',true)),
('MIXER-8CH', '8-Channel Audio Mixer', 'Dallas, TX', 10, 0,
    JSON_OBJECT('category','av','type','mixer','channels',8)),
('LIGHT-UPLIGHT-LED', 'LED Uplight - RGBA', 'Dallas, TX', 50, 0,
    JSON_OBJECT('category','av','type','lighting','led',true,'color','rgba')),
('PROJECTOR-4K', '4K Projector - 5000 Lumens', 'Plano, TX', 8, 0,
    JSON_OBJECT('category','av','type','projector','resolution','4k','lumens',5000)),
('SCREEN-PROJ-120', '120" Projection Screen - Tripod', 'Plano, TX', 12, 0,
    JSON_OBJECT('category','av','type','screen','size','120in')),

-- CONSTRUCTION EQUIPMENT (Premium) -------------------------------------
('LIFT-SCISSOR-19', '19ft Electric Scissor Lift', 'Fort Worth, TX', 10, 0,
    JSON_OBJECT('category','construction','type','lift','height_ft',19,'power','electric')),
('LIFT-SCISSOR-26', '26ft Electric Scissor Lift', 'Arlington, TX', 8, 0,
    JSON_OBJECT('category','construction','type','lift','height_ft',26,'power','electric')),
('LIFT-BOOM-40', '40ft Telescopic Boom Lift - Diesel', 'Dallas, TX', 5, 0,
    JSON_OBJECT('category','construction','type','boom','height_ft',40,'power','diesel')),
('GEN-5KW', '5kW Portable Generator - Gas', 'Fort Worth, TX', 20, 0,
    JSON_OBJECT('category','construction','type','generator','watts',5000,'fuel','gas')),
('GEN-10KW-DIESEL', '10kW Diesel Generator - Towable', 'Arlington, TX', 12, 0,
    JSON_OBJECT('category','construction','type','generator','watts',10000,'fuel','diesel')),
('COMPRESSOR-185CFM', '185 CFM Air Compressor - Towable', 'Fort Worth, TX', 8, 0,
    JSON_OBJECT('category','construction','type','compressor','cfm',185)),
('SCAFFOLD-5x5x7', '5x5x7 Frame Scaffold Package', 'Plano, TX', 15, 0,
    JSON_OBJECT('category','construction','type','scaffold','size','5x5x7')),

-- HEAVY EQUIPMENT (Premium to High-end) --------------------------------
('FORKLIFT-5K', '5,000 lb Forklift - Propane', 'Arlington, TX', 6, 0,
    JSON_OBJECT('category','heavy','type','forklift','capacity_lbs',5000,'fuel','propane')),
('SKIDSTEER-1800', '1,800 lb Skid Steer Loader', 'Fort Worth, TX', 8, 0,
    JSON_OBJECT('category','heavy','type','skidsteer','capacity_lbs',1800)),
('EXCAVATOR-MINI', 'Mini Excavator - 3 Ton', 'Dallas, TX', 5, 0,
    JSON_OBJECT('category','heavy','type','excavator','weight_tons',3)),

-- CLIMATE CONTROL & SPECIALTY ------------------------------------------
('HEATER-PROPANE', 'Propane Heater - 200K BTU', 'Fort Worth, TX', 25, 0,
    JSON_OBJECT('category','climate','type','heater','btu',200000,'fuel','propane')),
('FAN-DRUM-36', '36" Drum Fan - High Velocity', 'Plano, TX', 30, 0,
    JSON_OBJECT('category','climate','type','fan','size','36in'))

ON DUPLICATE KEY UPDATE name = VALUES(name);


-- RATES ================================================================
-- Pricing structure: daily, weekly (5x daily), monthly (15x daily)
-- Damage waiver: 5-15% based on item value
-- Delivery fees: $25-$200 based on size/weight
-- =====================================================================

INSERT INTO rates (sku, daily, weekly, monthly, damage_waiver_pct, delivery_fee_base) VALUES
-- EVENT / PARTY RENTALS (Low cost, low delivery) -----------------------
('CHAIR-FOLD-WHT',      1.50,    7.50,   22.50,  5.00,  25.00),
('CHAIR-CHIAVARI',      4.00,   20.00,   60.00,  5.00,  25.00),
('TABLE-6FT-RECT',      8.00,   40.00,  120.00,  5.00,  35.00),
('TABLE-8FT-RECT',     10.00,   50.00,  150.00,  5.00,  35.00),
('TABLE-60RND',        12.00,   60.00,  180.00,  5.00,  35.00),
('LINEN-120RND-WHT',    8.00,   40.00,  120.00,  5.00,  15.00),
('LINEN-120RND-BLK',    8.00,   40.00,  120.00,  5.00,  15.00),
('TENT-10x10',         45.00,  225.00,  675.00,  8.00,  50.00),
('TENT-20x20',        150.00,  750.00, 2250.00, 10.00, 120.00),
('TENT-40x60',        450.00, 2250.00, 6750.00, 12.00, 200.00),
('STAGE-4x8',          25.00,  125.00,  375.00,  8.00,  40.00),

-- AUDIO / VISUAL EQUIPMENT (Mid-range delivery) ------------------------
('SPEAKER-PA-BASIC',   75.00,  375.00, 1125.00, 10.00,  50.00),
('SPEAKER-PA-PRO',    150.00,  750.00, 2250.00, 12.00,  75.00),
('MIC-WIRELESS-HH',    25.00,  125.00,  375.00,  8.00,  25.00),
('MIXER-8CH',          50.00,  250.00,  750.00, 10.00,  35.00),
('LIGHT-UPLIGHT-LED',  15.00,   75.00,  225.00,  8.00,  25.00),
('PROJECTOR-4K',      125.00,  625.00, 1875.00, 12.00,  45.00),
('SCREEN-PROJ-120',    35.00,  175.00,  525.00,  8.00,  40.00),

-- CONSTRUCTION EQUIPMENT (Higher delivery fees) ------------------------
('LIFT-SCISSOR-19',   175.00,  875.00, 2625.00, 15.00, 125.00),
('LIFT-SCISSOR-26',   225.00, 1125.00, 3375.00, 15.00, 150.00),
('LIFT-BOOM-40',      350.00, 1750.00, 5250.00, 15.00, 175.00),
('GEN-5KW',            85.00,  425.00, 1275.00, 10.00,  65.00),
('GEN-10KW-DIESEL',   165.00,  825.00, 2475.00, 12.00,  95.00),
('COMPRESSOR-185CFM', 145.00,  725.00, 2175.00, 12.00,  85.00),
('SCAFFOLD-5x5x7',     65.00,  325.00,  975.00, 10.00,  55.00),

-- HEAVY EQUIPMENT (Premium pricing, high delivery) ---------------------
('FORKLIFT-5K',       450.00, 2250.00, 6750.00, 15.00, 200.00),
('SKIDSTEER-1800',    385.00, 1925.00, 5775.00, 15.00, 185.00),
('EXCAVATOR-MINI',    550.00, 2750.00, 8250.00, 15.00, 200.00),

-- CLIMATE CONTROL & SPECIALTY ------------------------------------------
('HEATER-PROPANE',     55.00,  275.00,  825.00, 10.00,  45.00),
('FAN-DRUM-36',        35.00,  175.00,  525.00,  8.00,  35.00)

ON DUPLICATE KEY UPDATE daily = VALUES(daily);


-- CUSTOMERS ============================================================
-- Tier A: VIP clients (15% discount eligible)
-- Tier B: Regular commercial clients (5% discount eligible)
-- Tier C: Walk-in / one-time customers (no discount)
-- =====================================================================

INSERT INTO customers (name, tier, default_location) VALUES
('Walk-In Customer',              'C', 'Plano, TX'),
('Dallas Event Planners LLC',     'B', 'Dallas, TX'),
('Fort Worth Convention Center',  'A', 'Fort Worth, TX'),
('Arlington Construction Co.',    'B', 'Arlington, TX'),
('Premier Events & Catering',     'A', 'Dallas, TX'),
('ABC Production Company',        'B', 'Plano, TX'),
('DFW Wedding Venue',             'A', 'Southlake, TX')
ON DUPLICATE KEY UPDATE tier = VALUES(tier);


-- POLICIES =============================================================
-- Tax rate, damage waiver, tier discounts, minimum rental periods
-- =====================================================================

INSERT INTO policies (key_name, value_json) VALUES
('tax_rate',
    JSON_OBJECT('pct', 8.25, 'description', 'Texas state + local sales tax')),

('default_damage_waiver',
    JSON_OBJECT('pct', 10.0, 'description', 'Standard damage waiver percentage')),

('tier_discounts',
    JSON_OBJECT(
        'A', JSON_OBJECT('pct', 15.0, 'description', 'VIP tier discount'),
        'B', JSON_OBJECT('pct', 5.0, 'description', 'Regular commercial discount'),
        'C', JSON_OBJECT('pct', 0.0, 'description', 'No discount for walk-ins')
    )),

('minimum_rental',
    JSON_OBJECT(
        'days', 1,
        'description', 'Minimum rental period is 1 day'
    )),

('delivery_zones',
    JSON_OBJECT(
        'local', JSON_OBJECT('radius_miles', 25, 'fee_multiplier', 1.0),
        'regional', JSON_OBJECT('radius_miles', 50, 'fee_multiplier', 1.5),
        'extended', JSON_OBJECT('radius_miles', 100, 'fee_multiplier', 2.0)
    ))

ON DUPLICATE KEY UPDATE value_json = VALUES(value_json);


-- =====================================================================
-- END OF SEED DATA
-- =====================================================================
-- Total Items: 30 across 5 categories
-- Price Range: $1.50/day (chairs) to $550/day (excavator)
-- Locations: Plano, Dallas, Fort Worth, Arlington, Southlake
-- =====================================================================
