import os
from flask import Flask, render_template, request, redirect, url_for, flash
from db import execute_query, execute_query_one

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ============ HOME ============

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

# ============ STORES CRUD ============

@app.route('/stores')
def stores_list():
    """List all stores with search and filter functionality"""
    # Get filter parameters
    search_query = request.args.get('search', '').strip()
    location_id = request.args.get('location_id', '').strip()
    category_id = request.args.get('category_id', '').strip()
    sort_by = request.args.get('sort_by', 'name').strip()

    # Base SQL query
    sql = """
        SELECT DISTINCT s.store_id, s.store_name, l.name as location_name,
               COALESCE(AVG(r.rating), 0) as avg_rating,
               COUNT(DISTINCT f.food_id) as food_count
        FROM stores s
        LEFT JOIN locations l ON s.location_id = l.location_id
        LEFT JOIN foods f ON s.store_id = f.store_id
        LEFT JOIN reviews r ON f.food_id = r.food_id
        LEFT JOIN store_categories sc ON s.store_id = sc.store_id
        WHERE 1=1
    """
    params = []

    # Apply search filter
    if search_query:
        sql += " AND s.store_name ILIKE %s"
        params.append(f'%{search_query}%')

    # Apply location filter
    if location_id:
        sql += " AND s.location_id = %s"
        params.append(location_id)

    # Apply category filter
    if category_id:
        sql += " AND sc.category_id = %s"
        params.append(category_id)

    sql += """
        GROUP BY s.store_id, s.store_name, l.name
    """
    # Apply sorting
    if sort_by == 'name':
        sql += " ORDER BY s.store_name ASC"
    elif sort_by == 'rating_desc':
        sql += " ORDER BY avg_rating DESC"
    elif sort_by == 'rating_asc':
        sql += " ORDER BY avg_rating ASC"
    elif sort_by == 'food_count_desc':
        sql += " ORDER BY food_count DESC"
    elif sort_by == 'food_count_asc':
        sql += " ORDER BY food_count ASC"
    else:
        sql += " ORDER BY s.store_id ASC"    

    stores = execute_query(sql, tuple(params) if params else None)

    # Get all locations and categories for filter dropdowns
    locations = execute_query("SELECT * FROM locations ORDER BY name")
    categories = execute_query("SELECT * FROM categories ORDER BY category_name")

    return render_template('stores/list.html',
                         stores=stores,
                         locations=locations,
                         categories=categories,
                         search_query=search_query,
                         selected_location=location_id,
                         selected_category=category_id,
                         sort_by=sort_by)

@app.route('/stores/<int:store_id>')
def store_detail(store_id):
    """Show store details including menu and reviews"""
    # Get store info
    store = execute_query_one("""
        SELECT s.*, l.name as location_name
        FROM stores s
        LEFT JOIN locations l ON s.location_id = l.location_id
        WHERE s.store_id = %s
    """, (store_id,))

    if not store:
        flash('Store not found')
        return redirect(url_for('stores_list'))

    # Get business hours
    hours = execute_query("""
        SELECT * FROM business_hours
        WHERE store_id = %s
        ORDER BY day_of_week, no
    """, (store_id,))

    # Get categories
    store_categories = execute_query("""
        SELECT c.category_name
        FROM store_categories sc
        JOIN categories c ON sc.category_id = c.category_id
        WHERE sc.store_id = %s
    """, (store_id,))

    # Get foods with average ratings
    foods = execute_query("""
        SELECT f.*,
               COALESCE(AVG(r.rating), 0) as avg_rating,
               COUNT(r.review_id) as review_count
        FROM foods f
        LEFT JOIN reviews r ON f.food_id = r.food_id
        WHERE f.store_id = %s
        GROUP BY f.food_id
        ORDER BY f.food_name
    """, (store_id,))

    # Get reviews with user info
    reviews = execute_query("""
        SELECT r.*, u.name as user_name, f.food_name
        FROM reviews r
        JOIN users u ON r.user_id = u.user_id
        JOIN foods f ON r.food_id = f.food_id
        WHERE f.store_id = %s
        ORDER BY r.timestamp DESC
        LIMIT 20
    """, (store_id,))

    # Get users for review form
    users = execute_query("SELECT * FROM users ORDER BY name")

    return render_template('stores/detail.html',
                         store=store,
                         hours=hours,
                         store_categories=store_categories,
                         foods=foods,
                         reviews=reviews,
                         users=users)

