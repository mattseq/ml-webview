from pymongo import MongoClient # type: ignore
from bson.objectid import ObjectId # type: ignore
import os

mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
mongo = MongoClient(mongo_uri)
db = mongo['webview']

runs_collection = db['runs']

def save_run(title, description, start_time, end_time, training_history):
    run_doc = {
        'title': title,
        'description': description,
        'start_time': start_time,
        'end_time': end_time,
        'training_history': training_history
    }
    
    result = runs_collection.insert_one(run_doc)
    return str(result.inserted_id)

def get_run(run_id):
    run = runs_collection.find_one({'_id': ObjectId(run_id)})
    if run:
        run['id'] = str(run['_id'])
        del run['_id']
    return run

def list_runs():
    runs = list(runs_collection.find().sort('start_time', -1))
    for run in runs:
        run['id'] = str(run['_id'])
        del run['_id']
    return runs