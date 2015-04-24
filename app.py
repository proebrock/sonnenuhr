import datetime
import flask
import math
import os
import shlex
import subprocess
import threading
import time



def RunShell(commandLine):
	command = shlex.split(commandLine)
	process = subprocess.Popen(command, shell=False, \
		stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = process.communicate()
	return process.returncode, out, err



class PwmOutput:
	# Uses the WiringPi tools (https://github.com/WiringPi)
	def __init__(self, dummyMode=False):
		self.dummyMode = dummyMode
		self.dutyCycle = 0.0
		if not self.dummyMode:
			RunShell('gpio unexport 1')
			RunShell('gpio mode 1 pwm')
			RunShell('gpio pwm-ms')
			# Base frequency 19.200.000Hz / 96 / 1000 = 200Hz
			RunShell('gpio pwmr 1000')
			RunShell('gpio pwmc 96')

	def __str__(self):
		return 'PwmOutput(dummyMode={0}, dutyCycle={1})'.format(self.dummyMode, self.dutyCycle)

	def SetDutyCycle(self, dutyCycle):
		self.dutyCycle = dutyCycle
		if not self.dummyMode:
			RunShell('gpio pwm 1 {0}'.format( \
				int(round(1000.0 * dutyCycle))))

	def GetDutyCycle(self):
		return self.dutyCycle



class AlarmClock:

	def __init__(self):
		now = datetime.datetime.now()
		self.startSec = 3600.0 * now.hour + 60.0 * now.minute + now.second + (now.microsecond / 1000000.0) + 70.0
		self.stopSec = self.startSec + 70.0
		self.alarmActive = False
		self.pwm = PwmOutput(True)
		self.cancel = False
		self.isRunning = False

	def __str__(self):
		return 'AlarmClock(isRunning={0}, startSec={1}, stopSec={2}, alarmActive={3}, self.pwm={4})'.format( \
			self.isRunning, self.startSec, self.stopSec, self.alarmActive, self.pwm)

	def SetEnabled(self, enabled):
		if enabled:
			if not self.isRunning:
				print('Starting alarm clock ...')
				self.cancel = False
				self.thread = threading.Thread(target = self.__Worker)
				self.thread.start()
				self.isRunning = True
		else:
			if self.isRunning:
				print('Stopping alarm clock ...')
				self.cancel = True
				self.thread.join()
				self.isRunning = True

	def GetEnabled(self):
		return self.isRunning
	
	def SetTimings(self, startSec, stopSec):
		self.startSec = startSec
		self.stopSec = stopSec
	
	def GetTimings(self):
		return (self.startSec, self.stopSec)

	def SetIntensity(self, intensity):
		self.alarmActive = False;
		self.pwm.SetDutyCycle(intensity)

	def GetIntensity(self):
		return self.pwm.GetDutyCycle()

	def __SetIntensityByTime(self, nowSec):
		# Calculate percentage by allowing alarm duration over midnight
		p = nowSec - self.startSec
		if p < 0.0:
			p += 24.0 * 3600.0
		q = self.stopSec - self.startSec
		if q < 0.0:
			q += 24.0 * 3600.0
		# Clamp value to 0..1
		r = max(0.0, min(p/q, 1.0))
		self.pwm.SetDutyCycle(r)

	def __Worker(self):
		cycleTimeSec = 1.0
		while not self.cancel:
			# Get current time
			now = datetime.datetime.now()
			nowSec = (3600.0 * now.hour) + (60.0 * now.minute) + \
				now.second + (now.microsecond / 1000000.0)
			if self.alarmActive:
				self.__SetIntensityByTime(nowSec)
				# If stop time is now, stop alarm
				if abs(self.stopSec - nowSec) <= cycleTimeSec/2.0:
					self.alarmActive = False
			else:
				# If start time is now, start alarm
				if abs(self.startSec - nowSec) <= cycleTimeSec/2.0:
					self.alarmActive = True
					self.__SetIntensityByTime(nowSec)
			print(str(self))
			time.sleep(cycleTimeSec)
		return



class FormData:
	def __init__(self):
		self.alarmClock = AlarmClock()
		self.musicEnabled = False
		self.setButtons = { 'Off' : 0.0, '5%' : 0.05, '60%' : 0.6, 'Full' : 1.0 }

	def __str__(self):
		return 'FormData(alarmEnabled={0}, musicEnabled={1}, wakeupTime={2}, fadeDuration={3})'.format( \
			len(flask.request.form.getlist('_alarmEnabled')) > 0,
			len(flask.request.form.getlist('_musicEnabled')) > 0,
			flask.request.form['_wakeupTime'],
			flask.request.form["_fadeDuration"])

	def Parse(self):
		buttonLabel = flask.request.form['_submitButton']
		if buttonLabel in self.setButtons.keys():
			self.alarmClock.SetIntensity(self.setButtons[buttonLabel])
		elif buttonLabel == 'Save Alarm Settings':
			self.alarmClock.SetEnabled(len(flask.request.form.getlist('_alarmEnabled')) > 0)
			self.musicEnabled = len(flask.request.form.getlist('_musicEnabled')) > 0
			try:
				wakeupTime = datetime.datetime.strptime(
					flask.request.form['_wakeupTime'], '%H:%M').time()
			except ValueError:
				wakeupTime = datetime.datetime.now().time()
			fadeDuration = 60.0 * float(flask.request.form["_fadeDuration"])
			stopSec = 3600.0 * wakeupTime.hour + 60.0 * wakeupTime.minute + \
				wakeupTime.second + (wakeupTime.microsecond / 1000000.0)
			startSec = stopSec - fadeDuration
			if startSec < 0:
				startSec += 24.0 * 3600.0
			self.alarmClock.SetTimings(startSec, stopSec)

	def Render(self):
		startSec, stopSec = self.alarmClock.GetTimings()
		wakeupTime = '{0:02.0f}:{1:02.0f}'.format(math.floor(stopSec / 3600.0), \
			round(stopSec - 3600.0 * math.floor(stopSec / 3600.0)) / 60.0)
		fadeDuration = stopSec - startSec
		if (fadeDuration < 0):
			fadeDuration += 24.0 * 3600.0
		fadeDuration = '{0:.0f}'.format(round(fadeDuration / 60.0))
		return flask.render_template('form.html',
			status = '{0:.0f}%'.format(100.0 * self.alarmClock.GetIntensity()),
			alarmEnabled = "checked" if self.alarmClock.GetEnabled() else "",
			musicEnabled = "checked" if self.musicEnabled else "",
			wakeupTime=wakeupTime, fadeDuration=fadeDuration)



app = flask.Flask(__name__)
formData = FormData()

@app.route('/favicon.ico')
def favicon():
	return flask.send_from_directory(os.path.join(app.root_path, 'static'), \
		'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def form():
	return formData.Render()

@app.route('/', methods=['POST'])
def post():
	print(str(formData))
	formData.Parse()
	print(str(formData.alarmClock))
	return formData.Render()

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=80, debug=True)

