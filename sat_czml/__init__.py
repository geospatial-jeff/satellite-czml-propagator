import datetime
from multiprocessing import Process, Pipe

from pyorbital.orbital import Orbital


class Satellite(object):

    def __init__(self, name, speed=60, orbit_count=1, swath_color=(255, 0, 0, 127), track_color=(255, 255, 255, 200), swath_width=10000):
        self.name = name
        self.orbit = Orbital(name)
        self.NUM_STEPS = 255
        self.speed = speed
        self.orbit_count = orbit_count
        self.swath_width = swath_width

        # Styling
        self.swath_color = swath_color
        self.track_color = track_color

    @property
    def period(self):
        return self.orbit.orbit_elements.period * self.orbit_count

    @property
    def time(self):
        return datetime.datetime.utcnow()

    @property
    def timestep(self):
        return (self.period / self.NUM_STEPS) * 60

    def time_steps(self):
        steps = []
        start_time = self.time
        for step in range(self.NUM_STEPS):
            step_info = {'startTime': start_time}
            start_time += datetime.timedelta(seconds=self.timestep)
            step_info.update({'endTime': start_time})
            steps.append(step_info)
        return steps

    def ground_track(self, time=True, altitude=True):
        duration = 0
        track = []
        for item in [self.orbit.get_lonlatalt(x['startTime']) for x in self.time_steps()]:
            if time:
                track.append(duration)
            track.append(item[0])
            track.append(item[1])
            if altitude:
                track.append(1000 * item[2])
            else:
                track.append(0)
            duration += self.timestep
        return track

    def to_czml(self):
        output = []
        time_steps = self.time_steps()
        ground_track = self.ground_track()
        start_time = time_steps[0]['startTime'].strftime("%Y-%m-%dT%H:%M:%S")
        end_time = time_steps[-1]['endTime'].strftime("%Y-%m-%dT%H:%M:%S")

        # Global packet
        global_element = {
            'id': 'document',
            'name': self.name,
            'version': '1.0',

            'clock': {
                'interval': start_time + '/' + end_time,
                'currentTime': start_time,
                'multiplier': self.speed,
            }
        }
        output.append(global_element)

        # Path object
        path_object = {
            'id': self.name + '/Propagated Orbit',
            'name': self.name + ' Propagated Orbit',
            'availability': start_time + '/' + end_time,
            'position': {
                'epoch': start_time,
                'cartographicDegrees': ground_track
            },

            'path': {
                "material": {
                    "polylineOutline": {
                        "color": {
                            "rgba": self.track_color
                        },
                        "outlineColor": {
                            "rgba": [255, 255, 255, 200]
                        },
                        "outlineWidth": 5
                    }
                },
                'width': 1,
                'resolution': 120,
            }
        }
        output.append(path_object)

        # Point variable
        point_object = {
            "id": self.name + '/Satellite',
            "name": self.name + " Satellite",

            "availability": start_time + '/' + end_time,

            "position": {
                "epoch": start_time,
                "cartographicDegrees": ground_track
            },
            "billboard": {
                "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAADJSURBVDhPnZHRDcMgEEMZjVEYpaNklIzSEfLfD4qNnXAJSFWfhO7w2Zc0Tf9QG2rXrEzSUeZLOGm47WoH95x3Hl3jEgilvDgsOQUTqsNl68ezEwn1vae6lceSEEYvvWNT/Rxc4CXQNGadho1NXoJ+9iaqc2xi2xbt23PJCDIB6TQjOC6Bho/sDy3fBQT8PrVhibU7yBFcEPaRxOoeTwbwByCOYf9VGp1BYI1BA+EeHhmfzKbBoJEQwn1yzUZtyspIQUha85MpkNIXB7GizqDEECsAAAAASUVORK5CYII=",
                "scale": 2
            },
            "label":{
              "fillColor":{
                "rgba":[
                  0,255,0,255
                ]
              },
              "font":"15pt Lucida Console",
              "horizontalOrigin":"LEFT",
              "outlineColor":{
                "rgba":[
                  0,0,0,255
                ]
              },
              "outlineWidth":4,
              "pixelOffset":{
                "cartesian2":[
                  12,0
                ]
              },
              "style":"FILL_AND_OUTLINE",
              "text": self.name,
              "verticalOrigin":"CENTER",
            }
        }
        output.append(point_object)

        # Corridor (swath width)
        corridor_object = {
            'id': self.name + '/Corridor',
            'name': self.name + ' Ground Swath',
            'corridor': {
                'positions': {
                    'cartographicDegrees': self.ground_track(time=False, altitude=False)
                },
                'width': self.swath_width,
                "material": {
                    "solidColor": {
                        "color": {
                            "rgba": self.swath_color
                        }
                    }
                }
            }

        }
        output.append(corridor_object)

        return output

    def to_czml_multi(self, placeholder, conn):
        conn.send(self.to_czml())
        conn.close()

class Constellation(object):

    @classmethod
    def load(cls, arg_list):
        satellites = [Satellite(**x) for x in arg_list]
        return cls(satellites)

    def __init__(self, satellites):
        self.satellites = satellites

    def execute(self):
        response = {}

        processes = []
        parent_connections = []

        for satellite in self.satellites:
            parent_conn, child_conn = Pipe()
            parent_connections.append(parent_conn)
            process = Process(target=satellite.to_czml_multi, args=('', child_conn))
            processes.append(process)

        for process in processes:
            process.start()

        for process in processes:
            process.join()

        for parent_connection in parent_connections:
            resp = parent_connection.recv()
            response.update({resp[0]['name']: resp})

        return response