from bokeh.embed import components
from bokeh.resources import INLINE
from flask import Flask, render_template, current_app, Blueprint
import pandas as pd

from ui.webapi import api, systemapi, portalapi, mementoapi
from utils.plots import portalsScatter
from utils.snapshots import getWeekString
from db import DB
from ui.metrics import qa

import yaml

ui = Blueprint('ui', __name__, template_folder='templates', static_folder='static')
ui.add_app_template_filter(getWeekString)


def render(template, data=None, **kwargs):
    portalCount = current_app.config['portalCount']
    if data is None:
        data={}
    data['portalCount']=portalCount
    return render_template(template, data=data, **kwargs)


@ui.route("/", methods=['GET'])
def index():
    return render("index.jinja")


@ui.route('/quality', methods=['GET'])
def qualitymetrics():
    return render('quality_metrics.jinja', qa=qa)


@ui.route('/portalslist', methods=['GET'])
def portalslist():
    db=current_app.config['db']
    ps = db.get_portals()
    return render('odpw_portals.jinja', data={'portals':ps})


@ui.route('/about', methods=['GET'])
def about():
    return render('about.jinja')


@ui.route('/portal', methods=['GET'])
def portaldash():
    data={}
    db=current_app.config['db']
    return render("odpw_portaldash.jinja",  data=data)


@ui.route('/api', methods=['GET'])
def apispec():
    return render('apiui.jinja')


@ui.route('/sparql', methods=['GET'])
def sparqlendpoint():
    return render('sparql_endpoint.jinja', endpoint=current_app.config['endpoint'])


@ui.route('/portals/portalsstats', methods=['GET'])
def portalssize():
    db=current_app.config['db']
    # query portal snapshotcount, first and last snapshot, datasetcount, resourcecount
    # results=[row2dict(r) for r in s.query(Portal, Portal.snapshot_count,Portal.first_snapshot, Portal.last_snapshot, Portal.datasetcount, Portal.resourcecount)]
    results = {}
    df = pd.DataFrame(results)
    p = portalsScatter(df)
    script, div= components(p)

    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()

    return render("odpw_portals_stats.jinja",
        plot_script=script,
        plot_div=div,
        js_resources=js_resources,
        css_resources=css_resources
    )


@ui.route('/portalstable', methods=['GET'])
def portalstable():
    db = current_app.config['db']
    ps = db.get_portals()
    return render('odpw_portals_table.jinja', data={'portals':ps})


def create_app(conf, db):
    app = Flask(__name__)
    endpoint = conf['endpoint']
    app.config['db'] = db
    app.config['portalCount'] = db.get_portals_count()
    app.config['endpoint'] = endpoint

    app.register_blueprint(ui, url_prefix=conf['ui']['url_prefix_ui'])
    blueprint = Blueprint('api', __name__, url_prefix=conf['rest']['url_prefix_rest'])
    api.init_app(blueprint)

    bps = [systemapi, portalapi, mementoapi]
    for bp in bps:
        api.add_namespace(bp)
    app.register_blueprint(blueprint)
    return app



def name():
    return 'ODPWUI'


def help():
    return "Open Data Portal Watch User Interface"


def setupCLI(pa):
    pass


def cli(config, db, args):
    app = create_app(config, db)
    app.run(debug=True)


if __name__ == "__main__":
    with open("config.yaml", "r") as f:
        config = yaml.load(f)
    db = DB(config['endpoint'])
    app = create_app(config, db)
    app.run(debug=True)
