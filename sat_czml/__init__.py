import datetime
from pyorbital.orbital import Orbital


class Satellite(object):

    def __init__(self, name, speed=60, orbit_count=1):
        self.name = name
        self.orbit = Orbital(name)
        self.NUM_STEPS = 255
        self.speed = speed
        self.orbit_count = orbit_count

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
            'id': 'path',
            'availability': start_time + '/' + end_time,
            'position': {
                'epoch': start_time,
                'cartographicDegrees': ground_track
            },

            'path': {
                "material": {
                    "polylineOutline": {
                        "color": {
                            "rgba": [255, 255, 255, 200]
                        },
                        "outlineColor": {
                            "rgba": [0, 173, 253, 200]
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
            "id": "point",

            "availability": start_time + '/' + end_time,

            "position": {
                "epoch": start_time,
                "cartographicDegrees": ground_track
            },

            "point": {
                "color": {
                    "rgba": [255, 255, 255, 255]
                },
                "outlineColor": {
                    "rgba": [0, 173, 253, 255]
                },
                "outlineWidth": 15,
                "heightReference": "RELATIVE_TO_GROUND"
            }
        }
        output.append(point_object)

        # Corridor (swath width)
        corridor_object = {
            'id': 'corridor',
            'name': 'swath',
            'corridor': {
                'positions': {
                    'cartographicDegrees': self.ground_track(time=False, altitude=False)
                },
                'width': 185000,
                "material": {
                    "solidColor": {
                        "color": {
                            "rgba": [255, 0, 0, 127]
                        }
                    }
                }
            }

        }
        output.append(corridor_object)

        return output