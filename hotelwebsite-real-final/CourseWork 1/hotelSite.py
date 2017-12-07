from flask import Flask, render_template
from flask import request, redirect, session

from datetime import datetime, timedelta
import csv
from hashlib import blake2b
from itertools import count

#TODO: FULL CALENDAR SOURCE PLEASE GOD
#TODO: View bookings without account
#TODO: REVIEW OVERFLOW
#TODO: LOgin Templsate login
#TODO: Format calender

app = Flask(__name__)
# TODO: Make secure!!!
app.secret_key = "kjsfdgjhigfhgfdjk"
#Get rid of unesserary whitespace made by jinja
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

@app.route('/')
def home(): 
    return render_template('home.html')
    
@app.route('/attractions')
def attractions():
    return render_template('attractions.html')

#Booking page methods -------------------------------
@app.route('/bookings')
def bookings(): 
    if not ("email" in session):
        session["errorMessage"] = "Please login before making or viewing bookings"
        return redirect("/login")
    else:
        #Get unconfirmed bookings to display to admin, if they are logged in
        with open("unconfirmedBookings.csv", "r") as file:
            reader = csv.reader(file)
            unconfirmedBookings = [{"name": row[0], "numberOfRooms": row[1],
                                    "arrivalDate": row[2], "departureDate": row[3]} for row in reader]

        message = getAndPopMessage()

        events = getAvailiableRooms()

        return render_template('bookings.html', unconfirmedBookings=unconfirmedBookings, events=events, message=message)

@app.route('/addBooking', methods=['post'])
def addBooking():
    numberOfRooms = int(request.form['numberOfRooms'])

    temp = datetime.strptime(request.form['arrivalDate'], "%Y-%m-%d")
    arrivalDate = datetime.strftime(temp, "%A %d/%m/%Y")

    temp = datetime.strptime(request.form['departureDate'], "%Y-%m-%d")
    departureDate = datetime.strftime(temp, "%A %d/%m/%Y")

    email = session['email']
    
    booking = [email, numberOfRooms, arrivalDate, departureDate]

    if isDoubleBooked(booking):
        session["errorMessage"] = "The dates you have booked conflict with an earlier booking you made, " \
                                  "we don't allow double booking. Sorry for the inconvinience"
        return redirect('/bookings')
    else:
        with open('unconfirmedBookings.csv', 'a', newline="") as file:
            writer = csv.writer(file)
            writer.writerow(booking)
            session["errorMessage"] = "Your booking has been sent to our managers. Thank you for doing business with us"
            return redirect('/bookings')

@app.route('/declineBooking', methods=['post'])
def declineBooking():
    index = int(request.form["index"])

    removeLineCsv("unconfirmedBookings.csv", index)

    session['errorMessage'] = "Booking has been declined"
    return redirect('/bookings')

@app.route('/confirmBooking', methods=['post'])
def confirmBooking():
    index = int(request.form["index"])
    with open("unconfirmedBookings.csv", "r") as file:
        reader = csv.reader(file)
        lines = [row for row in reader]
        confirmedBooking = lines[index]

    success = updateRoomNumbers(confirmedBooking[1:])

    if not success:
        session["errorMessage"] = "We don't have enough rooms to accomodate you throughout your stay." \
                                  " We apologise for the inconvinience"
        return redirect('/bookings')
    else:
        removeLineCsv("unconfirmedBookings.csv", index)

        with open("confirmedBookings.csv", "a", newline='') as file:
            writer = csv.writer(file)
            writer.writerow(confirmedBooking)

        session["errorMessage"] = "Booking has been confirmed"
        return redirect('/bookings')

# Review methods --------------------------------------
@app.route('/reviews', methods=['get'])
def reviews():
    with open('reviews.csv', 'r') as file:
        reader = csv.reader(file)
        reviews = [{"name":row[0], "date":row[1], "content":row[2]} for row in reader]
        return render_template('reviews.html', reviews=reviews)

