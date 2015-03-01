import flask
import os
import datetime



class FormData:
	def __init__(self):
		self.dutyCycle = 0.0
		self.alarmEnabled = False
		self.musicEnabled = False
		self.wakeupTime = datetime.datetime.now().time()
		self.fadeDuration = 20
		self.setButtons = { 'Off' : 0.0, '30%' : 0.3, '70%' : 0.7, 'Full' : 1.0 }
	
	def __str__(self):
		result = 'dutyCycle={0}%, alarmEnabled={1}'.format( \
			100.0 * self.dutyCycle, self.alarmEnabled)
		if self.alarmEnabled:
			result += ', musicEnabled={0}, wakeupTime={1}, fadeDuration={2} min'.format( \
				self.musicEnabled, self.wakeupTime.strftime('%H:%M'), self.fadeDuration)
		return result
	
	def Parse(self):
		buttonLabel = flask.request.form['_submitButton']
		if buttonLabel in self.setButtons.keys():
			self.dutyCycle = self.setButtons[buttonLabel]
		elif buttonLabel == 'Save Alarm Settings':
			self.alarmEnabled = len(flask.request.form.getlist('_alarmEnabled')) > 0
			self.musicEnabled = len(flask.request.form.getlist('_musicEnabled')) > 0
			try:
				self.wakeupTime = datetime.datetime.strptime(
					flask.request.form['_wakeupTime'], '%H:%M').time()
			except ValueError:
				self.wakeupTime = datetime.datetime.now().time()
			self.fadeDuration = flask.request.form["_fadeDuration"]

	def Render(self):
		return flask.render_template('form.html',
			status = '{0:.0f}%'.format(100.0 * self.dutyCycle),
			alarmEnabled = "checked" if self.alarmEnabled else "",
			musicEnabled = "checked" if self.musicEnabled else "",
			wakeupTime = self.wakeupTime.strftime('%H:%M'),
			fadeDuration = self.fadeDuration)



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
	formData.Parse()
	print(str(formData))
	return formData.Render()

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=80, debug=True)

