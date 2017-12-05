from flask import Flask, render_template
from flask import request, redirect, session

from datetime import datetime, timedelta
import csv
from hashlib import blake2b
from itertools import count

#TODO: FULL CALENDAR SOURCE PLEASE GOD
#TODO: Booking date is inconsisent!
#TODO: Update Booking HTML
#TODO: CHECK DATA
#TODO: DO AVAILIABLE
#TODO: Function logic
#TODO: Indication of account status in template

app = Flask(__name__)
#TODO: Make secure!!!
app.secret_key="kjsfdgjhigfhgfdjk"

@app.route('/')
def home(): 
    return render_template('home.html')
    
@app.route('/attractions')
def attractions():
    return render_template('attractions.html')

#Booking page methods -------------------------------
@app.route('/bookings')
def bookings(): 
    with open("unconfirmedBookings.csv", "r") as file:
        reader = csv.reader(file)
        unconfirmedBookings = [{"name": row[0], "numberOfRooms": row[1],
                                "arrivalDate": row[2], "departureDate": row[3]} for row in reader]

    events = getAvailiableRooms()

    return render_template('bookings.html', unconfirmedBookings=unconfirmedBookings, events=events)

@app.route('/addBooking', methods=['post'])
def addBooking():
    number = int(request.form['numberOfRooms'])

    if number < 1:
        return redirect('/invalidRoomNumber')

    arrivalDateDateTime = datetime.strptime(request.form['arrivalDate'], "%Y-%m-%d")
    arrivalDate = datetime.strftime(arrivalDateDateTime, "%A %d/%m/%Y")

    departureDateDateTime = datetime.strptime(request.form['departureDate'], "%Y-%m-%d")
    departureDate = datetime.strftime(departureDateDateTime, "%A %d/%m/%Y")

    booking = [session['email'], number, arrivalDate, departureDate]

    if isDoubleBooked(booking):
        return redirect('/doubleBooked')

    with open('unconfirmedBookings.csv', 'a', newline="") as file:
        writer = csv.writer(file)
        writer.writerow([session['email'], number, arrivalDate, departureDate])

    return redirect('/bookingSent')

@app.route('/declineBooking', methods=['post'])
def declineBooking():
    index = int(request.form["index"])

    removeLineCsv("unconfirmedBookings.csv", index)

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
        return redirect('/exceededRooms')

    removeLineCsv("unconfirmedBookings.csv", index)

    with open("confirmedBookings.csv", "a", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(confirmedBooking)

    return redirect('/bookings')


# Review methods --------------------------------------
@app.route('/reviews', methods=['get'])
def reviews():
    with open('reviews.csv', 'r') as file:
        reader = csv.reader(file)
        reviews = [{"name":row[0], "date":row[1], "content":row[2]} for row in reader]
        #reviews.csv is in oldest first order
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
@app.route('/login')
def login():
    return render_template("login.html")

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

    return redirect("/credentialsFailed")

@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('admin', None)

    return redirect('/')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/attemptRegistration', methods=['post'])
def attemptRegistration():
    usernameInput = request.form['name']
    emailInput = request.form['email']
    hashedPasswordInput = hash(request.form['password'])
    confirmHashedPasswordInput = hash(request.form['confirmPassword'])

    if hashedPasswordInput == confirmHashedPasswordInput:
        #TODO: make cleaner
        with open('accounts.csv', 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == emailInput:
                    return redirect('/accountExists')

        #TODO: Comment everything
        with open('accounts.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([emailInput, hashedPasswordInput, usernameInput])
        session['email'] = emailInput

        with open("adminEmail.csv", "r") as file:
            adminEmail = file.readline().rstrip()

        if session['email'] == adminEmail:
            session['admin'] = True

        return redirect('/')
    else:
        return redirect('/passwordsDontMatch')

# Error pages -------------------------------------------
@app.route('/doubleBooked')
def doubleBooked():
    return render_template("doubleBooked.html")

@app.route('/invalidRoomNumber')
def invalidRoomNumber():
    return render_template("invalidRoomNumber.html")

@app.route('/bookingSent')
def bookingSent():
    return render_template("bookingSent.html")

@app.route('/exceededRooms')
def exceededRooms():
    return render_template("exceededRooms.html")

@app.route('/credentialsFailed')
def credentialsFailed():
    return render_template("credentialsFailed.html")

@app.route('/accountExists')
def accountExists():
    return render_template("accountExists.html")

@app.route('/passwordsDontMatch')
def passwordsDontMatch():
    return render_template("passwordsDontMatch.html")
# ---------------------------------------------------

# Helper methods -------------------------------

# ---------------------------------------------------

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