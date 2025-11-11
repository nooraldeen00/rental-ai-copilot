-- INVENTORY
CREATE TABLE IF NOT EXISTS inventory (
  sku VARCHAR(32) PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  location VARCHAR(64) NOT NULL,
  on_hand INT NOT NULL,
  committed INT NOT NULL DEFAULT 0,
  attributes JSON
);

-- RATES
CREATE TABLE IF NOT EXISTS rates (
  sku VARCHAR(32) PRIMARY KEY,
  daily DECIMAL(8,2) NOT NULL,
  weekly DECIMAL(8,2) NOT NULL,
  monthly DECIMAL(8,2) NOT NULL,
  damage_waiver_pct DECIMAL(5,2) NOT NULL,
  delivery_fee_base DECIMAL(8,2) NOT NULL
);

-- CUSTOMERS
CREATE TABLE IF NOT EXISTS customers (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  tier ENUM('A','B','C') DEFAULT 'C',
  default_location VARCHAR(64)
);

-- POLICIES
CREATE TABLE IF NOT EXISTS policies (
  key_name VARCHAR(64) PRIMARY KEY,
  value_json JSON NOT NULL
);

-- RUNS (agent runs)
CREATE TABLE IF NOT EXISTS runs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  input_text TEXT,
  seed INT,
  status VARCHAR(32),
  cost_usd DECIMAL(10,4),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- STEPS (agent trace)
CREATE TABLE IF NOT EXISTS steps (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  run_id BIGINT,
  kind VARCHAR(64),
  input_json JSON,
  output_json JSON,
  latency_ms INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE
);

-- FEEDBACK
CREATE TABLE IF NOT EXISTS feedback (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  run_id BIGINT,
  rating INT,
  note TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE
);

-- INDEXES (for speed)
CREATE INDEX idx_steps_runid       ON steps(run_id);
CREATE INDEX idx_steps_runid_kind  ON steps(run_id, kind);
CREATE INDEX idx_steps_created     ON steps(created_at);

CREATE INDEX idx_runs_created      ON runs(created_at);
CREATE INDEX idx_customers_tier    ON customers(tier);

-- extra FK to ensure rate SKU always exists in inventory
ALTER TABLE rates
  ADD CONSTRAINT fk_rates_inventory
  FOREIGN KEY (sku) REFERENCES inventory(sku)
  ON DELETE CASCADE;
