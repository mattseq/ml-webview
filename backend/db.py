from typing import Any, Dict, List, Optional
import os
from flask_sqlalchemy import SQLAlchemy # type: ignore
from flask import Flask # type: ignore

db = SQLAlchemy()

class Run(db.Model):
    __tablename__ = 'runs'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_time = db.Column(db.BigInteger, nullable=False)
    end_time = db.Column(db.BigInteger, nullable=True)
    training_history = db.Column(db.PickleType, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'training_history': self.training_history
        }

def init_db(app):
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()

def save_run(title, description, start_time, end_time, training_history):
    run = Run(
        title=title,
        description=description,
        start_time=start_time,
        end_time=end_time,
        training_history=training_history
    )
    
    db.session.add(run)
    db.session.commit()
    return int(run.id)

def get_run(run_id):
    run = Run.query.get(run_id)
    if run:
        return run.to_dict()
    return None

def list_runs():
    rows = Run.query.order_by(Run.start_time.desc()).all()
    return [row.to_dict() for row in rows]

def delete_run(run_id):
    run = Run.query.get(run_id)
    if run:
        db.session.delete(run)
        db.session.commit()
        return run.to_dict()
    return None

def delete_all_runs():
    runs = Run.query.all()
    run_dicts = [run.to_dict() for run in runs]
    for run in runs:
        db.session.delete(run)
    db.session.commit()
    return run_dicts

def edit_run(run_id, title, description):
    run = Run.query.get(run_id)
    if run:
        if title is not None:
            run.title = title
        if description is not None:
            run.description = description
        db.session.commit()
        return run.to_dict()
    return None