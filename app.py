import os
import logging
import random
import datetime

from datetime import datetime, timedelta

from flask import Flask, redirect, render_template, request, send_from_directory, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect


app = Flask(__name__, static_folder='static')
csrf = CSRFProtect(app)

# WEBSITE_HOSTNAME exists only in production environment
if 'WEBSITE_HOSTNAME' not in os.environ:
    # local development, where we'll use environment variables
    print("Loading config.development and environment variables from .env file.")
    app.config.from_object('azureproject.development')
else:
    # production
    print("Loading config.production.")
    app.config.from_object('azureproject.production')

app.config.update(
    SQLALCHEMY_DATABASE_URI=app.config.get('DATABASE_URI'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

# Initialize the database connection
db = SQLAlchemy(app)

# Enable Flask-Migrate commands "flask db init/migrate/upgrade" to work
migrate = Migrate(app, db)

# The import must be done after db initialization due to circular import issue
from models import Restaurant, Review, Node, Group, TempData

@app.route('/', methods=['GET'])
def index():
    print('Request for index page received')
    groups = Group.query.all()
    group_node_counts = {group.id: len(group.nodes) for group in groups}
    nodes = Node.query.all()
    return render_template('index.html', nodes=nodes, group_node_counts=group_node_counts, groups=groups)

@app.route('/node/<int:id>', methods=['GET'])
def node_details(id):
    node = Node.query.get_or_404(id)
    temp_data = TempData.query.filter_by(node_id=id).all()
    
    # Convert TempData instances to dictionaries
    temp_data_dicts = [{
        'temp': data.temp,
        'time': data.time.isoformat(),  # Convert datetime to string
        'node_id': data.node_id
    } for data in temp_data]
    
    return render_template('node_details.html', node=node, temp_data=temp_data_dicts)

@app.route('/group/<int:id>', methods=['GET'])
def group_details(id):
    group = Group.query.get_or_404(id)
    nodes = Node.query.filter_by(group_id=id).all()
    
    group_data = []
    for node in nodes:
        node_temp_data = TempData.query.filter_by(node_id=node.id).all()

        # Convert each TempData instance to a dictionary
        formatted_node_data = [{
            'temp': data.temp,
            'time': data.time.isoformat(),  # Convert datetime to ISO format string
            'node_id': data.node_id
        } for data in node_temp_data]

        group_data.append({
            'nodeId': node.id,
            'temps': formatted_node_data
        })

    return render_template('group_details.html', group=group, nodes=nodes, group_data=group_data)

@app.route('/create', methods=['GET'])
def create_restaurant():
    print('Request for add restaurant page received')
    return render_template('create_restaurant.html')

@app.route('/create_mock_node', methods=['GET', 'POST'])
@csrf.exempt
def create_mock_node():
    if request.method == 'POST':
        try:
            node_id = request.form.get('id', type=int)
            name = request.form['name']
            group_id = request.form.get('group_id', type=int)
            location = request.form['location']

            new_node = Node(id=node_id, name=name, group_id=group_id, location=location)
            db.session.add(new_node)
            db.session.commit()

            # Generate random temperature data for this node
            generate_random_temp_data(new_node.id)

            return redirect(url_for('index'))  # Redirect after creating the node
        except Exception as e:
            # Handle exceptions and validation errors
            return render_template('create_mock_node.html', error_message=str(e))

    # GET request
    return render_template('create_mock_node.html')

@app.route('/create_group', methods=['GET', 'POST'])
@csrf.exempt
def create_group():
    print('Request for add group page received')
    if request.method == 'POST':
        group_id = request.form['group_id']
        group_name = request.form['group_name']
        selected_nodes = request.form.getlist('node_ids')

        # Create new group
        group = Group(id=group_id, name=group_name)
        db.session.add(group)

        # Associate selected nodes with this group
        for node_id in selected_nodes:
            node = Node.query.get(node_id)
            node.group_id = group_id
            db.session.add(node)

        db.session.commit()
        return redirect(url_for('index'))  # Redirect to the homepage or group list

    # For GET request, display form
    ungrouped_nodes = Node.query.filter_by(group_id=None).all()
    return render_template('create_group.html', ungrouped_nodes=ungrouped_nodes)

@app.route('/delete_node/<int:id>', methods=['POST'])
@csrf.exempt
def delete_node(id):
    node = Node.query.get_or_404(id)
    db.session.delete(node)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete_group/<int:id>', methods=['POST'])
@csrf.exempt
def delete_group(id):
    group = Group.query.get_or_404(id)
    db.session.delete(group)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/add', methods=['POST'])
@csrf.exempt
def add_restaurant():
    try:
        name = request.values.get('restaurant_name')
        street_address = request.values.get('street_address')
        description = request.values.get('description')
    except (KeyError):
        # Redisplay the question voting form.
        return render_template('add_restaurant.html', {
            'error_message': "You must include a restaurant name, address, and description",
        })
    else:
        restaurant = Restaurant()
        restaurant.name = name
        restaurant.street_address = street_address
        restaurant.description = description
        db.session.add(restaurant)
        db.session.commit()

        return redirect(url_for('details', id=restaurant.id))
    
#@app.route('/add_mock_node', methods=['POST'])
#@csrf.exempt
#def add_mock_node():
    # try:
    #     id = request.values.get('id')
    #     name = request.values.get('name')
    #     group_id = request.values.get('group_id')  # Assuming the form has a field for group_id
    #     if group_id:
    #         group_id = int(group_id)
    #     else:
    #         group_id = None
        

    #     location = request.values.get('location')
    #     #active = request.values.get('active', type=bool)
    #     #sleeptime = request.values.get('sleeptime', type=int)
    #     #interval_time = request.values.get('interval_time', type=int)
    # except KeyError as e:
    #     return render_template('create_node.html', error_message=f"Missing field: {e}")

    # node = Node(
    #     id=id,
    #     name=name,
    #     group_id=group_id,
    #     location=location
    # )
    # db.session.add(node)
    # db.session.commit()

    # return redirect(url_for('index'))

@app.route('/review/<int:id>', methods=['POST'])
@csrf.exempt
def add_review(id):
    try:
        user_name = request.values.get('user_name')
        rating = request.values.get('rating')
        review_text = request.values.get('review_text')
    except (KeyError):
        #Redisplay the question voting form.
        return render_template('add_review.html', {
            'error_message': "Error adding review",
        })
    else:
        review = Review()
        review.restaurant = id
        review.review_date = datetime.now()
        review.user_name = user_name
        review.rating = int(rating)
        review.review_text = review_text
        db.session.add(review)
        db.session.commit()

    return redirect(url_for('details', id=id))

@app.context_processor
def utility_processor():
    def star_rating(id):
        reviews = Review.query.where(Review.restaurant == id)

        ratings = []
        review_count = 0
        for review in reviews:
            ratings += [review.rating]
            review_count += 1

        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        stars_percent = round((avg_rating / 5.0) * 100) if review_count > 0 else 0
        return {'avg_rating': avg_rating, 'review_count': review_count, 'stars_percent': stars_percent}

    return dict(star_rating=star_rating)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

def generate_random_temp_data(node_id, count=100):
    for i in range(count):
        try:
            temp = random.uniform(-10, 40)  # Random temperature between -10 and 40 degrees Celsius
            time = datetime.now() - timedelta(days=random.randint(0, 365))  # Random time within the last year

            temp_data = TempData(temp=temp, time=time, node_id=node_id)
            db.session.add(temp_data)
        except Exception as e:
            print(f'Error creating TempData {i+1}: {e}')
            continue  # Continue with the next iteration in case of an error

    db.session.commit()


if __name__ == '__main__':
    app.run()
