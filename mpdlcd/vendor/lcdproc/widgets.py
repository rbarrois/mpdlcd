# Copyright (c) 2015, JingleManSweep
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the <organization> nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


class StringWidget(object):
    """ String Widget """

    def __init__(self, screen, ref, x, y, text):
        self.screen = screen
        self.ref = ref
        self.x = x
        self.y = y
        self.text = text

        self.screen.server.request("widget_add %s %s %s" % (self.screen.ref, self.ref, "string"))
        self.update()

    def update(self):
        self.screen.server.request(
            'widget_set %s %s %s %s "%s"' % (self.screen.ref, self.ref, self.x, self.y, self.text),
        )

    def set_x(self, x):
        self.x = x
        self.update()

    def set_y(self, y):
        self.y = y
        self.update()

    def set_text(self, text):
        self.text = text
        self.update()


class TitleWidget(object):
    """ Title Widget """

    def __init__(self, screen, ref, text):
        self.screen = screen
        self.ref = ref
        self.text = text

        self.screen.server.request("widget_add %s %s %s" % (self.screen.ref, self.ref, "title"))
        self.update()

    def update(self):
        self.screen.server.request('widget_set %s %s "%s"' % (self.screen.ref, self.ref, self.text))

    def set_text(self, text):
        self.text = text
        self.update()


class HBarWidget(object):

    def __init__(self, screen, ref, x, y, length):
        self.screen = screen
        self.ref = ref
        self.x = x
        self.y = y
        self.length = length

        self.screen.server.request("widget_add %s %s %s" % (self.screen.ref, self.ref, "hbar"))
        self.update()

    def update(self):
        self.screen.server.request(
            "widget_set %s %s %s %s %s" % (self.screen.ref, self.ref, self.x, self.y, self.length),
        )

    def set_x(self, x):
        self.x = x
        self.update()

    def set_y(self, y):
        self.y = y
        self.update()

    def set_length(self, length):
        self.length = length
        self.update()


class VBarWidget(object):

    def __init__(self, screen, ref, x, y, length):
        self.screen = screen
        self.ref = ref
        self.x = x
        self.y = y
        self.length = length

        self.screen.server.request("widget_add %s %s %s" % (self.screen.ref, self.ref, "vbar"))
        self.update()

    def update(self):
        self.screen.server.request(
            "widget_set %s %s %s %s %s" % (self.screen.ref, self.ref, self.x, self.y, self.length),
        )

    def set_x(self, x):
        self.x = x
        self.update()

    def set_y(self, y):
        self.y = y
        self.update()

    def set_length(self, length):
        self.length = length
        self.update()


class IconWidget(object):

    def __init__(self, screen, ref, x, y, name):
        self.screen = screen
        self.ref = ref
        self.x = x
        self.y = y
        self.name = name

        self.screen.server.request("widget_add %s %s %s" % (self.screen.ref, self.ref, "icon"))
        self.update()

    def update(self):
        self.screen.server.request("widget_set %s %s %s %s %s" % (self.screen.ref, self.ref, self.x, self.y, self.name))

    def set_x(self, x):
        self.x = x
        self.update()

    def set_y(self, y):
        self.y = y
        self.update()

    def set_name(self, name):
        self.name = name
        self.update()


class ScrollerWidget(object):

    def __init__(self, screen, ref, left, top, right, bottom, direction, speed, text):
        self.screen = screen
        self.ref = ref
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom
        self.direction = direction
        self.speed = speed
        self.text = text

        self.screen.server.request("widget_add %s %s %s" % (self.screen.ref, self.ref, "scroller"))
        self.update()

    def update(self):
        self.screen.server.request(
            'widget_set %s %s %s %s %s %s %s %s "%s"' % (
                self.screen.ref,
                self.ref,
                self.left,
                self.top,
                self.right,
                self.bottom,
                self.direction,
                self.speed,
                self.text,
            ))

    def set_left(self, left):
        self.left = left
        self.update()

    def set_top(self, top):
        self.top = top
        self.update()

    def set_right(self, right):
        self.right = right
        self.update()

    def set_bottom(self, bottom):
        self.bottom = bottom
        self.update()

    def set_direction(self, direction):
        self.direction = direction
        self.update()

    def set_speed(self, speed):
        self.speed = speed
        self.update()

    def set_text(self, text):
        self.text = text
        self.update()


class FrameWidget(object):

    def __init__(self, screen, ref, left, top, right, bottom, width, height, direction, speed):
        self.screen = screen
        self.ref = ref
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom
        self.width = width
        self.height = height
        self.direction = direction
        self.speed = speed

        self.screen.server.request("widget_add %s %s %s" % (self.screen.ref, self.ref, "frame"))
        self.update()

    def update(self):
        self.screen.server.request(
            'widget_set %s %s %s %s %s %s %s %s %s %s' % (
                self.screen.ref,
                self.ref,
                self.left,
                self.top,
                self.right,
                self.bottom,
                self.width,
                self.height,
                self.direction,
                self.speed,
            ))

    def set_left(self, left):
        self.left = left
        self.update()

    def set_top(self, top):
        self.top = top
        self.update()

    def set_right(self, right):
        self.right = right
        self.update()

    def set_bottom(self, bottom):
        self.bottom = bottom
        self.update()

    def set_width(self, width):
        self.width = width
        self.update()

    def set_height(self, height):
        self.height = height
        self.update()

    def set_direction(self, direction):
        self.direction = direction
        self.update()

    def set_speed(self, speed):
        self.speed = speed
        self.update()


class NumberWidget(object):

    def __init__(self, screen, ref, x, value):
        self.screen = screen
        self.ref = ref
        self.x = x
        self.value = value

        self.screen.server.request("widget_add %s %s %s" % (self.screen.ref, self.ref, "num"))
        self.update()

    def update(self):
        self.screen.server.request('widget_set %s %s %s %s' % (self.screen.ref, self.ref, self.x, self.value))

    def set_x(self, x):
        self.x = x
        self.update()

    def set_value(self, value):
        self.value = value
        self.update()
