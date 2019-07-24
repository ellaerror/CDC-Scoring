import requests
import time
import socket
import subprocess
import datetime
import smtplib
import warnings
import shutil

warnings.filterwarnings("ignore")

# Custom variables in the section below:
# Change these to change the flow of the competition

# this is the hour the scoring engine will start
# 9 
START   = 13
# this is how many minutes the grace period is 
# this value must be under an hour.
# 40
GRACE   = 0

# this is the time the first break starts. 
# The var with H is the hour, and the other is the minute.
# 1200
BREAK1H = 13
BREAK1M = 30

# this is the time the second break starts.
# Again, H=hour, M=minute
# 1530
BREAK2H = 13
BREAK2M = 45

# This is how long the breaks will take in minutes
# 30
BREAKLENGTH = 1

# this is the hour at which the competition will end. 
# 19
END = 14

# How many seconds between checks
# 37.5
SECONDS = 10

# Init vars
CHECKS= 0
SCORE = 0
POINTS = 100 / ((((END - START)*60)-((BREAKLENGTH*2)+GRACE)) / (SECONDS/60))
WEB_HOST = 'http://172.19.55.12'
TOM_HOST = 'http://172.19.55.13:8080'
FILE_HOST = '172.19.50.14'
MAIL_HOST = 'https://172.19.50.16'
SERVICES = {
        "WEBUP":False,
        "TOMUP":False,
        "DNSUP":False,
        "FILEUP":False,
        "MAILUP":False
        }
SMTP = smtplib.SMTP('172.19.50.16', 587)

# Clear the screen
subprocess.run("clear")

# Create a new log
LOG_FILE = "scoring-log-" + datetime.datetime.now().strftime('%m_%d_%H-%M') + ".log"
shutil.copy("scoring-log.sample", LOG_FILE)
log = open(LOG_FILE, "a")

# Start this script before the start time. It will wait until then to start
# actually running.

print("The scoring engine has started running at", datetime.datetime.now().strftime('%H:%M'))
while(datetime.datetime.now().hour < START):
    time.sleep(.001)

# First it will wait 40 minutes, or the grace period.
print("The competition has begun... starting the grace period.")
while(datetime.datetime.now().hour == START and datetime.datetime.now().minute< GRACE):
    time.sleep(.001)

