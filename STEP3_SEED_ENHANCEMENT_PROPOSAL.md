# Step 3: Database Seed Data Enhancement Proposal

## Overview
This proposal expands the RentalAI Copilot inventory from **3 items** to **30 items** across multiple rental categories with realistic pricing and customer tiers.

---

## Current vs. Enhanced Comparison

### Current State (seed.sql)
```sql
INVENTORY: 3 items
  - CHAIR-FOLD (White folding chair)
  - TENT-20x20 (20x20 tent)
  - TABLE-8FT (8ft table)

CUSTOMERS: 2 customers
  - Walk-In Customer (Tier C)
  - VIP Client (Tier A)

POLICIES: 2 policies
  - tax_rate: 8.25%
  - default_damage_waiver: 10%

PRICE RANGE: $1.50/day - $150/day
```

### Enhanced State (seed_enhanced.sql)
```sql
INVENTORY: 30 items across 5 categories
  - Event/Party (11 items): Chairs, tables, linens, tents, staging
  - Audio/Visual (7 items): Speakers, mics, mixers, lights, projectors
  - Construction (7 items): Lifts, generators, compressors, scaffolding
  - Heavy Equipment (3 items): Forklift, skid steer, excavator
  - Climate Control (2 items): Heaters, fans

CUSTOMERS: 7 customers with meaningful tiers
  - 3 Tier A (VIP): 15% discount eligible
  - 3 Tier B (Regular commercial): 5% discount eligible
  - 1 Tier C (Walk-in): No discount

POLICIES: 5 policies
  - tax_rate: 8.25% (Texas sales tax)
  - default_damage_waiver: 10%
  - tier_discounts: A=15%, B=5%, C=0%
  - minimum_rental: 1 day
  - delivery_zones: Local/Regional/Extended with fee multipliers

PRICE RANGE: $1.50/day (folding chair) - $550/day (excavator)
LOCATIONS: Plano, Dallas, Fort Worth, Arlington, Southlake
```

---

## Detailed Inventory Breakdown

### 1. Event / Party Rentals (11 items)
**Use Case:** Weddings, corporate events, parties, conferences

| SKU | Item | Daily Rate | Category |
|-----|------|------------|----------|
| CHAIR-FOLD-WHT | Folding Chair - White Plastic | $1.50 | Budget |
| CHAIR-CHIAVARI | Chiavari Chair - Gold | $4.00 | Premium |
| TABLE-6FT-RECT | 6ft Rectangular Table | $8.00 | Basic |
| TABLE-8FT-RECT | 8ft Rectangular Table | $10.00 | Basic |
| TABLE-60RND | 60" Round Table | $12.00 | Mid-range |
| LINEN-120RND-WHT | 120" Tablecloth - White | $8.00 | Basic |
| LINEN-120RND-BLK | 120" Tablecloth - Black | $8.00 | Basic |
| TENT-10x10 | 10x10 Pop-Up Tent | $45.00 | Basic |
| TENT-20x20 | 20x20 Frame Tent | $150.00 | Mid-range |
| TENT-40x60 | 40x60 Pole Tent | $450.00 | Premium |
| STAGE-4x8 | 4x8 Stage Platform | $25.00 | Mid-range |

**AI Recognition:** Chair, table, tent, linen, stage, tablecloth

### 2. Audio / Visual Equipment (7 items)
**Use Case:** Conferences, weddings, concerts, presentations

| SKU | Item | Daily Rate | Category |
|-----|------|------------|----------|
| SPEAKER-PA-BASIC | PA Speaker System - 500W | $75.00 | Mid-range |
| SPEAKER-PA-PRO | Professional PA - 2000W | $150.00 | Premium |
| MIC-WIRELESS-HH | Wireless Handheld Mic | $25.00 | Basic |
| MIXER-8CH | 8-Channel Audio Mixer | $50.00 | Mid-range |
| LIGHT-UPLIGHT-LED | LED Uplight - RGBA | $15.00 | Basic |
| PROJECTOR-4K | 4K Projector - 5000 Lumens | $125.00 | Premium |
| SCREEN-PROJ-120 | 120" Projection Screen | $35.00 | Mid-range |

**AI Recognition:** Speaker, sound, audio, PA system, microphone, mic, mixer, lighting, light, uplight, projector, screen

### 3. Construction Equipment (7 items)
**Use Case:** Construction sites, maintenance, renovations

