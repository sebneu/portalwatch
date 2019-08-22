from collections import defaultdict

import numpy as np
from bokeh.layouts import column, row
from bokeh.models import NumeralTickFormatter, FuncTickFormatter, Text, Range1d, HoverTool, \
    ColumnDataSource, Spacer, Circle, Legend, GlyphRenderer
from bokeh.plotting import figure
from bokeh.palettes import brewer
from numpy.ma import arange

from ui.metrics import qa
from utils.snapshots import getLastNSnapshots, getWeekString, getWeekString1



def portalsScatter(df):
    df=df.fillna(0)

    def get_dataset(df, name):
        df1 = df[df['software'] == name].copy()
        #print name,df1.describe()
        del df1['software']
        return df1

    software_df = {}
    for s in df.software.unique():
        software_df[s] = get_dataset(df,s)

    #socrata = get_dataset(df,"Socrata")
    #opendatasoft = get_dataset(df,"OpenDataSoft")

    hmax = 0
    vmax = 0

    p = figure(   plot_width=600, plot_height=600
                , min_border=10, min_border_left=50
                , toolbar_location="above"
                ,y_axis_type="log",x_axis_type="log")
    p.toolbar.logo = None
    p.toolbar_location = None


    #p.xaxis[0].axis_label = '#Datasets'
    #p.yaxis[0].axis_label = '#Resources'
    p.background_fill_color = "#fafafa"


    ph = figure(toolbar_location=None, plot_width=p.plot_width, plot_height=200, x_range=p.x_range,
                 min_border=10, min_border_left=50, y_axis_location="right",x_axis_type="log")

    pv = figure(toolbar_location=None, plot_width=200, plot_height=p.plot_height,
                y_range=p.y_range, min_border=10, y_axis_location="right",y_axis_type="log")
    colors = brewer['BrBG'][len(software_df)]
    for i, l in enumerate(software_df):
        s = software_df[l]
        c = colors[i]
        source=ColumnDataSource(data=s)
        p.scatter(x='datasets', y='resources', size=len(software_df), source=source, color=c, legend=l)

    #for i, item in enumerate([
    #                    #(all, 'All','black')
    #                    (ckan,'CKAN', '#3A5785')
    #                    ,(socrata,'Socrata', 'green')
    #                    ,(opendatasoft,'OpenDataSoft', 'red')
    #                    ]):

    #    s,l,c=item
    #    source=ColumnDataSource(data=s)
    #    p.scatter(x='datasets', y='resources', size=3, source=source, color=c, legend=l)


        # create the horizontal histogram
        maxV= s['datasets'].max()
        bins= 10 ** np.linspace(np.log10(1), np.log10(maxV), 10)
        hhist, hedges = np.histogram(s['datasets'], bins=bins)#[0,5,10,50,100,500,1000,5000,10000,50000,100000]
        hzeros = np.zeros(len(hedges)-1)
        hmax = max(hhist)*1.5 if max(hhist)*1.5>hmax else hmax

        LINE_ARGS = dict(color=c, line_color=None)


        ph.xgrid.grid_line_color = None
        #ph.yaxis.major_label_orientation = np.pi/4
        ph.background_fill_color = "#fafafa"

        ph.quad(bottom=0, left=hedges[:-1], right=hedges[1:], top=hhist, color=c, line_color=c, alpha=0.5)
        hh1 = ph.quad(bottom=0, left=hedges[:-1], right=hedges[1:], top=hzeros, alpha=0.5, **LINE_ARGS)
        hh2 = ph.quad(bottom=0, left=hedges[:-1], right=hedges[1:], top=hzeros, alpha=0.1, **LINE_ARGS)

        # create the vertical histogram
        maxV= s['resources'].max()
        bins= 10 ** np.linspace(np.log10(1), np.log10(maxV), 10)
        vhist, vedges = np.histogram(s['resources'], bins=bins)#[0,5,10,50,100,500,1000,5000,10000,50000,100000]
        vzeros = np.zeros(len(vedges)-1)
        vmax = max(vhist)*1.5 if max(vhist)*1.5>vmax else vmax


        pv.ygrid.grid_line_color = None
        #pv.xaxis.major_label_orientation = np.pi/4
        pv.background_fill_color = "#fafafa"

        pv.quad(left=0, bottom=vedges[:-1], top=vedges[1:], right=vhist, color=c, line_color=c, alpha=0.5)
        vh1 = pv.quad(left=0, bottom=vedges[:-1], top=vedges[1:], right=vzeros, alpha=0.5, **LINE_ARGS)
        vh2 = pv.quad(left=0, bottom=vedges[:-1], top=vedges[1:], right=vzeros, alpha=0.1, **LINE_ARGS)

    ph.y_range=Range1d(0.1, hmax)
    pv.x_range=Range1d(0.1, vmax)

    #plots={'scatter':p,'data':ph,'res':pv}
    p.legend.location = "bottom_right"

    layout = column(row(p, pv), row(ph, Spacer(width=200, height=200)))

    return layout