# Then it will start scoring services. During the 30 minute breaks,
# it will pause and stop the scoring.
print("Scoring of services has begun at",datetime.datetime.now().strftime('%H:%M'))
# Changing this value will change when the competition ends
while (datetime.datetime.now().hour < END):

    #
    # Check to see if it's break time (1200-1230 and 1530-1600)
    #

    if ((datetime.datetime.now().hour == BREAK1H and datetime.datetime.now().minute == BREAK1M) or (datetime.datetime.now().hour == BREAK2H and datetime.datetime.now().minute == BREAK2M)):
        subprocess.run("clear")
        print("Break time has begun. Scoring of services has stopped.")
        time.sleep(BREAKLENGTH*60) # value has to be in seconds
    #
    # Get responses from the servers
    #
    if (CHECKS != 0):
        subprocess.run(["printf", "\\033[15A"])
   
    # Start timer
    starttime = time.time()

    # Apache Wordpress
    try: #reaching wordpress
        web = requests.get(url = WEB_HOST)
        if (web.ok):
            SERVICES["WEBUP"] = True
        else: 
            SERVICES["WEBUP"] = False
    except:
         SERVICES["WEBUP"] = False
    
    # Apache Tomcat
    try: #reaching tomcat
        tom = requests.get(url = TOM_HOST)
        if (tom.ok):
            SERVICES["TOMUP"] = True
        else:
            SERVICES["TOMUP"] = False
    except: 
        SERVICES["TOMUP"] = False
        
    # DNS Services
    try: #a DNS query
        socket.gethostbyname('google.com')
        SERVICES["DNSUP"] = True
    except:
        SERVICES["DNSUP"] = False

    # File Server Check
    try: #remounting the file share and checking for a file
        remount = "sudo mount -t cifs -o username=scoring,password=password //172.19.50.14/Files /home/install/files"
        subprocess.run(["sudo", "umount", "/home/install/files/"])
        subprocess.run(remount.split())
        open('/home/install/files/DONOTDELETE.txt')
        SERVICES["FILEUP"] = True
    except:
        SERVICES["FILEUP"] = False
    
    # Mail Server Check
    try: # to access the mail server
        mail = requests.get(url = MAIL_HOST, verify=False)
        if (mail.ok):
            SMTP = smtplib.SMTP('172.19.50.16',587)
            SMTP.ehlo()
            SMTP.starttls()
            SMTP.login("scoring@compb.muc-ish.de", "password")
    
            header = "From: scoring@compb.muc-ish.de\r\nTo: scoring.compb.muc-ish.de\r\n" 
            subjct = "Subject: Check " + str(CHECKS+1) + "\r\n\r\n"
            body   = "Scoring engine check " + str(CHECKS+1) + ". \nCompleted at " + datetime.datetime.now().strftime('%H:%M') + ".\nCurrent score is " + str(SCORE) + " points."
            msg = header + subjct + body
            try: # to send mail
                SMTP.sendmail("scoring@compb.muc-ish.de", ["scoring@compb.muc-ish.de"], msg)
                SERVICES["MAILUP"] = True
                SMTP.quit()
            except: 
                SERVICES["MAILUP"] = False
    
    except:
        SERVICES["MAILUP"] = False
  
    # New Service Check
    #try:
    #    test thing
    # except: 
    #     it dont work
    
    # End timer
    tottime = time.time() - starttime

    #
    # Show results
    #
    CHECKS += 1
    print("\n ------------------------")
    print(" | Check       :", CHECKS, "\t|")
    print(" | Time        :", datetime.datetime.now().strftime('%H:%M'), "\t|")
    print(" ------------------------")
    print(" | Wordpress   :", SERVICES["WEBUP"], "\t|")
    print(" | Tomcat      :", SERVICES["TOMUP"], "\t|")
    print(" | DNS         :", SERVICES["DNSUP"], "\t|")
    print(" | File Server :", SERVICES["FILEUP"], "\t|")
    print(" | Mail Server :", SERVICES["MAILUP"], "\t|")
    #print(" | Service     :", SERVICES["SERVICEUP"], "\t|")
    print(" ------------------------")
    
    #
    # Write results to the log
    #
    log.write("   " + str(CHECKS) + "\t| " + str(SERVICES["WEBUP"]) + "\t" + str(SERVICES["TOMUP"]) + "\t" + str(SERVICES["DNSUP"]) + "\t" + str(SERVICES["FILEUP"]) + "\t" + str(SERVICES["MAILUP"]) + "\t| " + datetime.datetime.now().strftime('%H:%M') + "\t| " + str(SCORE) + "\n")

    #
    # Calculate Score
    #
    count = 0.0
    for srv,up in SERVICES.items():
        if (up):
            count += 1.0
    # The multiplier here is how many points per service check.
    # it's calculated in the vars. For a ten hour competition,
    # with 37.5 second checks, it should be .125
    SCORE += (count / len(SERVICES))*POINTS
    
    print(" | Score       :", round(SCORE,2), "\t|")
    print(" ------------------------")
    print(" | Time        :", str(round(SECONDS - tottime,2)), "\t|")
    print(" ------------------------")
    
    # This value decides how long there is between 
    # service checks. Keep in mind each check takes
    # a few seconds on it's own.
    curtime = time.time()
    while(time.time() < curtime + SECONDS - tottime):
        subprocess.run(["printf", "\\033[2A"])
        print(" | Time        :", round((curtime+(SECONDS+.01-tottime))-time.time(),2), "\t|")
        print(" ------------------------")
    #(37.5 = .625 mins)

print("\nThe Competition has ended! Congratulations!")
print("You finished with", round(SCORE,6), "points!")
