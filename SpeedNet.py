#
# Program:      SpeedNetDevStage1.py
# Author:       Tanner Utz
#
# Stages:       In our environments there are three verion name types
#                   *SpeedNetDevStage1.py - This includes shorter loop iterations
#                   *SpeedNetDevStage2.py - This has normal iterations and runs alongside production
#                   *SpeedNet.py - This runs in the production environemnt after the above testing
#
# Description:  This program is designed to test many attributes of a network that it runs on. Initially
#                  it will test the network speeds however with 5 minute iterations we plan to have it 
#                  testing much more.
#
# Testing:      SEARCHCHANGE - Signals a line that needs changed for production
#               SEARCHREMOVE - Signals a line that needs removed for production
#               SEARCHENABLE - Signals a line that needs enabled for production
#

from distutils import core
import email
import os
from sqlite3 import Date
import speedtest
import time
from datetime import datetime
import csv
import matplotlib.pyplot as plt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from pythonping import ping

speed_test = speedtest.Speedtest()

def networkDefDown():

    googleAveragePing = 0
    yahooAveragePing = 0
    bingAveragePing = 0
    googleDown = False
    yahooDown = False
    bingDown = False

    try:
        googleAveragePing = ping('8.8.8.8', size=40, count=10).rtt_avg_ms
    except:
        googleDown = True

    try:
        yahooAveragePing = ping('98.137.27.103', size=40, count=10).rtt_avg_ms
    except:
        yahooDown = True

    try:
        bingAveragePing = ping('202.89.233.100', size=40, count=10).rtt_avg_ms
    except:
        bingDown = True

    return googleDown and yahooDown and bingDown

