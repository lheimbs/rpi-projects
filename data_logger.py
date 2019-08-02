#!/home/pi/projects/rpi-projects/venv/bin/python3
# coding=utf-8

import ADC0832
import Adafruit_DHT
import time, datetime, os, traceback, subprocess

FILE_FOLDER = os.path.join(os.sep, 'home', 'pi', 'log')
RESULT_FILE = 'results.csv'
LOG_FILE = 'data_logger.log'
start_time = time.time()

def log(logstring):
    with open(os.path.join(FILE_FOLDER, LOG_FILE), 'a+') as logfile:
        curr_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        logfile.write(curr_time + ":   " + str(logstring))

def init():
    log('Script started')
    # Setup the photoresistor
    ADC0832.setup()
    # setup current week
    date = datetime.datetime.now()
    CURR_WEEK=date.isocalendar()[1]
    # 
    weekly_res_file(CURR_WEEK)
    return CURR_WEEK

def check_res_file():
    num_res_files = len([name for name in os.listdir('.') if os.path.isfile(name) and RESULT_FILE[:-5] in name])
    
    if num_res_files > 0:
        size_curr_res_file = os.stat(RESULT_FILE).st_size

        if size_curr_res_file > 1024*1024*100:
            new_res_file = RESULT_FILE[:-4] + str(num_res_files+1) + RESULT_FILE[-4:]
            log("Logfile too big; renaming to: '%s'" % new_res_file)
            os.rename(RESULT_FILE, new_res_file)

def weekly_res_file(CURR_WEEK):
    date = datetime.datetime.now()
    week = date.isocalendar()[1]
    if week > CURR_WEEK or week < CURR_WEEK:
        print("Change Week")
        res_save_name = "week-" + str(week) + "-results.csv"
        retVal = subprocess.call(["cp", os.path.join(FILE_FOLDER, RESULT_FILE), res_save_name])
        with open(os.path.join(FILE_FOLDER, LOG_FILE), 'a+') as logfile:
            subprocess.call(["echo", "date,time,temperature,humidity,brighness"], stdout=logfile)
        return week
    else:
        return CURR_WEEK

def write_to_file(res_string):
    with open(os.path.join(FILE_FOLDER, RESULT_FILE), 'a+') as file:
        file.write(res_string)

def main():
    CURR_WEEK=init()
    while True:
        # read dht11
        humidity, temperature = Adafruit_DHT.read_retry(11, 17)

        # read photoresistor
        light = ADC0832.getResult()
            
        curr_datetime = datetime.datetime.now()
        curr_date = curr_datetime.strftime('%d-%m-%Y')
        curr_time = curr_datetime.strftime('%H:%M:%S')
        write_to_file("%s,%s,%d,%d,%d\n" % (curr_date,curr_time,temperature, humidity, light))

        CURR_WEEK = weekly_res_file(CURR_WEEK)
        time.sleep(60.0 - ((time.time() - start_time) % 60.0))

if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        ADC0832.destroy()
        log("Finished")
        print('Finished')
    except Exception as e:
        log("Error: " + str(e))
        log(traceback.format_exc())
        print(traceback.format_exc())
