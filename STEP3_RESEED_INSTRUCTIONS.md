# Step 3: Database Re-seeding Instructions

## Overview
These instructions explain how to apply the enhanced seed data to your RentalAI Copilot database.

---

## Option 1: Using Docker Compose (Recommended)

### Prerequisites
- Docker and Docker Compose installed
- Terminal access with proper permissions

### Steps

#### 1. Backup Current Data (Optional but Recommended)
```bash
# Export current database
docker-compose exec db mysqldump -u por -ppor por > backup_$(date +%Y%m%d_%H%M%S).sql

# Or backup the entire database container
docker-compose exec db mysqldump -u por -ppor --all-databases > full_backup_$(date +%Y%m%d_%H%M%S).sql
```

#### 2. Stop Current Containers
```bash
docker-compose down
```

#### 3. Replace Seed File
```bash
# Backup original seed file
cp backend/db/seed.sql backend/db/seed.sql.backup

# Replace with enhanced seed data
cp backend/db/seed_enhanced.sql backend/db/seed.sql
```

#### 4. Remove Old Database Volume (Fresh Start)
```bash
# This will delete all existing data and start fresh
docker-compose down -v

# Verify volumes are removed
docker volume ls | grep por
```

#### 5. Start Fresh with New Seed Data
```bash
# Build and start containers
docker-compose up --build -d

# Watch logs to verify database initialization
docker-compose logs -f db
```

#### 6. Verify New Data Loaded
```bash
# Check item count (should be 30)
docker-compose exec db mysql -u por -ppor por -e "SELECT COUNT(*) as item_count FROM inventory;"

# Check customer count (should be 7)
docker-compose exec db mysql -u por -ppor por -e "SELECT COUNT(*) as customer_count FROM customers;"

# View sample items
docker-compose exec db mysql -u por -ppor por -e "SELECT sku, name, location FROM inventory LIMIT 10;"

# View price range
docker-compose exec db mysql -u por -ppor por -e "SELECT MIN(daily) as min_price, MAX(daily) as max_price FROM rates;"
```

---

## Option 2: Using Docker Without Compose

### Prerequisites
- Docker installed
- MySQL container running

### Steps

#### 1. Copy Enhanced Seed File into Container
```bash
# Copy the new seed file to the database container
docker cp backend/db/seed_enhanced.sql por_db:/tmp/seed_enhanced.sql
```

#### 2. Execute SQL File
```bash
# Connect to MySQL and run the seed file
docker exec -it por_db mysql -u por -ppor por -e "source /tmp/seed_enhanced.sql"
```

#### 3. Verify Data
```bash
# Check counts
docker exec -it por_db mysql -u por -ppor por -e "
  SELECT
    (SELECT COUNT(*) FROM inventory) as inventory_count,
    (SELECT COUNT(*) FROM rates) as rates_count,
    (SELECT COUNT(*) FROM customers) as customers_count,
    (SELECT COUNT(*) FROM policies) as policies_count;
"
```

---

## Option 3: Local MySQL (No Docker)

### Prerequisites
- MySQL 8.0+ installed locally
- Database `por` exists with proper credentials

### Steps

#### 1. Backup Current Database
```bash
mysqldump -u por -ppor por > backup_$(date +%Y%m%d_%H%M%S).sql
```

#### 2. Clear Existing Data (Optional - for fresh start)
```bash
mysql -u por -ppor por <<EOF
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE rates;
TRUNCATE TABLE inventory;
TRUNCATE TABLE customers;
DELETE FROM policies;
SET FOREIGN_KEY_CHECKS = 1;
EOF
```

#### 3. Load Enhanced Seed Data
```bash
mysql -u por -ppor por < backend/db/seed_enhanced.sql
```

#### 4. Verify Data
```bash
mysql -u por -ppor por -e "
  SELECT
    (SELECT COUNT(*) FROM inventory) as inventory_count,
    (SELECT COUNT(*) FROM rates) as rates_count,
    (SELECT COUNT(*) FROM customers) as customers_count,
    (SELECT COUNT(*) FROM policies) as policies_count;
"
```

---

## Option 4: Docker Compose with Live Update (No Downtime)

### Use Case
If you want to update seed data without recreating containers.

### Steps

#### 1. Copy File into Running Container
```bash
docker cp backend/db/seed_enhanced.sql por_db:/tmp/seed_enhanced.sql
```

#### 2. Execute in Running Database
```bash
docker-compose exec db mysql -u por -ppor por < /tmp/seed_enhanced.sql
```

#### 3. Verify
```bash
docker-compose exec db mysql -u por -ppor por -e "SELECT COUNT(*) FROM inventory;"
```

**Note:** This approach updates existing data using `ON DUPLICATE KEY UPDATE` clauses, so it won't delete existing runs/steps/feedback.

---

## Verification Checklist

After re-seeding, verify the following:

### ✓ Inventory Count
```sql
SELECT COUNT(*) FROM inventory;
-- Expected: 30
```

### ✓ Rates Count
```sql
SELECT COUNT(*) FROM rates;
-- Expected: 30
```

### ✓ Customers Count
```sql
SELECT COUNT(*) FROM customers;
-- Expected: 7
```

### ✓ Policies Count
```sql
SELECT COUNT(*) FROM policies;
-- Expected: 5
```

