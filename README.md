# Sonnenuhr

"Sonnenuhr" is German for "sundisk". It is basically a disc-shaped very bright lamp you can put into your bedroom. You program the alarm time of the lamp by its website in your LAN, e.g. with your cellphone. At alarm, the lamp will slowly start to get brighter and brighter some time before wakeup time. Just the right way to wake up in the dark time of the year!

## Schematics

For this project we use the following material:

* A Raspberry Pi of any type. We just need a single 3.3V driven GPIO.
* A powerful LED light source from Barthelme LED Solutions (50762933): A disc of 290mm diameter with multiple white power LEDs. The module contains can be powered directly with 24V with 31.20W. The luminous flux is 3241 lm. It can be ordered from Conrad under order number [1275401-62](https://www.conrad.ch/de/led-baustein-weiss-3120-w-3241-lm-120-24-v-barthelme-50762933-1275401.html).
* A power MOSFET to switch the 24V and 1.3A. The MOSFET I picked is capable of much more: Internatinal Rectifier / Infineon Technologies IRFZ48VPBF N-Channel 150W (TO-220). Further details can be found on the manufacturer's website [here](https://www.infineon.com/dgdl/irfz48vpbf.pdf?fileId=5546d462533600a40153563ec0b92233). It can be ordered from Conrad under order number [162757-62](https://www.conrad.ch/de/mosfet-infineon-technologies-irfz48vpbf-1-n-kanal-150-w-to-220-162757.html).
* An optocoupler for a secure isolation between the 3.3V voltage of the Raspberry Pi and the 24V power: An Everlight EL817. Further details can be found on the manufacturer's website [here](https://everlighteurope.com/index.php?controller=attachment&id_attachment=1158).

This is the schematics:

[Schematics](schematics.png)

*R1: Optocoupler forward voltage 1.2V, forward current 20mA; R1=(3.3V-1.2V)/0.02A=105Ohm
* R2/R3: Vgs(th)=2..4V; take at least double of that to open D-S; so lets pick R2=22kOhm, R3=15kOhm with U_R2=14.3V and U_R3=9.7V; I=24V/(22kOhm+15kOhm)=0.65mA; Max Current 50mA -> OK!

## Software basics

The application is based on Python [Flask](http://flask.pocoo.org/) to create a website that is capable of accessing low level GPIO in the Raspberry Pi which is done by [WiringPi](http://wiringpi.com/).

## Installation and start

* Put Raspberry pi in your WLAN
* raspi-config -> set timezone, make sure NTP is active
* sudo apt-get install git tmux python-flask
* git clone https://github.com/proebrock/sonnenuhr.git
* cd sonnenuhr; sudo python app.py
