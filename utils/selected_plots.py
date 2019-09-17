from bokeh.core.properties import value
from bokeh.io import show, output_file
from bokeh.plotting import figure
from bokeh.palettes import brewer
from bokeh.models import HoverTool

import collections

from ui.metrics import qa
from utils.snapshots import getDateString
PLOT_HEIGHT=600
PLOT_WIDTH=1000
LINE_WIDTH=4


def num_portals(db, portals, snapshots):
    portals_num = {}
    for sn in snapshots:
        portals_num[sn] = collections.defaultdict(dict)
        for p in portals:
            p_info = db.get_portal_info(p, sn)
            portals_num[sn][p] = 1 if p_info['datasets'] > 0 else 0

    dates = [getDateString(sn) for sn in snapshots]
    colors = brewer['BrBG'][len(portals)]

    sorted_portals_num = collections.defaultdict(list)
    for sn in snapshots:
        for portal in portals:
            sorted_portals_num[portal].append(portals_num[sn][portal])

    data = {'dates': dates}
    for portal in portals:
        data[portal] = sorted_portals_num[portal]

    p = figure(x_range=dates, plot_height=PLOT_HEIGHT, plot_width=PLOT_WIDTH,
               toolbar_location=None, tools="hover", tooltips="@{dates}: $name")

    p.vbar_stack(portals, x='dates', width=0.9, color=colors, source=data, legend=[value(x) for x in portals])

    p.y_range.start = 0
    p.y_range.end = len(portals)
    p.x_range.range_padding = 0.1
    p.xgrid.grid_line_color = None
    p.axis.minor_tick_line_color = None
    p.outline_line_color = None
    p.legend.location = "top_left"
    return p


def dataset_evolution(db, portals, snapshots):
    info = {}
    for sn in snapshots:
        info[sn] = collections.defaultdict(int)
        for p in portals:
            p_info = db.get_portal_info(p, sn)
            info[sn]['datasets'] += p_info['datasets']
            info[sn]['resources'] += p_info['resources']

    dates = [getDateString(sn) for sn in snapshots]

    sorted_formats = collections.defaultdict(list)
    format_labels = []
    for label in ['datasets', 'resources']:
        format_labels.append(label)
        for sn in snapshots:
            sorted_formats[label].append(info[sn][label] if label in info[sn] else 0)

    colors = [brewer['BrBG'][3][0], brewer['BrBG'][3][2]]

    data = {'dates': dates}
    for l in format_labels:
        data[l] = sorted_formats[l]

    p = figure(x_range=dates, plot_height=PLOT_HEIGHT, plot_width=PLOT_WIDTH,
               toolbar_location=None, tools="hover", tooltips="$name @dates: @$name")

    p.vbar_stack(format_labels, x='dates', width=0.9, color=colors, source=data,
                 legend=[value(x) for x in format_labels])

    p.y_range.start = 0
    p.x_range.range_padding = 0.1
    p.xgrid.grid_line_color = None
    p.axis.minor_tick_line_color = None
    p.outline_line_color = None
    p.legend.location = "top_left"
    p.legend.orientation = "horizontal"
    return p


def format_evolution(db, portals, snapshots):
    formats = {}
    for sn in snapshots:
        formats[sn] = collections.defaultdict(int)
        for p in portals:
            p_formats = db.get_portal_formats(p, sn)
            for f in p_formats:
                formats[sn][f['label']] += f['count']

    dates = [getDateString(sn) for sn in snapshots]

    tf = sorted(formats[snapshots[-1]].items(), key=lambda k_v: k_v[1], reverse=True)[:10]
    sorted_formats = collections.defaultdict(list)
    format_labels = []
    for f in tf:
        label = f[0]
        format_labels.append(label)
        for sn in snapshots:
            sorted_formats[label].append(formats[sn][label] if label in formats[sn] else 0)

    colors = brewer['BrBG'][10]

    data = {'dates': dates}
    for l in format_labels:
        data[l] = sorted_formats[l]

    p = figure(x_range=dates, plot_height=PLOT_HEIGHT, plot_width=PLOT_WIDTH,
               toolbar_location=None, tools="hover", tooltips="$name @dates: @$name")

    p.vbar_stack(format_labels, x='dates', width=0.9, color=colors, source=data,
                 legend=[value(x) for x in format_labels])

    p.y_range.start = 0
    p.x_range.range_padding = 0.1
    p.xgrid.grid_line_color = None
    p.axis.minor_tick_line_color = None
    p.outline_line_color = None
    p.legend.location = "top_left"
    p.legend.orientation = "horizontal"

    return p


def format_per_portal(db, portals, snapshots, format='csv'):
    format_counts = {}
    for i, portal in enumerate(portals):
        format_counts[portal] = []
        for sn in snapshots:
            count = db.get_portal_format_count(portal, format, sn)
            if count > 0:
                format_counts[portal].append(count)
            else:
                format_counts[portal].append(None)

    colors = brewer['BrBG'][len(portals)]
    dates = [getDateString(sn) for sn in snapshots]

    data = {'dates': dates}
    for portal in portals:
        data[portal] = format_counts[portal]

    p = figure(x_range=dates, plot_height=PLOT_HEIGHT, plot_width=PLOT_WIDTH,
               toolbar_location=None, tools="hover", tooltips="$name @dates: @$name")

    for i, portal in enumerate(format_counts):
        line = p.line(x='dates', y=portal, line_width=LINE_WIDTH, legend=dict(value=portal), color=colors[i], source=data)

        hover = HoverTool(tooltips=[(portal, "@{"+portal+"}"), ("Date", "@{dates}")], renderers=[line])
        p.add_tools(hover)

    p.y_range.start = 0
    p.x_range.range_padding = 0.1
    p.xgrid.grid_line_color = None
    p.axis.minor_tick_line_color = None
    p.outline_line_color = None
    p.legend.location = "top_left"
    return p


def openness_evolution(db, portals, snapshots):
    metrics = {}
    op_metrics = qa[2]['metrics']
    for sn in snapshots:
        metrics[sn] = collections.defaultdict(int)
        for p in portals:
            p_q = db.get_portal_quality(p, sn)
            for q in op_metrics:
                metrics[sn][q.lower()] += float(p_q.get(q.lower(), {'measurement': 0.0})['measurement'])

    dates = [getDateString(sn) for sn in snapshots]

    sorted_metrics = collections.defaultdict(list)
    metrics_labels = []
    for m in op_metrics:
        label = op_metrics[m]['label']
        metrics_labels.append(label)
        for sn in snapshots:
            sorted_metrics[label].append(metrics[sn][m.lower()] / len(portals))

    colors = [brewer['BrBG'][5][0], brewer['BrBG'][5][3], brewer['BrBG'][5][4]]
    #colors = [op_metrics[m]['color'] for m in op_metrics]

    data = {'dates': dates}
    for l in metrics_labels:
        data[l] = sorted_metrics[l]

    p = figure(x_range=dates, plot_height=PLOT_HEIGHT, plot_width=PLOT_WIDTH,
               toolbar_location=None)

    for i, l in enumerate(sorted_metrics):
        line = p.line(x='dates', y=l, line_width=LINE_WIDTH, legend=dict(value=l), color=colors[i], source=data)

        hover = HoverTool(tooltips=[(l, "@{"+l+"}"), ("Date", "@{dates}")], renderers=[line])
        p.add_tools(hover)

    p.y_range.start = 0
    p.y_range.end = 1
    p.x_range.range_padding = 0.1
    p.xgrid.grid_line_color = None
    p.axis.minor_tick_line_color = None
    p.outline_line_color = None
    p.legend.location = "top_left"
    return p