### ✓ Price Range
```sql
SELECT MIN(daily) as min_daily, MAX(daily) as max_daily FROM rates;
-- Expected: min=1.50, max=550.00
```

### ✓ Categories Present
```sql
SELECT
    JSON_EXTRACT(attributes, '$.category') as category,
    COUNT(*) as count
FROM inventory
GROUP BY category
ORDER BY count DESC;
-- Expected: event(11), av(7), construction(7), heavy(3), climate(2)
```

### ✓ Customer Tiers
```sql
SELECT tier, COUNT(*) as count FROM customers GROUP BY tier;
-- Expected: A(3), B(3), C(1)
```

### ✓ Foreign Key Integrity
```sql
-- All rates should have corresponding inventory items
SELECT COUNT(*)
FROM rates r
LEFT JOIN inventory i ON r.sku = i.sku
WHERE i.sku IS NULL;
-- Expected: 0 (no orphaned rates)
```

---

## Rollback Instructions

If you need to rollback to the original 3-item seed data:

### Using Docker Compose
```bash
# Stop containers
docker-compose down -v

# Restore original seed file
cp backend/db/seed.sql.backup backend/db/seed.sql

# Restart with original data
docker-compose up --build -d
```

### Using Backup File
```bash
# If you created a backup earlier
mysql -u por -ppor por < backup_YYYYMMDD_HHMMSS.sql

# Or with Docker
docker-compose exec db mysql -u por -ppor por < backup_YYYYMMDD_HHMMSS.sql
```

---

## Testing After Re-seeding

### Test 1: View Sample Inventory
```bash
docker-compose exec db mysql -u por -ppor por -e "
  SELECT sku, name, location, on_hand
  FROM inventory
  ORDER BY name
  LIMIT 10;
"
```

### Test 2: View Price Ranges by Category
```bash
docker-compose exec db mysql -u por -ppor por -e "
  SELECT
      JSON_EXTRACT(i.attributes, '$.category') as category,
      MIN(r.daily) as min_daily,
      MAX(r.daily) as max_daily,
      AVG(r.daily) as avg_daily
  FROM inventory i
  JOIN rates r ON i.sku = r.sku
  GROUP BY category
  ORDER BY avg_daily;
"
```

### Test 3: Test API with New Data
```bash
# Start backend (if not already running)
docker-compose up -d

# Test event rental quote
curl -X POST http://localhost:8000/quote/run \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Need 50 chairs and 5 tables for wedding this weekend",
    "customer_tier": "A",
    "location": "Dallas",
    "start_date": "2025-12-13",
    "end_date": "2025-12-14"
  }'

# Test construction equipment
curl -X POST http://localhost:8000/quote/run \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Need scissor lift for 3 days",
    "customer_tier": "B",
    "location": "Fort Worth",
    "start_date": "2025-12-10",
    "end_date": "2025-12-12"
  }'

# Test heavy equipment
curl -X POST http://localhost:8000/quote/run \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Need forklift for a week",
    "customer_tier": "C",
    "location": "Arlington",
    "start_date": "2025-12-09",
    "end_date": "2025-12-15"
  }'
```

---

## Troubleshooting

### Issue: "Access denied for user 'por'@'localhost'"
**Solution:** Check database credentials in `.env` or `docker-compose.yml`

### Issue: "Table doesn't exist"
**Solution:** Run schema.sql first:
```bash
docker-compose exec db mysql -u por -ppor por < backend/db/schema.sql
docker-compose exec db mysql -u por -ppor por < backend/db/seed_enhanced.sql
```

### Issue: "Cannot add foreign key constraint"
**Solution:** Ensure inventory items are inserted before rates:
The seed file is ordered correctly, but if you see this error, check that inventory is populated first.

### Issue: "Duplicate entry for key 'PRIMARY'"
**Solution:** This is expected with `ON DUPLICATE KEY UPDATE`. The seed file will update existing records rather than fail.

### Issue: Docker permission denied
**Solution:** Add your user to the docker group:
```bash
sudo usermod -aG docker $USER
newgrp docker
```

---

## Quick Reference Commands

### View All Inventory
```bash
docker-compose exec db mysql -u por -ppor por -e "SELECT * FROM inventory;"
```

### View All Rates
```bash
docker-compose exec db mysql -u por -ppor por -e "SELECT * FROM rates ORDER BY daily;"
```

### View All Customers
```bash
docker-compose exec db mysql -u por -ppor por -e "SELECT * FROM customers;"
```

### View All Policies
```bash
docker-compose exec db mysql -u por -ppor por -e "SELECT key_name, value_json FROM policies;"
```

### Interactive MySQL Shell
```bash
docker-compose exec db mysql -u por -ppor por
```

---

## Summary

**Recommended Approach:** Option 1 (Docker Compose with fresh start)

**Estimated Time:** 5-10 minutes

**Data Loss:** All existing runs, steps, and feedback will be cleared (fresh start)
- To preserve runs/steps/feedback: Use Option 4 (live update)

**Success Criteria:**
- ✓ 30 inventory items
- ✓ 7 customers with diverse tiers
- ✓ 5 policies including tier discounts
- ✓ API returns quotes with new inventory
- ✓ All verification queries pass

---

**Ready to proceed?** Choose your preferred option and follow the steps above.
