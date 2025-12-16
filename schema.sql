-- NYCU Food Recommendation Database Schema

-- Drop tables if they exist (in reverse order of dependencies)
DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS foods CASCADE;
DROP TABLE IF EXISTS store_categories CASCADE;
DROP TABLE IF EXISTS business_hours CASCADE;
DROP TABLE IF EXISTS stores CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS locations CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 1. Locations Table
CREATE TABLE locations (
    location_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    parent_id INT REFERENCES locations(location_id) ON DELETE SET NULL
);

-- 2. Categories Table
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE
);

-- 3. Stores Table
CREATE TABLE stores (
    store_id SERIAL PRIMARY KEY,
    store_name VARCHAR(100) NOT NULL,
    location_id INT REFERENCES locations(location_id) ON DELETE SET NULL
);

-- 4. Business Hours Table
CREATE TABLE business_hours (
    store_id INT REFERENCES stores(store_id) ON DELETE CASCADE,
    day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
    no INT NOT NULL,
    open_time TIME NOT NULL,
    close_time TIME NOT NULL,
    PRIMARY KEY (store_id, day_of_week, no)
);

-- 5. Store Categories
CREATE TABLE store_categories (
    store_id INT REFERENCES stores(store_id) ON DELETE CASCADE,
    category_id INT REFERENCES categories(category_id) ON DELETE CASCADE,
    PRIMARY KEY (store_id, category_id)
);

-- 6. Foods Table
CREATE TABLE foods (
    food_id SERIAL PRIMARY KEY,
    food_name VARCHAR(100) NOT NULL,
    price DECIMAL(6,2) NOT NULL CHECK (price >= 0),
    calories INT CHECK (calories >= 0),
    store_id INT NOT NULL REFERENCES stores(store_id) ON DELETE CASCADE
);

-- 7. Users Table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    gender VARCHAR(10),
    age INT CHECK (age > 0 AND age < 150)
);

-- 8. Reviews Table
CREATE TABLE reviews (
    review_id SERIAL PRIMARY KEY,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    cp_value INT CHECK (cp_value BETWEEN 1 AND 5),
    healthy INT CHECK (healthy BETWEEN 1 AND 5),
    fullness INT CHECK (fullness BETWEEN 1 AND 5),
    comment TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    food_id INT NOT NULL REFERENCES foods(food_id) ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX idx_foods_store ON foods(store_id);
CREATE INDEX idx_reviews_food ON reviews(food_id);
CREATE INDEX idx_reviews_user ON reviews(user_id);
CREATE INDEX idx_stores_location ON stores(location_id);
CREATE INDEX idx_business_hours_store ON business_hours(store_id);