def qualityChart(df):

    dim_color = {}
    key_color = {}
    for index, r  in df.iterrows():
        dim_color[r['Dimension']] =r['dim_color']
        key_color[r['Metric']]= r['color']


    width = 400
    height = 400
    inner_radius = 90
    outer_radius = 300 - 10

    minr = 0 #sqrt(log(0 * 1E4))
    maxr = 1#sqrt(log(1 * 1E4))
    a = (outer_radius - inner_radius) / (maxr - minr)
    b = inner_radius

    def rad(mic):
        v = a * mic + b
        return v

    big_angle = 2.0 * np.pi / (len(df) + 1)
    small_angle = big_angle / 7

    x = np.zeros(len(df))
    y = np.zeros(len(df))


    tools = "reset"
    # create chart
    p = figure( plot_width=width, plot_height=height, title="",
        x_axis_type=None, y_axis_type=None,
        x_range=[-420, 420], y_range=[-420, 420],
        min_border=0
        ,sizing_mode='scale_width',tools=''
        #,tools=tools
        #outline_line_color="black",
        #background_fill="#f0e1d2",
        #border_fill="#f0e1d2"
        )
    p.toolbar.logo = None
    p.toolbar_location = None

    p.line(x+1, y+1, alpha=0.5)

    # DIMENSION CIRCLE
    angles = np.pi/2 - big_angle/2 - df.index.to_series()*big_angle
    colors = [dim_color[dim] for dim in df.Dimension]
    p.annular_wedge(
        x, y, outer_radius+15, outer_radius+30, -big_angle+angles, angles, color=colors,
    )

    #source = ColumnDataSource(df)
    kcolors = [key_color[k] for k in df.Metric]
    source = ColumnDataSource(data=dict(
        x=x,
        value=df['value'],
        kcolors=kcolors,
        outer_radius=rad(df.value),
        end_angle=-big_angle+angles+6*small_angle,
        start_angle=-big_angle+angles+3*small_angle,
        label=df['label'],
        Dimension=df['Dimension'],
        perc=df['perc']
    ))

    g_r1= p.annular_wedge('x', 'value', inner_radius, 'outer_radius',
        'start_angle', 'end_angle',
        color='kcolors', source=source)

    p.annular_wedge(x, y, inner_radius, rad(df.perc),
        -big_angle+ angles+2.5*small_angle, -big_angle+angles+6.5*small_angle, alpha=0.4,
        color='grey')

    g1_hover = HoverTool(renderers=[g_r1],
                         tooltips=[('quality value', '@value'), ('Metric', '@label'),('Dimension', '@Dimension'),('Percentage of datasets', '@perc')])
    p.add_tools(g1_hover)
    #Mrtrics labels
    labels = np.array([c / 100.0 for c in range(0, 110, 10)]) #
    radii = a * labels + b

    p.circle(x, y, radius=radii, fill_color=None, line_color="#d3d3d3")
    p.annular_wedge([0], [0], inner_radius-10, outer_radius+10,
        0.48*np.pi, 0.52 * np.pi, color="white")

    p.text(x, radii, [str(r) for r in labels],
        text_font_size="8pt", text_align="center", text_baseline="middle")

    # radial axes
    p.annular_wedge(x, y, inner_radius, outer_radius+10,
        -big_angle+angles, -big_angle+angles, color="black")


    # Dimension labels
    xr = radii[5]*np.cos(np.array(-big_angle/1.25 + angles))
    yr = radii[5]*np.sin(np.array(-big_angle/1.25 + angles))

    label_angle=np.array(-big_angle/1.4+angles)
    label_angle[label_angle < -np.pi/2] += np.pi # easier to read labels on the left side
    p.text(xr, yr, df.label, angle=label_angle,
        text_font_size="9pt", text_align="center", text_baseline="middle")


    #dim legend
    p.rect([-40,-40, -40, -40,-40], [36,18, 0, -18, -36], width=30, height=13,
        color=list(dim_color.values()))
    p.text([-15,-15, -15, -15,-15], [36,18, 0, -18,-36], text=list(dim_color.keys()),
        text_font_size="9pt", text_align="left", text_baseline="middle")

    #p.logo = None
    #p.toolbar_location = None
    p.background_fill_color = "#fafafa"
    return p


