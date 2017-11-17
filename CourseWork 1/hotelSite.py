from flask import Flask, render_template
from flask import request
import csv
app = Flask(__name__)

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
    
@app.route('/reviews')
def reviews(): 
    return render_template('reviews.html')
	
#--------------------------------------------------- 

#Define page methods -------------------------------

#---------------------------------------------------

#Read and write to csv file ------------------------
def readCsv(fileName):
	with open(fileName, 'r') as inFile:
		reader = csv.reader(inFile)
		aList = [row for row in reader]
		
	return aList
	
def writeCsv(fileName, listName):
	with open(fileName, 'w', newline='') as outFile:
		writer = csv.writer(outFile)
		writer.writerows(listName)
	return
#---------------------------------------------------

if __name__ == '__main__':
    app.run(debug = True)