@app.route('/stores/create', methods=['GET', 'POST'])
def store_create():
    """Create a new store"""
    if request.method == 'POST':
        store_name = request.form.get('store_name', '').strip()
        location_id = request.form.get('location_id', '').strip()

        if not store_name:
            flash('Store name is required')
            return redirect(url_for('store_create'))

        try:
            execute_query("""
                INSERT INTO stores (store_name, location_id)
                VALUES (%s, %s)
            """, (store_name, location_id if location_id else None), fetch=False)

            flash('Store created successfully')
            return redirect(url_for('stores_list'))

        except Exception as e:
            flash(f'Error creating store: {str(e)}')
            return redirect(url_for('store_create'))

    # GET request
    locations = execute_query("SELECT * FROM locations ORDER BY name")
    return render_template('stores/create.html', locations=locations)

@app.route('/stores/<int:store_id>/edit', methods=['GET', 'POST'])
def store_edit(store_id):
    """Edit a store"""
    if request.method == 'POST':
        store_name = request.form.get('store_name', '').strip()
        location_id = request.form.get('location_id', '').strip()

        if not store_name:
            flash('Store name is required')
            return redirect(url_for('store_edit', store_id=store_id))

        try:
            execute_query("""
                UPDATE stores
                SET store_name = %s, location_id = %s
                WHERE store_id = %s
            """, (store_name, location_id if location_id else None, store_id), fetch=False)

            flash('Store updated successfully')
            return redirect(url_for('store_detail', store_id=store_id))

        except Exception as e:
            flash(f'Error updating store: {str(e)}')
            return redirect(url_for('store_edit', store_id=store_id))

    # GET request
    store = execute_query_one("SELECT * FROM stores WHERE store_id = %s", (store_id,))
    if not store:
        flash('Store not found')
        return redirect(url_for('stores_list'))

    locations = execute_query("SELECT * FROM locations ORDER BY name")
    return render_template('stores/edit.html', store=store, locations=locations)

@app.route('/stores/<int:store_id>/delete', methods=['POST'])
def store_delete(store_id):
    """Delete a store"""
    try:
        execute_query("DELETE FROM stores WHERE store_id = %s", (store_id,), fetch=False)
        flash('Store deleted successfully')
    except Exception as e:
        flash(f'Error deleting store: {str(e)}')

    return redirect(url_for('stores_list'))

# ============ FOODS CRUD ============

@app.route('/foods')
def foods_list():
    """List all foods"""
    # Get filter parameters
    search_query = request.args.get('search', '').strip()
    store_id = request.args.get('store_id', '').strip()
    min_price = request.args.get('min_price', '').strip()
    max_price = request.args.get('max_price', '').strip()
    sort_by = request.args.get('sort_by', 'id').strip()

    sql = """
        SELECT f.*, s.store_name,
               COALESCE(AVG(r.rating), 0) as avg_rating
        FROM foods f
        JOIN stores s ON f.store_id = s.store_id
        LEFT JOIN reviews r ON f.food_id = r.food_id
        WHERE 1=1
    """
    params = []

    if search_query:
        sql += " AND f.food_name ILIKE %s"
        params.append(f'%{search_query}%')

    if store_id:
        sql += " AND f.store_id = %s"
        params.append(store_id)

    if min_price:
        sql += " AND f.price >= %s"
        params.append(min_price)

    if max_price:
        sql += " AND f.price <= %s"
        params.append(max_price)
        
    
    sql += """
        GROUP BY f.food_id, s.store_name
    """


    if sort_by == 'price_asc':
        sql += " ORDER BY f.price ASC"
    elif sort_by == 'price_desc':
        sql += " ORDER BY f.price DESC"
    elif sort_by == 'rating_desc':
        sql += " ORDER BY avg_rating DESC"
    elif sort_by == 'rating_asc':
        sql += " ORDER BY avg_rating ASC"
    else:
        sql += " ORDER BY f.food_name ASC"

    foods = execute_query(sql, tuple(params) if params else None)
    stores = execute_query("SELECT * FROM stores ORDER BY store_name")

    return render_template('foods/list.html',
                         foods=foods,
                         stores=stores,
                         search_query=search_query,
                         selected_store=store_id,
                         min_price=min_price,
                         max_price=max_price,
                         sort_by=sort_by)

@app.route('/foods/create', methods=['POST'])
def food_create():
    """Create a new food item"""
    food_name = request.form.get('food_name', '').strip()
    price = request.form.get('price', '').strip()
    calories = request.form.get('calories', '').strip()
    store_id = request.form.get('store_id', '').strip()

    if not all([food_name, price, store_id]):
        flash('Food name, price, and store are required')
        return redirect(request.referrer or url_for('foods_list'))

    try:
        execute_query("""
            INSERT INTO foods (food_name, price, calories, store_id)
            VALUES (%s, %s, %s, %s)
        """, (food_name, price, calories if calories else None, store_id), fetch=False)

        flash('Food item created successfully')
    except Exception as e:
        flash(f'Error creating food item: {str(e)}')

    return redirect(request.referrer or url_for('foods_list'))

