from django.db import models

# Create your models here.

class server(models.Model):
	server_name = models.CharField(max_length=50, primary_key=True)
	ip_address = models.CharField(max_length=100)
	port_number = models.IntegerField()
	description = models.CharField(max_length=200)

class status(models.Model):
	server_name = models.ForeignKey(server)	
	current_players = models.IntegerField()
	max_players = models.IntegerField()
	map_name = models.CharField(max_length=100)
	added = models.DateTimeField(auto_now_add=True)
