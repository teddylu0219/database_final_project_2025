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

echo "Recreating schema..."
$PSQL -f "$ROOT_DIR/schema.sql"

echo "Importing locations..."
$PSQL -c "\\copy locations(location_id,name,parent_id) FROM '$DATA_DIR/locations.csv' CSV HEADER"

echo "Importing categories..."
$PSQL -c "\\copy categories(category_id,category_name) FROM '$DATA_DIR/categories.csv' CSV HEADER"

echo "Importing stores..."
$PSQL -c "\\copy stores(store_id,store_name,location_id) FROM '$DATA_DIR/stores.csv' CSV HEADER"

echo "Importing business_hours..."
$PSQL -c "\\copy business_hours(store_id,day_of_week,no,open_time,close_time) FROM '$DATA_DIR/business_hours.csv' CSV HEADER"

echo "Importing store_categories..."
$PSQL -c "\\copy store_categories(store_id,category_id) FROM '$DATA_DIR/store_categories.csv' CSV HEADER"

echo "Importing foods..."
$PSQL -c "\\copy foods(food_id,food_name,price,calories,store_id) FROM '$DATA_DIR/foods.csv' CSV HEADER"

echo "Importing users..."
$PSQL -c "\\copy users(user_id,name,gender,age) FROM '$DATA_DIR/users.csv' CSV HEADER"

echo "Importing reviews..."
$PSQL -c "\\copy reviews(review_id,rating,cp_value,healthy,fullness,comment,user_id,food_id) FROM '$DATA_DIR/reviews.csv' CSV HEADER"

echo "Aligning sequences..."
$PSQL <<'SQL'
SELECT setval('locations_location_id_seq', COALESCE((SELECT MAX(location_id) FROM locations), 1), true);
SELECT setval('categories_category_id_seq', COALESCE((SELECT MAX(category_id) FROM categories), 1), true);
SELECT setval('stores_store_id_seq', COALESCE((SELECT MAX(store_id) FROM stores), 1), true);
SELECT setval('foods_food_id_seq', COALESCE((SELECT MAX(food_id) FROM foods), 1), true);
SELECT setval('users_user_id_seq', COALESCE((SELECT MAX(user_id) FROM users), 1), true);
SELECT setval('reviews_review_id_seq', COALESCE((SELECT MAX(review_id) FROM reviews), 1), true);
SQL

echo "Done. Sample data loaded."