def sendEmail(pngFullPath, pngFileName, emailBody, emailRecipient):

    try:
        msg = MIMEMultipart()
        msg['From'] = '<Enter Your Email Send Username Here>'
        msg['To'] = emailRecipient
        msg['Subject'] = 'Report Update - ' + pngFileName
        body = emailBody
        msg.attach(MIMEText(body, 'plain'))

        attachment = open(pngFullPath, 'rb')
        part = MIMEBase('application', "octet-stream")
        part.set_payload((attachment).read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= %s" % pngFileName)
        msg.attach(part)

        server = smtplib.SMTP('smtp.office365.com', 587)  ### put your relevant SMTP here
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login('<Enter Your Email Send Username Here>', '<Enter Your Email Send Password Here>')  ### if applicable
        server.send_message(msg)
        server.quit()

    except:
        print("\n***The attempt to send a email to " + emailRecipient + " has failed!\n")
        pass

def getWeekday(dayInt):
    if dayInt == 0:
        return "Monday"
    elif dayInt == 1:
        return "Tuesday"
    elif dayInt == 2:
        return "Wednesday"
    elif dayInt == 3:
        return "Thursday"
    elif dayInt == 4:
        return "Friday"
    elif dayInt == 5:
        return "Saturday"
    elif dayInt == 6:
        return "Sunday"
    else:
        return "Unknown"

def buildReport(csvFileName, pngFileName, weekday):
    x = []
    yup = []
    ywn = []
    currentHour = 24
    avgDnPerHour = 0
    avgUpPerHour = 0
    hourlyRecCnt = 0

    with open(csvFileName,'r') as csvfile:
        rows = csv.reader(csvfile, delimiter=',')
        for row in rows:

            # If No records have been counted yet for this hour
            if hourlyRecCnt == 0:
                
                avgDnPerHour = float(row[2])
                avgUpPerHour = float(row[3])
                hourlyRecCnt = 1

                currentHour = row[1]

            # If the current hour is a repeated hour from the last iteration
            elif currentHour == row[1]:

                avgDnPerHour += float(row[2])
                avgUpPerHour += float(row[3])
                hourlyRecCnt += 1
        
            # If there is a new hour for this iteration, complete the average for the current hour
            else:
            
                avgDnPerHour /= hourlyRecCnt
                avgUpPerHour /= hourlyRecCnt

                x.append(currentHour)
                ywn.append(avgDnPerHour)
                yup.append(avgUpPerHour)

                avgDnPerHour = float(row[2])
                avgUpPerHour = float(row[3])
                hourlyRecCnt = 1

                currentHour = row[1]

    plt.plot(x, ywn, color = 'b', linestyle = 'solid',
            marker = 'o',label = "Download Speeds")

    plt.plot(x, yup, color = 'r', linestyle = 'solid',
            marker = 'o',label = "Upload Speeds")

    plt.xticks(rotation = 25)
    plt.xlabel('Hours of the Day')
    plt.ylabel('MB/sec')
    plt.title(weekday, fontsize = 20)
    plt.grid()
    plt.legend()
    plt.savefig(pngFileName)
    plt.cla()

def main():

    try:
                #-------------------------------------------------------
        print("\n *NOTICE:"
            + "\n               This program is designed to run forever."
            + "\n           It will never stop until it is interupted."
            + "\n           Recognize that the logging csv files will be"
            + "\n           saved at the end of every day just before"
            + "\n           the next days file is logged in the [Local"
            + "\n           System Logs] folder. This folder must exist"
            + "\n           masters Documents folder in order for this"
            + "\n           operation to work."
            + "\n"
            + "\n And off we go........................................."
            + "\n")

        while True:

            if not os.path.exists("/home/" + str(os.getlogin()) + "/Documents/SpeedNet Logs"):
                os.makedirs("/home/" + str(os.getlogin()) + "/Documents/SpeedNet Logs")
            corePath = "/home/" + str(os.getlogin()) + "/Documents/SpeedNet Logs"

            todaysDate = Date.today()
            csvFullPath = corePath + "/" + str(todaysDate) + ".csv"
            pngFullPath = corePath + "/" + str(todaysDate) + ".png"
            pngFileName = str(todaysDate) + '.png'

            csvfile = open(csvFullPath, 'w')
            csvwriter = csv.writer(csvfile)

            todaysMaxDn = 0
            todaysMaxUp = 0
            todaysMinDn = 100
            todaysMinUp = 100
            outageEvents = 0
            outageStart = datetime
            outageStop = datetime
            networkDown = False
            outageRecStart = []
            outageRecStop = []
            outageRecDownTime = []
    
            while Date.today() == todaysDate:

                try:
                    download_speed = int(round((speed_test.download() / 1000000), 0))
                except:
                    download_speed = "Ookla Error"
                    pass
        
                try:
                    upload_speed = int(round((speed_test.upload() / 1000000), 0))
                except:
                    upload_speed = "Ookla Error"
                    pass

                timeNow = datetime.now().strftime("%H:%M:%S")
                hourNow = datetime.now().strftime("%H")

                print(" Logging Network Speed...  " + str(timeNow) + "\n"
                    + "-------------------------------------------------------\n"
                    + "   Current Download Status:   " + str(download_speed) + " Mb/sec\n"
                    + "   Current Upload Status:     " + str(upload_speed) + " Mb/sec\n"
                    + "\n"
                    + " *Info has been writen to CSV -> " + str(todaysDate) + "\n"
                    + "-------------------------------------------------------\n")

                csvwriter.writerow([timeNow, hourNow, download_speed, upload_speed])

                if download_speed > todaysMaxDn:
                    todaysMaxDn = download_speed
                if upload_speed > todaysMaxUp:
                    todaysMaxUp = upload_speed
                if download_speed < todaysMinDn and download_speed != 0:
                    todaysMinDn = download_speed
                if upload_speed < todaysMinUp and upload_speed != 0:
                    todaysMinUp = upload_speed
                if download_speed == 0 and upload_speed == 0 and networkDefDown():
                    if not networkDown:
                        outageStart = datetime.now().strftime("%H:%M:%S")
                        networkDown = True
                else:
                    if networkDown:
                        networkDown = False
                        outageEvents += 1
                        outageStop = datetime.now().strftime("%H:%M:%S")
                        outageRecStart.append(outageStart)
                        outageRecStop.append(outageStop)
                        outageRecDownTime.append((outageStop - outageStart))

                time.sleep(270)

            csvfile.close()

            currentWeekdayID = getWeekday(todaysDate.weekday())
            buildReport(csvFullPath, pngFullPath, currentWeekdayID)

            emailBody = "Network Data for " + str(Date.today()) + "\n  Download Range:  " + str(todaysMinDn) + " mbps - " + str(todaysMaxDn) + " mbps, Delta " + str((todaysMaxDn - todaysMinDn)) + "\n  Upload Range:      " + str(todaysMinUp) + " mbps - " + str(todaysMaxUp) + " mbps, Delta " + str((todaysMaxUp - todaysMinUp)) + "\n  Outage Events:     " + str(outageEvents)

            index = 0
            for downTimeRec in outageRecDownTime:
                emailBody += "\n\t\t@" + str(outageRecStart[index]) + " -> " + str(outageRecStop[index]) + " DT: " + str(downTimeRec)
                index += 1

            sendEmail(pngFullPath, pngFileName, emailBody, '<Enter The Email Receiver Here>')

            print("\n The following have been completed:\n\n"
                + "\t *The File Labeled " + str(todaysDate) + ".csv has been saved.\n" 
                + "\t *The File Labeled " + str(todaysDate) + ".png has been saved.\n"
                + "\t *The above png has been emailed to John Utz and Tanner Utz.\n"
                + "\n " + str(todaysDate) + " has been recorded and logged.\n"
                + "\n Starting New Day.....\n\n")

    except:

        print("|||SYSTEM ENCOUNTERED AN ISSUE. RESTARTING NOW|||")
        pass
        main()

if __name__ == "__main__":
    main()