| SKU | Item | Daily Rate | Category |
|-----|------|------------|----------|
| LIFT-SCISSOR-19 | 19ft Electric Scissor Lift | $175.00 | Premium |
| LIFT-SCISSOR-26 | 26ft Electric Scissor Lift | $225.00 | Premium |
| LIFT-BOOM-40 | 40ft Telescopic Boom Lift | $350.00 | Premium |
| GEN-5KW | 5kW Portable Generator | $85.00 | Mid-range |
| GEN-10KW-DIESEL | 10kW Diesel Generator | $165.00 | Premium |
| COMPRESSOR-185CFM | 185 CFM Air Compressor | $145.00 | Premium |
| SCAFFOLD-5x5x7 | 5x5x7 Frame Scaffold | $65.00 | Mid-range |

**AI Recognition:** Scissor lift, boom lift, lift, aerial lift, generator, power, compressor, air compressor, scaffold, scaffolding

### 4. Heavy Equipment (3 items)
**Use Case:** Construction, landscaping, demolition, material handling

| SKU | Item | Daily Rate | Category |
|-----|------|------------|----------|
| FORKLIFT-5K | 5,000 lb Forklift - Propane | $450.00 | Premium |
| SKIDSTEER-1800 | 1,800 lb Skid Steer Loader | $385.00 | Premium |
| EXCAVATOR-MINI | Mini Excavator - 3 Ton | $550.00 | Premium |

**AI Recognition:** Forklift, skid steer, skidsteer, bobcat, excavator, digger, loader

### 5. Climate Control & Specialty (2 items)
**Use Case:** Temperature control for events and construction

| SKU | Item | Daily Rate | Category |
|-----|------|------------|----------|
| HEATER-PROPANE | Propane Heater - 200K BTU | $55.00 | Mid-range |
| FAN-DRUM-36 | 36" Drum Fan - High Velocity | $35.00 | Mid-range |

**AI Recognition:** Heater, heating, fan, cooling, ventilation

---

## Pricing Strategy

### Price Distribution
- **Budget ($1-10/day):** 5 items (17%) - Chairs, linens, basic tables
- **Mid-range ($10-100/day):** 13 items (43%) - Tables, tents, A/V, generators
- **Premium ($100-300/day):** 9 items (30%) - Lifts, projectors, large tents
- **High-end ($300-600/day):** 3 items (10%) - Heavy equipment

### Delivery Fees by Category
- **Event/Party:** $15-$200 (based on size)
- **Audio/Visual:** $25-$75 (moderate transport)
- **Construction:** $55-$175 (heavy equipment)
- **Heavy Equipment:** $185-$200 (specialized transport)

### Damage Waiver Rates
- **Low risk (5%):** Chairs, tables, linens
- **Medium risk (8-10%):** Tents, A/V equipment, basic construction
- **High risk (12-15%):** Lifts, heavy equipment

---

## Enhanced Customer Tiers

### Tier A - VIP Clients (3 customers)
**Discount:** 15%
**Examples:**
- Fort Worth Convention Center
- Premier Events & Catering
- DFW Wedding Venue

**Characteristics:** High volume, repeat business, excellent credit

### Tier B - Regular Commercial (3 customers)
**Discount:** 5%
**Examples:**
- Dallas Event Planners LLC
- Arlington Construction Co.
- ABC Production Company

**Characteristics:** Regular business, good payment history

### Tier C - Walk-in / One-time (1 customer)
**Discount:** 0%
**Examples:**
- Walk-In Customer

**Characteristics:** First-time or infrequent rentals

---

## Enhanced Policies

### New Policies Added

**1. tier_discounts**
```json
{
  "A": {"pct": 15.0, "description": "VIP tier discount"},
  "B": {"pct": 5.0, "description": "Regular commercial discount"},
  "C": {"pct": 0.0, "description": "No discount for walk-ins"}
}
```

**2. minimum_rental**
```json
{
  "days": 1,
  "description": "Minimum rental period is 1 day"
}
```

**3. delivery_zones**
```json
{
  "local": {"radius_miles": 25, "fee_multiplier": 1.0},
  "regional": {"radius_miles": 50, "fee_multiplier": 1.5},
  "extended": {"radius_miles": 100, "fee_multiplier": 2.0}
}
```

---

## How This Improves Demo Capabilities

