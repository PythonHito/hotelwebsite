from flask import Flask, render_template
from flask import request, redirect, session

from datetime import datetime
import csv
app = Flask(__name__)

#TODO: Make Review use datetime object instead of string, maybe
class Review():
	def __init__(self, name, date, content):
		self.name = name
		self.date = date
		self.content = content


#Define pages --------------------------------------
@app.route('/')
def home(): 
    return render_template('home.html')
    
@app.route('/attractions')
def attractions(): 
    return render_template('attractions.html')
    
@app.route('/bookings')
def bookings(): 
    return render_template('bookings.html')
	
@app.route('/addBooking', methods=['post'])
def addBooking():
	name = request.form['name']
	email = request.form['email']
	arrivalDateDateTime = datetime.strptime(request.form['arrivalDate'], "%Y-%m-%d")
	arrivalDate = datetime.strftime(arrivalDateDateTime, "%A %d/%m/%Y")
	
	departureDateDateTime = datetime.strptime(request.form['departureDate'], "%Y-%m-%d")
	departureDate = datetime.strftime(departureDateDateTime, "%A %d/%m/%Y")
	
	writeCsv('unconfirmedBookings.csv', [name,email,arrivalDate,departureDate], 'a')
	return redirect('/bookings')

#TODO: Possibly sanitize from code injection attacks
@app.route('/reviews', methods=['get'])
def reviews():
	rows = readCsv('reviews.csv')
	reviews = [Review(n[0], n[1], n[2]) for n in rows]
	#reviews.csv is in oldest first order
	return render_template('reviews.html', reviews=reversed(reviews))	

@app.route('/addReview', methods=['post'])
def addReview():
	name = request.form['name']
	date = datetime.strftime(datetime.now(), "%A %d/%m/%Y %H:%M:%S")
	content = request.form['content']
	writeCsv('reviews.csv', [name, date, content], 'a')
	return redirect('/reviews')
	
#--------------------------------------------------- 

#Define page methods -------------------------------

#---------------------------------------------------

#Read and write to csv file ------------------------
def readCsv(fileName):
	with open(fileName, 'r') as inFile:
		reader = csv.reader(inFile)
		aList = [row for row in reader]
		
	return aList
	
def writeCsv(fileName, listName, mode):
	with open(fileName, mode, newline='') as outFile:
		writer = csv.writer(outFile)
		writer.writerow(listName)
	return
#---------------------------------------------------

if __name__ == '__main__':
    app.run(debug = True)
