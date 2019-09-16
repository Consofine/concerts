#!/home/mike/anaconda3/bin/python
import sys
import requests
import json
import pandas as pd
import csv
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from smtplib import SMTP
import smtplib
import keys
import emailkeys
import ipdb

#absolute filepath to this directory, with slash appended
basePath=keys.basePath
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
def formatDate(date):
	year = date[0:4]
	month = months[int(date[date.index('-')+1:date.rfind('-')])-1]
	day = date[date.rfind('-')+1:]
	return ('{} {}, {}'.format(month, day, year))

def cat(filename, name, venue, date, priceRange, url):
	with open(basePath+filename, 'r') as f:
		string = f.read()
		string = string.replace('$prices', priceRange)
		string = string.replace('$title', name)
		string = string.replace('$venue', venue)
		string = string.replace('$date', date)
		string = string.replace('$link', url)
	f.close()
	return string

def getInfo(event):
	for attraction in event['_embedded']['attractions']:
		if (attraction['name'] in spotifyArtists.values):
			if (attraction['name'] not in ticketmasterArtists):
				date = event['dates']['start']['localDate']
				time = event['dates']['start']['localTime']
				time = time[:time.rfind(':')]
				date = '{} at {}'.format(formatDate(date), time)
				venue = event['_embedded']['venues'][0]['name']
				lowerPrice = str(event['priceRanges'][0]['min'])
				upperPrice = str(event['priceRanges'][0]['max'])
				if (len(lowerPrice[lowerPrice.index('.'):]) < 3):
					lowerPrice += '0'
				if (len(upperPrice[upperPrice.index('.'):]) < 3):
					upperPrice += '0'
				priceRange = '${}-${}'.format(lowerPrice, upperPrice)
				ticketLink = attraction['url']
				ticketmasterArtists[attraction['name']] = {'date': date, 'venue': venue, 'priceRange': priceRange, 'url': ticketLink}

baseUrl = 'https://app.ticketmaster.com/discovery/v2/events'
city = 'Chicago'
payload = {
	'city': city,
	'classificationName': 'music',
	'sort': 'date,asc',
	'apikey' : keys.key
}

csvData = pd.read_csv('{}artists.csv'.format(basePath), names=['artist'], header=0)
spotifyArtists = csvData['artist']
ticketmasterArtists = {}
r = requests.get(baseUrl, params=payload)
data = r.json()
pageNumbers = data['page']['totalPages']
for event in data['_embedded']['events']:
	try:
		getInfo(data)
	except:
		continue
for x in range(1, pageNumbers):
	payload['page'] = x
	r = requests.get(baseUrl, params=payload)
	data = r.json()
	try:
		# print('Working: page #{}'.format(x))
		for event in data['_embedded']['events']:
			try:
				getInfo(event)
			except:
				continue
	except Exception as e:
		try:
			if (data['errors'][0]['status'] == '400'):
				print('Api limit reached')
				break
		except:
			pass
		print('Error: {}'.format(str(e)))
		continue
try:
	savedArtists = pd.read_csv(basePath+'savedArtists.csv', index_col=0)
except FileNotFoundError:
	savedArtists = pd.DataFrame(columns=['artist'])
savedSet = savedArtists['artist']
newArtists = []
for key in ticketmasterArtists.keys():
	if key not in savedSet.values:
		# print('New artist: {}'.format(key))
		newArtists.append(key)
		savedArtists = savedArtists.append(pd.DataFrame([key], columns=['artist']), ignore_index=True)
savedArtists = savedArtists.reset_index(drop=True)
for artist in savedSet.values:
	if artist not in ticketmasterArtists.keys():
		print(savedArtists)
		savedArtists = pd.DataFrame(savedArtists[savedArtists.artist != artist])
		# print("Removed: {}".format(artist))
print(savedArtists)
savedArtists.to_csv('{}savedArtists.csv'.format(basePath))
savedSet = savedArtists['artist']
emailMes = ""
if newArtists:
	with open('{}inline-title.html'.format(basePath), 'r') as f:
		title = f.read()
		emailMes += title.replace('$title', 'New Artists')
	f.close()
	for artist in newArtists:
		artistData = ticketmasterArtists[artist]
		emailMes += cat('inline-section.html', artist, artistData['venue'], artistData['date'], artistData['priceRange'], artistData['url'])
with open('{}inline-title.html'.format(basePath), 'r') as f:
	title = f.read()
	emailMes += title.replace('$title', 'Old Artists')
f.close()
for artist in savedSet.values:
	artistData = ticketmasterArtists[artist]
	emailMes += cat('inline-section.html', artist, artistData['venue'], artistData['date'], artistData['priceRange'], artistData['url'])
with open('{}inline.html'.format(basePath), 'r') as f:
	mes = f.read()
	mes = mes.replace('$body', emailMes)
	f.close()
#list of recipients' addresses
if (newArtists):
	to_l = emailkeys.to_list
	emaillist = to_l
	msg = MIMEMultipart()
	msg['To'] = ",".join(to_l)
	msg['Subject'] = "Concerts Update"
	#name to show email as being from
	msg['From'] = emailkeys.from_name
	msg.preamble = 'Multipart message.\n'
	part = MIMEText(mes, 'html')
	msg.attach(part)
	server = smtplib.SMTP("smtp.gmail.com:587")
	server.ehlo()
	server.starttls()
	#login with email address and password
	server.login(emailkeys.email, emailkeys.password)
	server.sendmail(msg['From'], emaillist , msg.as_string())
	print("Email sent")
