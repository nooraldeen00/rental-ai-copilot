# backend/db/bootstrap.py
from __future__ import annotations
from sqlalchemy import text
from backend.db.connect import SessionLocal

DDL = """
CREATE TABLE IF NOT EXISTS runs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  input_text TEXT,
  seed INT,
  status VARCHAR(32),
  cost_usd DECIMAL(10,2) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS steps (
  id INT AUTO_INCREMENT PRIMARY KEY,
  run_id INT NOT NULL,
  kind VARCHAR(64) NOT NULL,
  input_json JSON NULL,
  output_json JSON NULL,
  duration_ms INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_steps_run_id (run_id),
  CONSTRAINT fk_steps_runs FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS policies (
  key_name VARCHAR(128) PRIMARY KEY,
  value_json JSON
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS inventory (
  sku VARCHAR(64) PRIMARY KEY,
  name VARCHAR(255) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS rates (
  sku VARCHAR(64) PRIMARY KEY,
  daily DECIMAL(10,2) NOT NULL,
  delivery_fee_base DECIMAL(10,2) DEFAULT 0,
  CONSTRAINT fk_rates_inventory FOREIGN KEY (sku) REFERENCES inventory(sku) ON DELETE CASCADE
) ENGINE=InnoDB;
"""

SEED = [
    (
        "INSERT INTO policies (key_name, value_json) VALUES "
        "('default_damage_waiver', JSON_OBJECT('pct', 8.0)) "
        "ON DUPLICATE KEY UPDATE value_json=VALUES(value_json);"
    ),
    (
        "INSERT INTO policies (key_name, value_json) VALUES "
        "('tax_rate', JSON_OBJECT('pct', 8.25)) "
        "ON DUPLICATE KEY UPDATE value_json=VALUES(value_json);"
    ),
    (
        "INSERT INTO inventory (sku, name) VALUES "
        "('CHAIR-FOLD','Folding Chair (White)'),"
        "('TENT-20x20','Tent 20x20'),"
        "('TABLE-8FT','8ft Banquet Table') "
        "ON DUPLICATE KEY UPDATE name=VALUES(name);"
    ),
    (
        "INSERT INTO rates (sku, daily, delivery_fee_base) VALUES "
        "('CHAIR-FOLD', 2.00, 25.00),"
        "('TENT-20x20', 150.00, 120.00),"
        "('TABLE-8FT', 10.00, 30.00) "
        "ON DUPLICATE KEY UPDATE daily=VALUES(daily), delivery_fee_base=VALUES(delivery_fee_base);"
    ),
]


def bootstrap():
    with SessionLocal() as s:
        # create tables
        for stmt in DDL.split(";"):
            if stmt.strip():
                s.execute(text(stmt))
        # seed basics
        for stmt in SEED:
            s.execute(text(stmt))
        s.commit()


if __name__ == "__main__":
    bootstrap()
    print("✅ DB bootstrapped (tables created + data seeded).")
