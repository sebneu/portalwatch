from bokeh.core.properties import value
from bokeh.io import show, output_file
from bokeh.plotting import figure
from bokeh.palettes import brewer

import collections

from ui.metrics import qa
from utils.snapshots import getDateString
PLOT_HEIGHT=600
PLOT_WIDTH=1000
LINE_WIDTH=4

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
        #tf = db.get_formats(snapshot=sn, limit=10)

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
    for i, p in enumerate(portals):
        format_counts[p] = []
        for sn in snapshots:
            format_counts[p].append(db.get_portal_format_count(p, format, sn))


    colors = brewer['BrBG'][len(portals)]
    dates = [getDateString(sn) for sn in snapshots]

    data = {'dates': dates}
    for p in portals:
        data[p] = format_counts[p]

    p = figure(x_range=dates, plot_height=PLOT_HEIGHT, plot_width=PLOT_WIDTH,
               toolbar_location=None, tools="hover", tooltips="$name @dates: @$name")

    p.vline_stack(portals, x='dates', line_width=LINE_WIDTH, color=colors, source=data,
                  legend=[value(x) for x in format_counts])
    # add a line renderer
    #for i, portal in enumerate(format_counts):
    #    p.line(snapshots, format_counts[portal], line_width=LINE_WIDTH, legend=portal, color=colors[i])

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
               toolbar_location=None, tools="hover", tooltips="$name @dates: @$name")

    p.vline_stack(metrics_labels, x='dates', line_width=LINE_WIDTH, color=colors, source=data,
                  legend=[value(x) for x in metrics_labels])

    p.y_range.start = 0
    p.x_range.range_padding = 0.1
    p.xgrid.grid_line_color = None
    p.axis.minor_tick_line_color = None
    p.outline_line_color = None
    p.legend.location = "top_left"
    p.legend.orientation = "horizontal"

    return p
