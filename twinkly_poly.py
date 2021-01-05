#!/usr/bin/env python3

"""
This is a NodeServer for Twinkly written by automationgeek (Jean-Francois Tremblay)
based on the NodeServer template for Polyglot v2 written in Python2/3 by Einstein.42 (James Milne) milne.james@gmail.com
"""

import polyinterface
import time
import json
import sys
from twinkly_client import TwinklyClient
from copy import deepcopy

LOGGER = polyinterface.LOGGER
SERVERDATA = json.load(open('server.json'))
VERSION = SERVERDATA['credits'][0]['version']

def get_profile_info(logger):
    pvf = 'profile/version.txt'
    try:
        with open(pvf) as f:
            pv = f.read().replace('\n', '')
    except Exception as err:
        logger.error('get_profile_info: failed to read  file {0}: {1}'.format(pvf,err), exc_info=True)
        pv = 0
    f.close()
    return { 'version': pv }

class Controller(polyinterface.Controller):

    def __init__(self, polyglot):
        super(Controller, self).__init__(polyglot)
        self.name = 'Twinkly'
        self.initialized = False
        self.queryON = False
        self.twinkly_host = ""
        self.tries = 0
        self.hb = 0

    def start(self):
        LOGGER.info('Started Twinkly for v2 NodeServer version %s', str(VERSION))
        self.setDriver('ST', 0)
        try:
            if 'host' in self.polyConfig['customParams']:
                self.milight_host = self.polyConfig['customParams']['host']
            else:
                self.milight_host = ""


            if self.milight_host == "" :
                LOGGER.error('Twinkly requires \'host\' parameters to be specified in custom configuration.')
                return False
            else:
                self.discover()
                self.query()

        except Exception as ex:
            LOGGER.error('Error starting Twinkly NodeServer: %s', str(ex))
            
        self.check_profile()
        self.heartbeat()

    def shortPoll(self):
        self.query()

    def longPoll(self):
        self.heartbeat()

    def query(self):
        self.setDriver('ST', 1)
        for node in self.nodes:
            if self.nodes[node].queryON == True :
                self.nodes[node].query()
            self.nodes[node].reportDrivers()

    def heartbeat(self):
        LOGGER.debug('heartbeat: hb={}'.format(self.hb))
        if self.hb == 0:
            self.reportCmd("DON",2)
            self.hb = 1
        else:
            self.reportCmd("DOF",2)
            self.hb = 0

    def discover(self, *args, **kwargs):
        time.sleep(1)
        count = 1
        for myHost in self.twinkly_host.split(','):
            uniq_name = "twinkly" + "_" + myHost.replace(".","") + "_" + str(count)
            self.addNode(Twinkly_Light(self, uniq_name , uniq_name, myHost ))
            time.sleep(1)
            count = count + 1

    def delete(self):
        LOGGER.info('Deleting Twinkly')

    def check_profile(self):
        self.profile_info = get_profile_info(LOGGER)
        # Set Default profile version if not Found
        cdata = deepcopy(self.polyConfig['customData'])
        LOGGER.info('check_profile: profile_info={0} customData={1}'.format(self.profile_info,cdata))
        if not 'profile_info' in cdata:
            cdata['profile_info'] = { 'version': 0 }
        if self.profile_info['version'] == cdata['profile_info']['version']:
            self.update_profile = False
        else:
            self.update_profile = True
            self.poly.installprofile()
        LOGGER.info('check_profile: update_profile={}'.format(self.update_profile))
        cdata['profile_info'] = self.profile_info
        self.saveCustomData(cdata)

    def install_profile(self,command):
        LOGGER.info("install_profile:")
        self.poly.installprofile()

    id = 'controller'
    commands = {
        'QUERY': query,
        'DISCOVER': discover,
        'INSTALL_PROFILE': install_profile,
    }
    drivers = [{'driver': 'ST', 'value': 1, 'uom': 2}]

class TwinklyLight(polyinterface.Node):

    def __init__(self, controller, primary, address, name, host):

        super(TwinklyLight, self).__init__(controller, primary, address, name)
        self.queryON = True
        self.myTwinkly = TwinklyClient(host)

    def start(self):
        self.query()

    def setOn(self, command):
        self.myTwinkly.set_is_on(True)
        self.setDriver('ST', 100,True)
        
    def setOff(self, command):
        self.myTwinkly.set_is_on(True)
        self.setDriver('ST', 0,True)
        
    def setBrightness(self, command):
        intBri = int(command.get('value'))
        self.myTwinkly.set_brightness(intBri)
        self.setDriver('GV1', intBri,True)
 
    def query(self):
        if ( self.myTwinkly.get_is_on() == True ) :
           self.setDriver('ST', 100,True) 
        else :
           self.setDriver('ST', 0,True) 
        
        self.setDriver('GV1', self.myTwinkly.get_brightness() , True)
                        
    drivers = [{'driver': 'ST', 'value': 0, 'uom': 78},
               {'driver': 'GV1', 'value': 0, 'uom': 51}]

    id = 'TWINKLY_LIGHT'
    commands = {
                    'DON': setOn,
                    'DOF': setOff,
                    'SET_BRI': setBrightness
                }

if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('TwinklyNodeServer')
        polyglot.start()
        control = Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
