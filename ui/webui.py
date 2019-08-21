from bokeh.embed import components
from bokeh.resources import INLINE
from flask import Flask, render_template, current_app, Blueprint
import pandas as pd

from ui.webapi import api, systemapi, portalapi, mementoapi
from utils.plots import portalsScatter, qualityChart
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
    db=current_app.config['db']
    data=getPortalInfos(db, portalid, snapshot)

    portal = db.get_portal(portalid)
    portal.update(db.get_portal_info(portal['uri']))

    data['portal'] = portal
    return render("odpw_portal.jinja", snapshot=snapshot, portalid=portalid, data=data)



@ui.route('/portal/<portalid>/<int:snapshot>/quality', methods=['GET'])
def portalQuality(snapshot, portalid):
    db = current_app.config['db']
    #q = s.query(PortalSnapshotQuality) \
    #    .filter(PortalSnapshotQuality.portalid == portalid) \
    #    .filter(PortalSnapshotQuality.snapshot == snapshot)
    qdata = None


    portal = db.get_portal(portalid)
    quality = db.get_portal_quality(portal['uri'])
    d = []
    datasets = int(qdata['datasets'])
    for inD in qa:
        for k, v in inD['metrics'].items():
            k = k.lower()
            # TODO what to do if metric has no value?
            if qdata[k] != None and qdata[k] != 'None':
                value = float(qdata[k])
                perc = int(qdata[k + 'N']) / (datasets * 1.0) if datasets > 0 else 0
                c = {'Metric': k, 'Dimension': inD['dimension'],
                     'dim_color': inD['color'], 'value': value, 'perc': perc}
                c.update(v)
                d.append(c)

    data = getPortalInfos(db,portalid,snapshot)
    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()

    if d:
        df= pd.DataFrame(d)
        p = qualityChart(df)
        script, div= components(p)

        data['portals'] = db.get_portals()
        data['quality'] = qdata
        return render("odpw_portal_quality.jinja",
            plot_script=script
            ,plot_div=div
            ,js_resources=js_resources
            ,css_resources=css_resources
            ,snapshot=snapshot
            , portalid=portalid
            , data=data
            , qa=qa
        )
    else:
        return render("odpw_portal_quality.jinja",
                      snapshot=snapshot,
                      js_resources=js_resources,
                      css_resources=css_resources,
                      portalid=portalid,
                      data=data,
                      qa=qa
                      )



@ui.route('/portal/<portalid>/<int:snapshot>/evolution', methods=['GET'])
def portalEvolution(snapshot, portalid):
    db=current_app.config['dbc']
    data={}
    for R in s.query(PortalSnapshot).filter(PortalSnapshot.portalid==portalid):
        data[R.portalid+str(R.snapshot)]=row2dict(R)
    for R in s.query(PortalSnapshotQuality).filter(PortalSnapshotQuality.portalid==portalid):
        data[R.portalid+str(R.snapshot)].update(row2dict(R))

    df=pd.DataFrame([v for k,v in data.items()])
    p=evolutionCharts(df)
    script, div= components(p)

    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()

    data = getPortalInfos(db,portalid,snapshot)

    return render("odpw_portal_evolution.jinja",
        plot_script=script
        ,plot_div=div
        ,js_resources=js_resources
        ,css_resources=css_resources
        ,snapshot=snapshot
        , portalid=portalid
        , data=data
    )


@ui.route('/portal/<portalid>/<int:snapshot>/dataset', methods=['GET'], defaults={'dataset': None})
@ui.route('/portal/<portalid>/dataset/<path:dataset>', methods=['GET'], defaults={'snapshot': None})
@ui.route('/portal/<portalid>/<int:snapshot>/dataset/<path:dataset>', methods=['GET'])
def portalDataset(snapshot, portalid, dataset):
    if not snapshot:
        snapshot = getCurrentSnapshot()

    db=current_app.config['dbc']
    data = getPortalInfos(db,portalid,snapshot)
    data.update(getPortalDatasets(db, portalid, snapshot))

    dd=None
    if dataset:
        for dt in data['datasets']:
            if dt['id']==dataset:
                dd=dt
                break

        r= s.query(DatasetData).join(Dataset).filter(Dataset.id==dataset).join(DatasetQuality).add_entity(DatasetQuality).first()
        data['datasetData']=row2dict(r)
        software = s.query(Portal.software).filter(Portal.id==portalid).first()[0]
        if software == 'Socrata':
            data['json']=data['datasetData']['raw']['view']
        else:
            data['json']=data['datasetData']['raw']
        data['report']=dataset_reporter.report(r[0],r[1], software=None)

        #with Timer(key="getSchemadotorgDatasets", verbose=True):
        #    q = Session.query(Portal).filter(Portal.id == portalid)
        #    p = q.first()
        #    schemadotorg = json.dumps(dcat_to_schemadotorg.convert(p, r[0]), indent=3)

        q= s.query(MetaResource,ResourceInfo).filter(MetaResource.md5==r[0].md5).outerjoin(ResourceInfo, and_( ResourceInfo.uri==MetaResource.uri,ResourceInfo.snapshot==snapshot))
        data['resources']=[row2dict(r) for r in q.all()]
        for r in data['resources']:
            if 'header' in r and isinstance(r['header'], basestring):
                r['header']=ast.literal_eval(r['header'])


    q=s.query(Dataset.md5, func.min(Dataset.snapshot).label('min'), func.max(Dataset.snapshot).label('max')).filter(Dataset.id==dataset).group_by(Dataset.md5)
    r=[row2dict(r) for r in q.all()]
    versions={}
    for i in r:
        a=versions.setdefault(i['md5'],[])
        a.append({'min':i['min'],'max':i['max']})
    data['versions']=r

    return render("odpw_portal_dataset.jinja", data=data, snapshot=snapshot, portalid=portalid, dataset=dd, qa=qa, error=errorStatus)


@ui.route('/portal/<portalid>/<int:snapshot>/dist/formats', methods=['GET'])
def portalFormats(snapshot, portalid):
    db = current_app.config['dbc']
    data = getPortalInfos(db, portalid, snapshot)

    data['portals']= [ row2dict(r) for r in s.query(Portal).all()]
    data.update(aggregatePortalInfo(s, portalid,snapshot, limit=None))

    return render("odpw_portal_dist.jinja", data=data, snapshot=snapshot, portalid=portalid)


@ui.route('/portal/<portalid>/<int:snapshot>/resources', methods=['GET'])
def portalRes(portalid, snapshot=None):
    if not snapshot:
        snapshot = getCurrentSnapshot()
    db = current_app.config['dbc']
    data={}
    data.update(getPortalInfos(db, portalid, snapshot))
    return render("odpw_portal_resources.jinja",  data=data,snapshot=snapshot, portalid=portalid)



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
