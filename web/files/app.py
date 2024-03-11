import pymongo
import bson
from datetime import datetime
import os
import hvac
from flask import Flask, render_template, request, url_for, flash, redirect, jsonify
from werkzeug.exceptions import abort


def connect_vault():
    vault_addr = os.getenv('VAULT_ADDR')
    if 'VAULT_TOKEN' in os.environ:
        vault_token = os.getenv('VAULT_TOKEN')
    else:
        vault_token = get_secret('VAULT_TOKEN')

    # Create a client
    vault_client = hvac.Client(
        url=vault_addr,
        token=vault_token
    )

    # Check if the client is authenticated
    if vault_client.is_authenticated():
        return vault_client
    else:
        return None

def get_secret(secret_name):
    try:
        with open(f'/run/secrets/{secret_name}', 'r') as secret_file:
            return secret_file.read().strip()
    except IOError:
        return None
    
def get_secret_from_vault(secret_name, key_name):
    vault_client = connect_vault()
    if vault_client is not None:
        # Read a secret
        secret = vault_client.secrets.kv.v2.read_secret_version(
            path=secret_name,
            mount_point='flask_blog',
        )
        # Get the data
        data = secret['data']['data']
        #print(data['Database'])
        return (data[key_name])
    else:
        return None

def get_db_connection():
    # Retrieve environment variables
    mongoHost = os.getenv('MONGO_DB_HOST')
    mongoPort = os.getenv('MONGO_DB_PORT', '27017')  # Default MongoDB port
    mongoDbName = get_secret_from_vault('MongoDB', 'Database')  # Specify the database name you want to use or access
    mongoUser = get_secret_from_vault('MongoDB', 'Username')
    mongoPassword = get_secret_from_vault('MongoDB', 'Password')

    # Construct the MongoDB Connection URL
    # Including the authSource parameter, which is typically 'admin' for MongoDB setups
    mongoURL = f"mongodb://{mongoUser}:{mongoPassword}@{mongoHost}:{mongoPort}/{mongoDbName}?authSource=admin"

    # Connect to MongoDB with authentication
    client = pymongo.MongoClient(mongoURL)
    conn = client[mongoDbName]

    return conn

def init_db():
    # Connect to MongoDB with authentication
    conn = get_db_connection()

    try:
        conn.validate_collection("posts")  # Try to validate a collection
    except pymongo.errors.OperationFailure:  # If the collection doesn't exist
        print("This collection doesn't exist, creating it now")
        postscol = conn["posts"]
        print(postscol)

        post_1 = {
            "_id" : "1",
            "created" : datetime.now(),
            "title" : "Post 1 title",
            "content" : "Post 1 content"
        }

        post_2 = {
            "_id" : "2",
            "created" : datetime.now(),
            "title" : "Post 2 title",
            "content" : "Post 2 content"
        }

        postscol.insert_many([post_1,post_2])
        print(conn.list_collection_names())

def get_post(post_id):
    conn = get_db_connection()
    coll = conn["posts"]
    if not bson.ObjectId.is_valid(post_id):
        # Handle the invalid post_id as you see fit
        print(f"{post_id} is not valid")
        return None
    post = coll.find_one({"_id": bson.ObjectId(oid=str(post_id))})
    if post is None:
        abort(404)
    return post


app = Flask(__name__)
app.config['SECRET_KEY'] = get_secret_from_vault('flask', 'FLASK_SECRET_KEY')

@app.route('/')
def index():
    conn = get_db_connection()
    coll = conn["posts"]
    posts = list(coll.find({}))
    serializedPosts = []

    for post in posts:
        post["_id"] = str(post["_id"])
        serializedPosts.append(post)

    return render_template('index.html', posts=serializedPosts)


@app.route('/<string:post_id>')
def post(post_id):
    post = get_post(post_id)
    return render_template('post.html', post=post)


@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            conn = get_db_connection()
            conn["posts"].insert_one(
                {"title": title, "content": content, "created": datetime.now()})
            return redirect(url_for('index'))

    return render_template('create.html')


@app.route('/<string:_id>/edit', methods=('GET', 'POST'))
def edit(_id):
    post = get_post(_id)

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            conn = get_db_connection()
            coll = conn["posts"]
            filter = {'_id': post["_id"]}
            update = {
                '$set': {
                    "title": title,
                    "content": content
                }
            }
            coll.update_one(filter, update)

            return redirect(url_for('index'))
    return render_template('edit.html', post=post)


@app.route('/<string:_id>/delete', methods=('POST',))
def delete(_id):
    post = get_post(_id)
    conn = get_db_connection()
    coll = conn["posts"]
    filter = {'_id': post["_id"]}
    coll.delete_one(filter)

    flash('"{}" was successfully deleted!'.format(post['title']))
    return redirect(url_for('index'))
