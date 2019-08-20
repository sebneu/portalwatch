from flask import current_app, Response
from flask_restplus import Api, Resource
import json

api = Api(version='1.1', title='ODPW Rest API', description='ODPW')


systemapi = api.namespace('system', description='Operations related to the set of all portals in the system')
portalapi = api.namespace('portal', description='Operations to retrieve information about a specific portal')
mementoapi = api.namespace('memento', description='Operations to retrieve historical dataset information')


@systemapi.route('/list')
class Portals(Resource):

    @systemapi.doc(description='Get a list of all portals (including the internal portal ID)')
    def get(self):
        """
        Returns list of portals.
        """
        db=current_app.config['db']
        data = db.get_portals()
        return Response(json.dumps(data), mimetype='application/json')

