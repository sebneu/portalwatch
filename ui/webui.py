from bokeh.embed import components
from bokeh.resources import INLINE
from flask import Flask, render_template, current_app, Blueprint
import pandas as pd

from ui.webapi import api, systemapi, portalapi, mementoapi
from utils.plots import portalsScatter
from utils.snapshots import getWeekString, getCurrentSnapshot
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
    ps_info = db.get_portals_info()
    for p in ps:
        if p in ps_info:
            ps[p].update(ps_info[p])
    return render('odpw_portals.jinja', data={'portals': ps.values()})


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
    ps_info = db.get_portals_info()
    for p in ps:
        if p in ps_info:
            ps[p].update(ps_info[p])
    return render('odpw_portals_table.jinja', data={'portals': ps.values()})





def getPortalInfos(db, portalid, snapshot):
    snapshots = db.get_portal_snapshots(portalid)
    if snapshots.index(snapshot)-1 > 0:
        p = snapshots[snapshots.index(snapshot)-1]
    else:
        p = None

    if snapshots.index(snapshot) + 1 < len(snapshots):
        n = snapshots[snapshots.index(snapshot) + 1]
    else:
        n = None

    data={'snapshots':{'list': snapshots,'prev': p, 'next': n}}
    return data


@ui.route('/portal/<portalid>/', methods=['GET'])
@ui.route('/portal/<portalid>/<int:snapshot>', methods=['GET'])
def portal(portalid, snapshot=getCurrentSnapshot()):
    current_sn = snapshot
    db=current_app.config['db']
    data=getPortalInfos(db, portalid, snapshot)

    portal = db.get_portal(portalid)

    #q = s.query(Portal).filter(Portal.id == portalid) \
    #    .join(PortalSnapshotQuality, PortalSnapshotQuality.portalid == Portal.id) \
    #    .filter(PortalSnapshotQuality.snapshot == snapshot) \
    #    .join(PortalSnapshot, PortalSnapshot.portalid == Portal.id) \
    #    .filter(PortalSnapshot.snapshot == snapshot) \
    #    .add_entity(PortalSnapshot) \
    #    .add_entity(PortalSnapshotQuality)

    data['portal'] = portal['title']
    #data['fetchInfo'] = row2dict(r[1])
    #data['fetchInfo']['duration']=data['fetchInfo']['end']-data['fetchInfo']['start']

    return render("odpw_portal.jinja", snapshot=current_sn, portalid=portalid, data=data)


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
    app.run(debug=True, port=config['ui']['port'], host='0.0.0.0')


if __name__ == "__main__":
    with open("config.yaml", "r") as f:
        config = yaml.load(f)
    db = DB(config['endpoint'])
    app = create_app(config, db)
    app.run(debug=True)