@app.route('/foods/<int:food_id>/edit', methods=['POST'])
def food_edit(food_id):
    """Edit a food item"""
    food_name = request.form.get('food_name', '').strip()
    price = request.form.get('price', '').strip()
    calories = request.form.get('calories', '').strip()

    if not all([food_name, price]):
        flash('Food name and price are required')
        return redirect(request.referrer or url_for('foods_list'))

    try:
        execute_query("""
            UPDATE foods
            SET food_name = %s, price = %s, calories = %s
            WHERE food_id = %s
        """, (food_name, price, calories if calories else None, food_id), fetch=False)

        flash('Food item updated successfully')
    except Exception as e:
        flash(f'Error updating food item: {str(e)}')

    return redirect(request.referrer or url_for('foods_list'))

@app.route('/foods/<int:food_id>/delete', methods=['POST'])
def food_delete(food_id):
    """Delete a food item"""
    try:
        execute_query("DELETE FROM foods WHERE food_id = %s", (food_id,), fetch=False)
        flash('Food item deleted successfully')
    except Exception as e:
        flash(f'Error deleting food item: {str(e)}')

    return redirect(request.referrer or url_for('foods_list'))


@app.route('/reviews/<int:review_id>/delete', methods=['POST'])
def review_delete(review_id):
    """Delete a review"""
    try:
        execute_query("DELETE FROM reviews WHERE review_id = %s", (review_id,), fetch=False)
        flash('Review deleted successfully')
    except Exception as e:
        flash(f'Error deleting review: {str(e)}')

    return redirect(request.referrer or url_for('index'))

# ============ ERROR HANDLERS ============

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.route('/foods/export')
def export_foods_csv():
    search = request.args.get('search', '').strip()
    store_id = request.args.get('store_id', '').strip()
    min_price = request.args.get('min_price', '').strip()
    max_price = request.args.get('max_price', '').strip()
    sort_by = request.args.get('sort_by', 'food_id').strip()

    sql = "SELECT f.*, s.store_name FROM foods f JOIN stores s ON f.store_id = s.store_id WHERE 1=1"
    params = []

    if search:
        sql += " AND f.food_name ILIKE %s"
        params.append(f"%{search}%")
    if store_id:
        sql += " AND f.store_id = %s"
        params.append(store_id)
    if min_price:
        sql += " AND f.price >= %s"
        params.append(min_price)
    if max_price:
        sql += " AND f.price <= %s"
        params.append(max_price)

    if sort_by in ['food_name', 'price', 'calories']:
        sql += f" ORDER BY {sort_by}"
    else:
        sql += " ORDER BY food_id"

    rows = execute_query(sql, tuple(params) if params else None)

    import io, csv
    output = io.StringIO()
    output.write('\ufeff')  
    writer = csv.writer(output)
    writer.writerow(['ID', '食物名稱', '餐廳', '價格', '卡路里'])
    for row in rows:
        writer.writerow([row['food_id'], row['food_name'], row['store_name'], row['price'], row['calories']])

    from flask import Response
    return Response(
        output.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={"Content-Disposition": "attachment; filename=foods.csv"}
    )


# ============ REVIEWS CRUD ============

@app.route('/reviews/create', methods=['POST'])
def review_create():
    """Create a new review"""
    rating = request.form.get('rating', '').strip()
    cp_value = request.form.get('cp_value', '').strip()
    healthy = request.form.get('healthy', '').strip()
    fullness = request.form.get('fullness', '').strip()
    comment = request.form.get('comment', '').strip()
    user_id = request.form.get('user_id', '').strip()
    food_id = request.form.get('food_id', '').strip()

    if not all([user_id, food_id]):
        flash('User and food are required')
        return redirect(request.referrer or url_for('index'))

    try:
        execute_query("""
            INSERT INTO reviews (rating, cp_value, healthy, fullness, comment, user_id, food_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            rating if rating else None,
            cp_value if cp_value else None,
            healthy if healthy else None,
            fullness if fullness else None,
            comment if comment else None,
            user_id,
            food_id
        ), fetch=False)

        flash('Review created successfully')
    except Exception as e:
        flash(f'Error creating review: {str(e)}')

    return redirect(request.referrer or url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)





