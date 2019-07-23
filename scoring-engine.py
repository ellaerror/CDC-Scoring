import requests
import time
import socket
import subprocess
import datetime
import smtplib
import warnings
import shutil

warnings.filterwarnings("ignore")

# Init vars
CHECKS= 0
SCORE = 0
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

# Start this script before 0900. It will wait until then to start
# actually running.

print("The scoring engine has started running at", datetime.datetime.now().strftime('%H:%M'))
while(datetime.datetime.now().hour < 9):
    time.sleep(.001)

# First it will wait 40 minutes, or the grace period.
print("The competition has begun... starting the grace period.")
while(datetime.datetime.now().hour == 9 and datetime.datetime.now().minute< 40):
    time.sleep(.001)

# Then it will start scoring services. During the 30 minute breaks,
# it will pause and stop the scoring.
print("Scoring of services has begun at",datetime.datetime.now().strftime('%H:%M'))
# Changing this value will change when the competition ends
while (datetime.datetime.now().hour < 19):

    #
    # Check to see if it's break time (1200-1230 and 1530-1600)
    #

    if ((datetime.datetime.now().hour == 12 and datetime.datetime.now().minute == 0) or (datetime.datetime.now().hour == 15 and datetime.datetime.now().minute == 30)):
        subprocess.run("clear")
        print("Break time has begun. Scoring of services has stopped.")
        time.sleep(1800) #1800 = 30 min
    #
    # Get responses from the servers
    #
    if (CHECKS != 0):
        subprocess.run(["printf", "\\033[15A"])
    
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
    print(" ------------------------")
    
    #
    # Write results to the log
    #
    log.write("   " + str(CHECKS) + "\t| " + str(SERVICES["WEBUP"]) + "\t" + str(SERVICES["TOMUP"]) + "\t" + str(SERVICES["DNSUP"]) + "\t" + str(SERVICES["FILEUP"]) + "\t" + str(SERVICES["MAILUP"]) + "\t| " + datetime.datetime.now().strftime('%H:%M') + "\n")

    #
    # Calculate Score
    #
    count = 0.0
    for srv,up in SERVICES.items():
        if (up):
            count += 1.0
    # The multiplier here is how many points per service check.
    # This number should be 20% of the minutes per check
    SCORE += (count / len(SERVICES))*.125
    
    print(" | Score       :", round(SCORE,6), "\t|")
    print(" ------------------------")
    print(" | Time        :", "37", "\t|")
    print(" ------------------------")
    
    # This value decides how long there is between 
    # service checks. Keep in mind each check takes
    # a few seconds on it's own.
    curtime = time.time()
    while(time.time() < curtime + 37.5 ):
        subprocess.run(["printf", "\\033[2A"])
        print(" | Time        :", round((curtime+37.51)-time.time(),2), "\t|")
        print(" ------------------------")
    #(37.5 = .625 mins)

print("\nThe Competition has ended! Congratulations!")
print("You finished with", round(SCORE,6), "points!")
