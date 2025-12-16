#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$ROOT_DIR/data"

# Load DB config from .env if present
if [ -f "$ROOT_DIR/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
  set +a
fi

export PGDATABASE="${DB_NAME:-nycu_food}"
export PGUSER="${DB_USER:-$USER}"
export PGPASSWORD="${DB_PASSWORD:-}"
export PGHOST="${DB_HOST:-localhost}"
export PGPORT="${DB_PORT:-5432}"

PSQL="psql -v ON_ERROR_STOP=1"

echo "Exporting tables to $DATA_DIR ..."
$PSQL -c "\\copy (SELECT location_id,name,parent_id FROM locations ORDER BY location_id) TO '$DATA_DIR/locations.csv' CSV HEADER"
$PSQL -c "\\copy (SELECT category_id,category_name FROM categories ORDER BY category_id) TO '$DATA_DIR/categories.csv' CSV HEADER"
$PSQL -c "\\copy (SELECT store_id,store_name,location_id FROM stores ORDER BY store_id) TO '$DATA_DIR/stores.csv' CSV HEADER"
$PSQL -c "\\copy (SELECT store_id,day_of_week,no,open_time,close_time FROM business_hours ORDER BY store_id,day_of_week,no) TO '$DATA_DIR/business_hours.csv' CSV HEADER"
$PSQL -c "\\copy (SELECT store_id,category_id FROM store_categories ORDER BY store_id,category_id) TO '$DATA_DIR/store_categories.csv' CSV HEADER"
$PSQL -c "\\copy (SELECT food_id,food_name,price,calories,store_id FROM foods ORDER BY food_id) TO '$DATA_DIR/foods.csv' CSV HEADER"
$PSQL -c "\\copy (SELECT user_id,name,gender,age FROM users ORDER BY user_id) TO '$DATA_DIR/users.csv' CSV HEADER"
$PSQL -c "\\copy (SELECT review_id,rating,cp_value,healthy,fullness,comment,user_id,food_id FROM reviews ORDER BY review_id) TO '$DATA_DIR/reviews.csv' CSV HEADER"

echo "Done. CSVs updated."
