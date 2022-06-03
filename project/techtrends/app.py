import sqlite3
import logging
import sys

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

connectionCount = 0


# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('./database.db')
    connection.row_factory = sqlite3.Row
    global connectionCount
    connectionCount += 1
    return connection


# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                              (post_id,)).fetchone()
    connection.close()
    return post


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'


# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)


# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.debug('Article not found!')
        return render_template('404.html'), 404
    else:
        app.logger.debug('Article "%s" retrieved!' % post['title'])
        return render_template('post.html', post=post)


# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('Rendering about us page!')
    return render_template('about.html')


# Define the post creation functionality
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            app.logger.debug('Creating new article: %s!', title)
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                               (title, content))
            connection.commit()
            connection.close()

            return redirect(url_for('index'))

    return render_template('create.html')


@app.route('/healthz')
def healthz():
    app.logger.debug('Retrieving application status')
    response = app.response_class(
        response=json.dumps({"result": "OK - healthy"}),
        status=200,
        mimetype='application/json'
    )
    return response


@app.route('/metrics')
def metrics():
    app.logger.info('Retrieving application metrics')

    posts = get_posts()
    # im assuming we count number of initiated connections instead of total number of concurrent active connections
    global connectionCount

    response = app.response_class(
        response=json.dumps({"db_connection_count": connectionCount, "post_count": len(posts)}),
        status=200,
        mimetype='application/json'
    )
    return response


def get_posts():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return posts


# start the application on port 3111
if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout,
                        level=logging.DEBUG,
                        format='%(levelname)s::%(name)s::%(asctime)s, %(message)s')
    app.run(host='0.0.0.0', port='3111')
