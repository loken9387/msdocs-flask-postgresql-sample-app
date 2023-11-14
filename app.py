import os
from datetime import datetime

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
from models import Restaurant, Review

@app.route('/', methods=['GET'])
def index():
    print('Request for index page received')
    groups = Group.query.all()
    nodes = Node.query.all()
    return render_template('index.html', groups=groups, nodes=nodes)

# This method will be used to display details and change details of the node
@app.route('/node/<int:id>', methods=['GET'])
def node_details(id):
    node = Node.query.get_or_404(id)
    temp_data = TempData.query.filter_by(node_id=id).all()
    return render_template('node_details.html', node=node, temp_data=temp_data)

@app.route('/node/update/<int:id>', methods=['POST'])
def update_node(id):
    node = Node.query.get_or_404(id)
    node.name = request.form['node_name']
    node.sleeptime = request.form['node_sleeptime']
    node.interval_time = request.form['node_interval_time']
    
    group_id = request.form['node_group']
    if group_id:
        node.group = Group.query.get(group_id)
    else:
        node.group = None
    
    db.session.commit()
    # Redirect to the node details page or wherever appropriate
    return redirect(url_for('node_details', id=node.id))
    

# This method will be used to display details of groups and delete groups 
@app.route('/group/<int:id>', methods=['GET'])
def group_details(id):
    group = Group.query.get_or_404(id)
    return render_template('group_details.html', group=group)

# This method will be used to create new groups
@app.route('/create', methods=['GET'])
def create_group():
    print('Request for add group page received')
    return render_template('create_group.html')

@app.route('/add', methods=['POST'])
@csrf.exempt
def add_group():
    try:
        group_id = request.values.get('group_id')
        name = request.values.get('group_name')
        selected_nodes = request.values.getlist('nodes')
    except (KeyError):
        # Redisplay the group creation form.
        return render_template('create_group.html', {
            'error_message': "You must include a group ID and name",
        })
    else:
        group = Group()
        group.id = group_id
        group.name = name
        db.session.add(group)
        db.session.flush()  # Flush to get the group ID if it's auto-generated

        # Assign selected nodes to the group
        nodes_to_assign = Node.query.filter(Node.id.in_(selected_nodes)).all()
        for node in nodes_to_assign:
            node.group_id = group.id

        db.session.commit()

        # Redirect to a details page or another appropriate page
        return redirect(url_for('group_details', id=group.id))

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

if __name__ == '__main__':
    app.run()