### 1. Diverse Use Cases
- **Events:** "Need 100 chairs and 10 tables for wedding"
- **Construction:** "Need scissor lift for 3 days"
- **A/V:** "Need sound system and projector for conference"
- **Heavy Equipment:** "Need excavator for week-long project"

### 2. Price Range Demonstrations
- Show how AI handles budget rentals ($150 total)
- Show mid-range events ($2,000 total)
- Show large construction projects ($10,000+ total)

### 3. Multi-Category Quotes
```
"Need chairs, tables, tent, and sound system for outdoor wedding"
→ AI selects from Event + A/V categories
```

### 4. Tier-Based Pricing
- Same quote for Tier A customer: 15% cheaper
- Shows dynamic pricing based on customer relationship

### 5. Realistic Pricing
- All prices based on actual rental market rates
- Weekly = 5x daily (industry standard)
- Monthly = 15x daily (industry standard)

---

## AI Recognition Improvements

### Natural Language Examples

**Before (3 items):**
- "Need chairs" → ✓ CHAIR-FOLD
- "Need tables" → ✓ TABLE-8FT
- "Need tent" → ✓ TENT-20x20
- "Need speakers" → ✗ Not found (fallback)
- "Need lift" → ✗ Not found (fallback)

**After (30 items):**
- "Need chairs for wedding" → ✓ CHAIR-FOLD-WHT or CHAIR-CHIAVARI
- "Need round tables" → ✓ TABLE-60RND
- "Need linens" → ✓ LINEN-120RND-WHT/BLK
- "Need sound system" → ✓ SPEAKER-PA-BASIC or SPEAKER-PA-PRO
- "Need scissor lift" → ✓ LIFT-SCISSOR-19 or LIFT-SCISSOR-26
- "Need generator" → ✓ GEN-5KW or GEN-10KW-DIESEL
- "Need excavator" → ✓ EXCAVATOR-MINI
- "Need heater for outdoor event" → ✓ HEATER-PROPANE

### SKU Naming Convention
All SKUs follow pattern: `CATEGORY-SIZE/TYPE-VARIANT`
- Easy for AI to parse
- Human-readable
- Consistent structure

---

## Database Compatibility

### Schema Compliance ✓
- No schema changes required
- All foreign key constraints respected
- Uses existing table structure
- JSON attributes for flexibility

### MySQL Compatibility ✓
- Standard INSERT...ON DUPLICATE KEY UPDATE syntax
- JSON_OBJECT() functions (MySQL 5.7+)
- ENUM types for tier field
- DECIMAL types for pricing

### Data Integrity ✓
- All rates have corresponding inventory items (FK constraint)
- Customer tiers use existing ENUM values (A, B, C)
- Policies use JSON for flexibility
- No orphaned records

---

## Testing Recommendations

### After Re-seeding

**1. Verify Item Count:**
```sql
SELECT COUNT(*) FROM inventory;  -- Should be 30
SELECT COUNT(*) FROM rates;       -- Should be 30
SELECT COUNT(*) FROM customers;   -- Should be 7
SELECT COUNT(*) FROM policies;    -- Should be 5
```

**2. Test Price Ranges:**
```sql
SELECT MIN(daily), MAX(daily) FROM rates;
-- Should show: 1.50 to 550.00
```

**3. Test Categories:**
```sql
SELECT
    JSON_EXTRACT(attributes, '$.category') as category,
    COUNT(*) as items
FROM inventory
GROUP BY category;
```

**4. Test AI Quote Generation:**
```bash
# Test event rental
curl -X POST http://localhost:8000/quote/run -d '{
  "message": "Need 50 chairs, 5 tables, and a tent for weekend wedding",
  "customer_tier": "A"
}'

# Test construction rental
curl -X POST http://localhost:8000/quote/run -d '{
  "message": "Need 19ft scissor lift for 3 days",
  "customer_tier": "B"
}'

# Test A/V rental
curl -X POST http://localhost:8000/quote/run -d '{
  "message": "Need sound system and projector for conference",
  "customer_tier": "C"
}'
```

---

## Files Changed

### New File Created:
- `backend/db/seed_enhanced.sql` - Enhanced seed data (30 items)

### File to be Replaced:
- `backend/db/seed.sql` - Current seed data (3 items)

**Note:** Original `seed.sql` will be backed up before replacement.

---

## Re-seeding Instructions

See next section for detailed commands...
