# Create your views here.
from django.http import HttpResponse
from django.template import Context, loader
from ukcs import Data, Parser
from models import *
import datetime
import time

import cairocffi as cairo

from matplotlib import pyplot

from StringIO import StringIO

def _to_seconds_from_epoch(dt):
	"""
	Returns a offset in seconds from epoch
	"""
	#return (dt-datetime.datetime(1970,1,1)).total_seconds()
	return time.mktime(dt.timetuple())


def _date_parser(period):
	"""
	Returns a datetime stamp for a duration, in the past
	"""
	try:
		period = int(period)
	except:
		raise ValueError("period must be an int")
	return datetime.datetime.today() - datetime.timedelta(days=int(period))

def _to_days_delta(date):
	"""
	Returns a string offset from a date
	"""
	assert isinstance(date, datetime.date), "date needs to be a datetime.date"
	difference = datetime.date.today() - date
	return (int(difference.days) * -1)
	

def server_status(request):
        """
        Server Status page
        """
	a = Data.Retrieve()
	b = Parser.ServerStatus(a)
        return HttpResponse(b.json_print, content_type="application/json")

def server_page(request):
	"""
	Server Detail page
	"""
	if "period" in request.GET and request.GET["period"]:
		period=int(request.GET["period"])
	else:
		period=5
	times = [("1D",1), ("2D", 2), ("3D", 3), ("5D", 5), ("1W", 7), ("3W", 21), ("5W", 35)]
 	s = server.objects.all().order_by('server_name')	
	t = loader.get_template('matplotlib.html')
	c = Context({
			'servers': s,
			'times': times,
			'period': period,
		   })
	return HttpResponse(t.render(c))

def graph_api(request, ip_address, port_number, period):
	"""
	API for graph request
	"""
	# Find server object
	s = server.objects.get(ip_address=ip_address, port_number=port_number)
	results = s.status_set.filter(added__gte=_date_parser(period))

	dataset = (
		(s.server_name, tuple([(_to_days_delta(x.added.date()), int(x.current_players)) for x in results])),
	)

	data = [int(x.current_players) for x in results]

	import pygal

	chart = pygal.StackedLine(fill=True)
	chart.add('Active Users', data)
	chart.title = "Players logged into: %s" % s.server_name

	from StringIO import StringIO

	graph = StringIO()
	
	response = HttpResponse(mimetype='image/svg+xml')
	response.write(chart.render())
	#response.write(chart.render_to_png())
	return response

def rickshaw_api(request, ip_address, port_number, period):
	"""
	Javascript object formation
	"""
	s = server.objects.get(ip_address=ip_address, port_number=port_number)
	results = s.status_set.filter(added__gte=_date_parser(period))

	data = [{ 'x': _to_seconds_from_epoch(x.added), 'y': int(x.current_players)} for x in results]

	t = loader.get_template('rickshaw.html')
	c = Context({
			'server': s,
			'data': data,
		   })
	return HttpResponse(t.render(c))

class ServerObject(object):
	def __init__(self):
		self.obj = None;
		self.data = None;
		self.name = None;

def new_homepage(request):
	"""
	Home page
	"""
	period=7
	s = server.objects.all().order_by('-server_name')
	graph_data = []
	for entry in s:
		results = entry.status_set.filter(added__gte=_date_parser(period))
		data = [{ 'x': _to_seconds_from_epoch(x.added), 'y': int(x.current_players)} for x in results]
		a = ServerObject()
		a.name = entry.server_name
		a.data = data
		a.obj = entry
		graph_data.append(a)
	t = loader.get_template('new_home.html')
	c = Context({
			'servers': graph_data,
		})
	return HttpResponse(t.render(c))

def matplotlib_graph(request, ip_address, port_number, period):
	"""
	Matplotlib image api
	"""
	from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
	from matplotlib.figure import Figure
	from matplotlib.dates import DateFormatter
	
	p = int(period)

	if p <= 2:
		df = DateFormatter('%H:%M')
	else:
		df = DateFormatter('%b %d')

	s = server.objects.get(ip_address=ip_address, port_number=port_number)
	results = s.status_set.filter(added__gte=_date_parser(period))

	fig=Figure(figsize=(8,2.5), facecolor='white')
	ax = fig.add_subplot(111)
	x = []
	y = []
	max = []
	for entry in results:
		x.append(entry.added)
		y.append(entry.current_players)
		max.append(entry.max_players)
	ax.plot_date(x, y, '-')
	ax.plot_date(x, max, '-', color='red')
	ax.set_xlabel = 'Date'
	ax.set_ylabel = 'Players'
	ax.set_title = s.server_name
	ax.xaxis.set_major_formatter(df)
	fig.autofmt_xdate()
	canvas=FigureCanvas(fig)
	response=HttpResponse(content_type='image/png')
	canvas.print_png(response)
	return response
