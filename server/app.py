#!/usr/bin/env python3

from models import db, Activity, Camper, Signup
from flask_restful import Api, Resource
from flask_migrate import Migrate
from flask import Flask, make_response, jsonify, request
import os
from flask_cors import CORS

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get(
    "DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)
api = Api(app)
CORS(app)

class Campers(Resource):
    def get(self):
        campers = [camper.to_dict(rules=('-signups',)) for camper in Camper.query.all()]
        
        if campers:
            response = make_response(
                campers, 200
            )
            return response
        else:
            return {'error': "Unexpected Server Error"}, 500
        
    def post(self):
        json = request.get_json()

        try:
            new_camper = Camper(
            name=json['name'],
            age=json['age'],
        )
            db.session.add(new_camper)
            db.session.commit()
        
        except ValueError as e:
            return {'errors': str(e)}, 400
        
        except Exception as e:
            return {'errors': 'Failed to add camper to database', 'message': str(e)}, 500

        camper_in_db = Camper.query.filter(
            Camper.name == json['name'], 
            Camper.age == json['age']
        ).first()

        camper_dict = camper_in_db.to_dict(rules=('-signups',))

        if camper_in_db:
            try:
                return camper_dict, 200
            
            except Exception as e:
                return {'errors': 'Camper not found'}, 400
        

class CampersById(Resource):
    def get(self, id):
        camper = Camper.query.filter(Camper.id == id).first()

        if camper:
            camper_dict = camper.to_dict()
            return camper_dict, 200
        else:
            return {'error': 'Camper not found'}, 404
        
    def patch(self, id):
        camper = Camper.query.filter(Camper.id == id).first()

        if camper:
            json = request.get_json()

            errors = []

            # Validate name is not empty
            if not json.get('name'):
                errors.append('validation errors')

            # Validate age is between 8 and 18
            age = json.get('age')
            if age is not None and (age < 8 or age > 18):
                errors.append('validation errors')

            if errors:
                return {'errors': errors}, 400

            # Update camper if no errors
            camper.name = json['name']
            camper.age = json['age']

            db.session.commit()

            return camper.to_dict(rules=('-signups',)), 202

        else:
            return {'error': ['Camper not found']}, 404
        
        
class Activities(Resource):
    def get(self):
        activities = [activity.to_dict(rules=('-signups',)) for activity in Activity.query.all()]

        return activities, 200
    

class ActivityById(Resource):
    def delete(self, id):
        activity = Activity.query.filter(Activity.id == id).first()

        if activity:
            db.session.delete(activity)
            db.session.commit()
            return {}, 204
        else:
            return {'error': 'Activity not found'}, 404

class Signups(Resource):
    def post(self):
        json = request.get_json()

        if json is None:
            return {'errors': ['No data provided']}, 400
        
        errors = []
        
        if not json.get('camper_id'):
            errors.append('validation errors')

        if not json.get('activity_id'):
            errors.append('validation errors')

        time = json.get('time')
        if time is not None and (time > 23 or time < 0):
            errors.append('validation errors')
        
        if errors:
            return {'errors': errors}, 400

        new_signup = Signup(
            camper_id=json['camper_id'],
            activity_id=json['activity_id'],
            time=json['time'],
        )

        db.session.add(new_signup)
        db.session.commit()

        new_signup_dict = new_signup.to_dict()

        response = make_response(
            new_signup_dict, 201
        )
        return response

api.add_resource(Campers, '/campers', endpoint='/campers')
api.add_resource(CampersById, '/campers/<int:id>')
api.add_resource(Activities, '/activities', endpoint='/activities')
api.add_resource(ActivityById, '/activities/<int:id>')
api.add_resource(Signups, '/signups')


@app.route('/')
def home():
    return ''

if __name__ == '__main__':
    app.run(port=5555, debug=True)



# What's the difference between setting serialization rules within the model vs inside the route views

# Can I implement GET (ALL) + GET_by_id using Flask RESTful?