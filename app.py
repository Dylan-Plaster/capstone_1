from flask import Flask, render_template, request

app = Flask(__name__)

app.route('/')
def show_homepage():
    """show the homepage for the app"""
    return render_template('home.html')