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


months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
def formatDate(date):
	year = date[0:4]
	month = months[int(date[date.index('-')+1:date.rfind('-')])-1]
	day = date[date.rfind('-')+1:]
	return ('{} {}, {}'.format(month, day, year))

baseUrl = 'https://app.ticketmaster.com/discovery/v2/events'
city = 'Chicago'
payload = {
	'city': city,
	'classificationName': 'music',
	'sort': 'date,asc',
	'apikey' : keys.key
}

csvData = pd.read_csv('artists.csv', names=['artist'], header=0)
spotifyArtists = csvData['artist']
ticketmasterArtists = {}
r = requests.get(baseUrl, params=payload)
data = r.json()
pageNumbers = data['page']['totalPages']
for event in data['_embedded']['events']:
	try:
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
					priceRange = '{}-${}'.format(lowerPrice, upperPrice)
					tickmasterArtists[event['name']] = {'date': date, 'venue': venue, 'priceRange': priceRange}
	except:
		continue
for x in range(1, pageNumbers):
	payload['page'] = x
	r = requests.get(baseUrl, params=payload)
	data = r.json()
	try:
		print('Working: page #{}'.format(x))
		for event in data['_embedded']['events']:
			try:
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
							priceRange = '{}-${}'.format(lowerPrice, upperPrice)
							ticketLink = attraction['url']
							ticketmasterArtists[attraction['name']] = {'date': date, 'venue': venue, 'priceRange': priceRange, 'url': ticketLink}
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
	savedArtists = pd.read_csv('savedArtists.csv', index_col=0)
except FileNotFoundError:
	savedArtists = pd.DataFrame(columns=['artist'])
savedSet = savedArtists['artist']
newArtists = []
for key in ticketmasterArtists.keys():
	if key not in savedSet.values:
		print('New artist: {}'.format(key))
		newArtists.append(key)
		savedArtists = savedArtists.append(pd.DataFrame([key], columns=['artist']), ignore_index=True)
savedArtists.to_csv('savedArtists.csv')


# because who doesn't love writing poorly styled html in python strings
artistList = """<html>
<head>
</head>
<body>
	<div><ul style="padding-inline-start: 0px;">"""
for artist in newArtists:
	artistList += """
				<li style="list-style: none;padding-bottom: 24px;">
					<div style="background-color: #9BC5DE;">
						<hr style="border: 1px solid #9BC5DE;" />
						<h1 style="color: white; text-align: center;font-size: 40px;font-weight: normal; line-height: 32px">{}</h1>
						<hr style="border: 1px solid #9BC5DE;" />
					</div>
					<div style="margin: 16px 0px 12px 24px">
						<div style="padding: 8px 0; ">
							<span style="font-size: 24px; font-weight: bold;">Performing at:</span>
							<span style="font-size: 24px;">{}</span>
						</div>
						<div style="padding: 8px 0;">
							<span style="font-size: 24px; font-weight: bold;">Date:</span>
							<span style="font-size: 24px;">{}</span>
						</div>
						<div style="padding: 8px 0;">
							<span style="font-size: 24px;font-weight:bold;">Ticket price range:</span>
							<span style="font-size: 24px;">${}</span>
						</div>
					</div>
					<div style="text-align: center;">
						<a href="{}">
							<button style="color: white; background-color: #9BC5DE; padding: 12px 20px; border-radius: 4px; border: none; cursor: pointer; text-align: center; font-weight: 300; box-sizing: border-box; font-size: 24px;">View Tickets</button>
						</a>
					</div>
				</li>""".format(artist, ticketmasterArtists[artist]['venue'], ticketmasterArtists[artist]['date'], ticketmasterArtists[artist]['priceRange'], ticketmasterArtists[artist]['url'])
artistList += """<ul\>"""
mes = """\
<html>
  <head></head>
  <body>
	{}
  </body>
</html>""".format(artistList)
if newArtists:
	print(mes)
	to = ", "
	to_l = emailkeys.to_list
	emaillist = to_l
	msg = MIMEMultipart()
	msg['To'] = ",".join(to_l)
	msg['Subject'] = "Concerts Update"
	msg['From'] = emailkeys.from_name
	msg.preamble = 'Multipart message.\n'
	part = MIMEText(mes, 'html')
	msg.attach(part)
	server = smtplib.SMTP("smtp.gmail.com:587")
	server.ehlo()
	server.starttls()
	server.login(emailkeys.email, emailkeys.password)
	server.sendmail(msg['From'], emaillist , msg.as_string())
	print("Email sent")
