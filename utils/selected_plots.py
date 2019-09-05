from bokeh.core.properties import value
from bokeh.io import show, output_file
from bokeh.plotting import figure
from bokeh.palettes import brewer

import collections

from utils.snapshots import getDateString


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

    p = figure(x_range=dates, plot_height=600, plot_width=1000, title="Crawl Dates",
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

    p = figure(x_range=dates, plot_height=600, plot_width=1000, title="Crawl Dates",
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