def evolSize(source,df):
    p = figure(   plot_width=600, plot_height=200
                , min_border=10, min_border_left=50
                , toolbar_location="above")
    p.background_fill_color = "#fafafa"
    p.legend.location = "top_left"
    p.toolbar.logo = None
    p.toolbar_location = None

    legends=[]

    l=p.line(x='snapshotId',y='datasets', line_width=2,source=source, color=brewer['BrBG'][3][0])
    c=p.circle(x='snapshotId',y='datasets', line_width=4,source=source, color=brewer['BrBG'][3][0])

    hit_target =Circle(x='snapshotId',y='datasets', size=10,line_color=None, fill_color=None)
    hit_renderer = p.add_glyph(source, hit_target)

    legends.append(("Datasets",[l,c]))
    p.add_tools(HoverTool(renderers=[hit_renderer], tooltips={'Metric':"Size", "Week": "@week", 'Value':"@datasets"}))

    #######
    l=p.line(x='snapshotId',y='resources', line_width=2,source=source, color=brewer['BrBG'][3][2])
    c=p.cross(x='snapshotId',y='resources', line_width=4,source=source, color=brewer['BrBG'][3][2])

    hit_target =Circle(x='snapshotId',y='resources', size=10,line_color=None, fill_color=None)
    hit_renderer = p.add_glyph(source, hit_target)

    legends.append(("Resources",[l,c]))
    p.add_tools(HoverTool(renderers=[hit_renderer], tooltips={'Metric':"Size", "Week": "@week", 'Value':"@resources"}))


    p.xaxis[0].ticker.desired_num_ticks = df.shape[0]

    p.xaxis.formatter=FuncTickFormatter.from_py_func(getWeekStringTick)
    p.axis.minor_tick_line_color = None

    legend = Legend( location=(0, -30))
    legend.items = legends
    p.add_layout(legend, 'right')

    p.xaxis[0].axis_label = 'Snapshot'
    p.yaxis[0].axis_label = 'Count'

    return p

def evolutionCharts(df):

    df['week'] = df['snapshot'].apply(getWeekString)
    df = df[df['end'].notnull()]
    df=df.sort_values(['snapshot'], ascending=[1])
    df['snapshotId']= range(1, len(df) + 1)
    print(df)
    source = ColumnDataSource(df)

    plots={'size':evolSize(source,df)}

    for q in qa:
        pt = figure(plot_width=600, plot_height=200
                , min_border=10, min_border_left=50
                , toolbar_location="above")
        pt.background_fill_color = "#fafafa"
        pt.legend.location = "top_left"
        pt.toolbar.logo = None
        pt.toolbar_location = None
        legends=[]
        marker = [pt.circle, pt.x, pt.cross, pt.square, pt.diamond, pt.triangle, pt.inverted_triangle, pt.asterisk, pt.square_cross]
        colors = brewer['BrBG'][max(3, min(len(q['metrics']), 11))]
        i = 0
        for m,v in q['metrics'].items():
            if m.lower() in df:
                l=pt.line(x='snapshotId',y=m.lower(), line_width=2,source=source, color=colors[i%len(colors)])
                c=marker[i%len(marker)](x='snapshotId',y=m.lower(), line_width=4,source=source, color=colors[i%len(colors)])
                # invisible circle used for hovering
                hit_target =Circle(x='snapshotId',y=m.lower(), size=10,line_color=None, fill_color=None)
                hit_renderer = pt.add_glyph(source, hit_target)

                legends.append((v['label']+" ["+m.lower()+"]",[l,c]))

                pt.add_tools(HoverTool(renderers=[hit_renderer], tooltips={'Metric':v['label'], "Week": "@week", 'Value':"@"+m.lower()}))
                pt.xaxis[0].ticker.desired_num_ticks = df.shape[0]
                i += 1

        pt.xaxis.formatter=FuncTickFormatter.from_py_func(getWeekStringTick)
        pt.axis.minor_tick_line_color = None

        legend = Legend(location=(0, -30))
        legend.items=legends
        pt.add_layout(legend, 'right')

        pt.xaxis[0].axis_label = 'Snapshot'
        pt.yaxis[0].axis_label = 'Average quality'

        plots[q['dimension']]=pt

    return plots

def getWeekStringTick():
    global tick
    if tick is None or len(str(tick))==0:
        return ''
    year="'"+str(tick)[:2]
    week=int(str(tick)[2:])
    return 'W'+str(week)+'-'+str(year)