@app.route('/addReview', methods=['post'])
def addReview():
    name = request.form['name']
    date = datetime.strftime(datetime.now(), "%A %d/%m/%Y %H:%M:%S")
    content = request.form['content']
    with open('reviews.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([name, date, content])
    return redirect('/reviews')

@app.route('/removeReview', methods=['post'])
def removeReview():
    index = int(request.form["index"])

    removeLineCsv("reviews.csv", index)

    return redirect('/reviews')


#Account methods -------------------------------

#TODO: Change HTML FOR DIS
@app.route('/login')
def login():
    message = getAndPopMessage()
    return render_template("login.html", message=message)

@app.route('/attemptLogin', methods=["post"])
def attemptLogin():
    emailInput = request.form['email']
    hashedPasswordInput = hash(request.form['password'])
    with open("accounts.csv", "r") as file:
        reader = csv.reader(file)
        for row in reader:
            candidate = {"email":row[0], "hashedPassword":row[1]}
            if candidate["email"] == emailInput and candidate["hashedPassword"] == hashedPasswordInput:
                    session["email"] = candidate["email"]

                    with open("adminEmail.csv", "r") as file:
                        adminEmail = file.readline().rstrip()

                    if session['email'] == adminEmail:
                        session['admin'] = True

                    return redirect("/")

    session["errorMessage"] = "The email/password combination you entered is incorrect"
    return redirect("/login")

@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('admin', None)

    return redirect('/')

@app.route('/register')
def register():
    message = getAndPopMessage()
        
    return render_template('register.html', message=message)

@app.route('/attemptRegistration', methods=['post'])
def attemptRegistration():
    usernameInput = request.form['name']
    emailInput = request.form['email']
    hashedPasswordInput = hash(request.form['password'])
    confirmHashedPasswordInput = hash(request.form['confirmPassword'])

    if hashedPasswordInput == confirmHashedPasswordInput:
        #TODO: make cleaner
        if accountExists(emailInput):
            session["errorMessage"] = "The email you entered already has an associated account"
            return redirect('/register')

        #Write account to file
        with open('accounts.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([emailInput, hashedPasswordInput, usernameInput])
        
        #Setup account session variables, logging user in
        session['email'] = emailInput

        with open("adminEmail.csv", "r") as file:
            adminEmail = file.readline().rstrip()

        if session['email'] == adminEmail:
            session['admin'] = True
        
        return redirect('/')
    else:
        session["errorMessage"] = "The passwords you entered don't match"
        return redirect('/register')

# ---------------------------------------------------

# Helper methods -------------------------------

# ---------------------------------------------------
def getAndPopMessage():
    if "errorMessage" in session:
        message = session["errorMessage"]
        session.pop("errorMessage", None)
    else:
        message = None
    return message

def accountExists(email):
    with open('accounts.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == email:
                return True
    return False

def getAvailiableRooms():
    with open("roomsBooked.csv", "r") as file:
        events = []
        reader = csv.reader(file)
        for row in reader:
            formatedDate = datetime.strptime(row[0], "%A %d/%m/%Y").strftime("%Y-%m-%d")
            numberOfRooms = row[1]
            events.append({'title': numberOfRooms, 'start':formatedDate})
        return events

def updateRoomNumbers(booking):
    bookingNumberOfRooms = int(booking[0])
    start = booking[1]
    end = booking[2]
    dates = datesRange(start, end)

    with open("roomsBooked.csv", "r") as file:
        roomNumbers = {}
        reader = csv.reader(file)
        for day in reader:
            date = datetime.strptime(day[0], "%A %d/%m/%Y")
            numberOfRooms = int(day[1])
            roomNumbers[date] = numberOfRooms

    for date in dates:
        if date in roomNumbers:
            roomNumbers[date] += bookingNumberOfRooms
        else:
            roomNumbers[date] = bookingNumberOfRooms

    with open("hotelInfo.csv", "r") as file:
        maxRooms = int(file.readline())

    overbooked = any(int(numberOfRooms) > maxRooms for numberOfRooms in roomNumbers.values())

    if overbooked:
        return 0
    else:
        roomNumbers = [n for n in sorted(roomNumbers.items(), key=lambda x: x[0]) if n[1] != 0]
        formatedRoomNumbers = [[datetime.strftime(day[0],"%A %d/%m/%Y") , day[1]] for day in roomNumbers]
        with open("roomsBooked.csv", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerows(formatedRoomNumbers)
        return 1

def datesRange(start, end):
    start = datetime.strptime(start, "%A %d/%m/%Y")
    end = datetime.strptime(end, "%A %d/%m/%Y")

    dates = []
    for days in count():
        dates.append(start + timedelta(days=days))

        if start + timedelta(days=days) == end:
            break

    return dates

def isDoubleBooked(booking):
    email = booking[0]
    start = booking[2]
    end = booking[3]
    bookingDates = datesRange(start, end)

    with open("confirmedBookings.csv", "r") as file:
        reader = csv.reader(file)
        for confirmedBooking in reader:
            if confirmedBooking[0] == email:
                confirmedStart = confirmedBooking[2]
                confirmedEnd = confirmedBooking[3]
                confirmedBookingDates = datesRange(confirmedStart, confirmedEnd)

                overlappingDates = [booking in confirmedBookingDates for booking in bookingDates]
                if any(overlappingDates) > 0:
                    return True
    return False

def removeLineCsv(fileName, index):
    with open(fileName, "r") as file:
        reader = csv.reader(file)
        lines = [row for row in reader]

    lines.pop(index)
    with open(fileName, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(lines)

def hash(dataString):
    return blake2b(dataString.encode()).hexdigest()

if __name__ == '__main__':
    app.run(debug = True)