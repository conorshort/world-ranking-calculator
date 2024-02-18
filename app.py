from flask import Flask
from flask import render_template
from live_results import get_classes_for_event, get_results_in_class
app = Flask(__name__)


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/event/<int:event_id>")
def event(event_id):
    event_classes = get_classes_for_event(event_id)
    return render_template('event.html', event_id=event_id, event_classes=event_classes)


@app.route("/event/<int:event_id>/<class_id>")
def class_ranking(event_id, class_id):
    results = get_results_in_class(event_id, class_id)
    return render_template('results.html', results=results)