def systemEvolutionBarPlot(df, yLabel, values):
    p = Bar(df, label='snapshot', values=values, agg='sum', stack='software',
        legend='bottom_left', bar_width=0.5, xlabel="Snapshots", ylabel=yLabel, sizing_mode='scale_width', height=200,tools='hover')

    glyph_renderers = p.select(GlyphRenderer)
    bar_source = [glyph_renderers[i].data_source for i in range(len(glyph_renderers))]
    hover = p.select(HoverTool)
    hover.tooltips = [
        ('software',' @software'),
        ('value', '@height'),
    ]
    p.xaxis.formatter=FuncTickFormatter.from_py_func(getWeekStringTick)
    p.axis.minor_tick_line_color = None

    p.background_fill_color = "#fafafa"
    p.legend.location = "top_left"
    p.toolbar.logo = None
    p.toolbar_location = None

    legend=p.legend[0].legends
    p.legend[0].legends=[]
    l = Legend( location=(0, -30))
    l.items=legend
    p.add_layout(l, 'right')

    return p

def systemEvolutionPlot(df):
    df=df.sort(['snapshot','count'], ascending=[1,0])

    p= systemEvolutionBarPlot(df,yLabel="#Portals", values='count')
    pd= systemEvolutionBarPlot(df,yLabel="#Datasets", values='datasets')
    pr= systemEvolutionBarPlot(df,yLabel="#Resources", values='resources')

    return {'portals':p,'datasets':pd,'resources':pr}

def portalDynamicity(df):

    def getWeekString(yearweek):
        if yearweek is None or len(str(yearweek)) == 0:
            return ''
        year = "'" + str(yearweek)[:2]
        week = int(str(yearweek)[2:])
        # d = d - timedelta(d.weekday())
        # dd=(week)*7
        # dlt = timedelta(days = dd)
        # first= d + dlt

        # dlt = timedelta(days = (week)*7)
        # last= d + dlt + timedelta(days=6)

        return 'W' + str(week) + '-' + str(year)
    bp = figure(plot_width=600, plot_height=300, y_axis_type="datetime", sizing_mode='scale_width',
                tools='')  # ,toolbar_location=None
    bp.toolbar.logo = None
    bp.toolbar_location = None
    label_dict={}
    for i, s in enumerate(df['snapshot']):
        label_dict[i] = getWeekString1(s)

    bp.yaxis[0].formatter = NumeralTickFormatter(format="0.0%")
    bp.xaxis[0].axis_label = 'Snapshots'
    bp.yaxis[0].axis_label = '% of portals'

    li = bp.line(df.index.values.tolist(), df['dyratio'], line_width=2, line_color='red', legend="dyratio")
    c = bp.circle(df.index.values.tolist(), df['dyratio'], line_width=2, line_color='red', legend="dyratio")
    li1 = bp.line(df.index.values.tolist(), df['adddelratio'], line_width=2, line_color='blue', legend="adddelratio")
    c = bp.circle(df.index.values.tolist(), df['adddelratio'], line_width=2, line_color='blue', legend="adddelratio")
    legend = bp.legend[0].legends
    bp.legend[0].legends = []
    l = Legend(location=(0, -30))
    l.items = legend
    bp.add_layout(l, 'right')



    labels=["staticRatio","updatedRatio","addRatio","delRatio"]

    colors = brewer["Pastel2"][len(labels)]
    bar = Bar(df,
              values=blend("staticRatio","updatedRatio","addRatio","delRatio", name='medals', labels_name='medal'),
              label=cat(columns='snapshot', sort=False),
              stack=cat(columns='medal', sort=False),
              color=color(columns='medal', palette=colors,
                          sort=False),
              legend='top_right',
              bar_width=0.5, sizing_mode='scale_width',
              tooltips=[('ratio', '@medal'), ('snapshot', '@snapshot'),('Value of Total',' @height{0.00%}')])
    legend = bar.legend[0].legends
    bar.legend[0].legends = []
    l = Legend(location=(0, -30))
    l.items = legend
    bar.add_layout(l, 'right')
    bar.xaxis[0].axis_label = 'Snapshots'
    bar.yaxis[0].axis_label = '% of datasets'
    bar.width=600
    bar.height=300
    bar.xaxis[0].formatter = FuncTickFormatter.from_py_func(getWeekStringTick)
    bar.toolbar.logo = None
    bar.toolbar_location = None

    bar.yaxis[0].formatter = NumeralTickFormatter(format="0.0%")
    return {'bar':bar,'lines':bp}