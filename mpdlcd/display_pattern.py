# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Raphaël Barrois

"""Handle screen patterns."""

import collections
import logging

logger = logging.getLogger(__name__)


FIXED_TEXT_FIELD = 'fixed'


class FormatError(ValueError):
    pass


class ScreenPattern(object):
    def __init__(self, lines, field_registry):
        self.lines = lines
        self.line_fields = []
        self.widgets = {}
        self.field_registry = field_registry

    def parse(self):
        for line in self.lines:
            field_defs = self.parse_line(line)
            fields = []
            for (kind, options) in field_defs:
                logger.debug("Creating field %s(%r)", kind, options)
                fields.append(self.field_registry.create(kind, **options))

            self.line_fields.append(fields)
            for field in fields:
                self.widgets[field] = None

    def compute_positions(self, screen_width, line):
        left = 1
        right = screen_width + 1
        flexible = None

        for field in line:
            if field.is_flexible():
                if flexible:
                    raise FormatError(
                        'There can be only one flexible field per line.')
                flexible = field

            elif not flexible:
                left += field.width

            else:
                # Met a 'flexible', computing from the right
                right -= field.width

        available = right - left
        if available <= 0:
            raise FormatError("Too much data for screen width")

        if flexible:
            if available < 1:
                raise FormatError(
                    "Not enough space to display flexible field %s" %
                    flexible.name)

            flexible.width = available

        positions = []
        left = 1
        for field in line:
            positions.append((left, field))
            left += field.width

        logger.debug('Positions are %r', positions)
        return positions

    def add_to_screen(self, screen_width, screen):
        for lineno, fields in enumerate(self.line_fields):
            for left, field in self.compute_positions(screen_width, fields):
                logger.debug("Adding field %s to screen %s at x=%d->%d, y=%d",
                    field, screen.ref, left, left+field.width - 1, 1 + lineno)

                self.widgets[field] = field.add_to_screen(screen,
                    left, 1 + lineno)

    def time_changed(self, elapsed, total):
        for field, widget in self.widgets.iteritems():
            field.time_changed(widget, elapsed, total)

    def state_changed(self, new_state):
        for field, widget in self.widgets.iteritems():
            field.state_changed(widget, new_state)

    def song_changed(self, new_song):
        for field, widget in self.widgets.iteritems():
            field.song_changed(widget, new_song)

    def parse_line(self, line):
        """Parse a line of text.

        A format contains fields, within curly brackets, and free text.
        Maximum one 'variable width' field is allowed per line.
        You cannot use the '{' or '}' characters in the various text/... fields.

        Format:
            '''{<field_kind>[ <field_option>,<field_option]} text {...}'''

        Example:
            '''{song text="%(artist)s",speed=4} {elapsed}'''
            '''{song text="%(title)s",speed=2} {mode}'''

        Args:
            line (str): the text to parse

        Returns:
            PatternLine: the parsed line pattern
        """
        logger.debug('Parsing line %s', line)

        OUT_FIELD = 0
        IN_FIELD_KIND = 1
        IN_FIELD_OPTION_NAME = 2
        IN_FIELD_OPTION_VALUE = 3

        class ParserState(object):
            def __init__(self, logger=None):
                self.quote = None
                self.escaping = False
                self.block = []
                self.kind = ''
                self.option_name = ''
                self.options = {}
                self.state = OUT_FIELD
                self.fields = []
                if not logger:
                    logger = logging.getLogger('%s.parser' % __name__)
                self.logger = logger

            def _reset(self):
                self.quote = None
                self.escaping = False
                self.block = []

            def _register_field(self, kind, options):
                self.fields.append((kind, dict(options)))

            def debug(self, msg, *args, **kwargs):
                self.logger.debug(msg, *args, **kwargs)

            def save_fixed_text(self):
                assert self.state == OUT_FIELD
                self._register_field(FIXED_TEXT_FIELD,
                    {'text': ''.join(self.block)})

            def enter_field(self):
                self.debug('Entering new field')
                self.state = IN_FIELD_KIND
                self.kind = ''
                self.options = {}
                self.option_name = ''
                self._reset()

            def leave_kind(self):
                self.state = IN_FIELD_OPTION_NAME
                self.kind = ''.join(self.block)
                self.debug("Got widget kind '%s'", self.kind)
                self._reset()

            def leave_option_name(self):
                self.state = IN_FIELD_OPTION_VALUE
                self.option_name = ''.join(self.block)
                self.debug("Got option name '%s' for '%s'",
                    self.option_name, self.kind)
                self._reset()

            def leave_option_value(self):
                self.state = IN_FIELD_OPTION_NAME
                option_value = ''.join(self.block)
                self.options[self.option_name] = option_value
                self.debug("Got option '%s=%s' for '%s'",
                    self.option_name, option_value, self.kind)
                self._reset()

            def leave_field(self):
                self.state = OUT_FIELD
                self._register_field(self.kind, self.options)
                self.debug("Got widget '%s(%s)'", self.kind,
                    ', '.join('%s=%r' % it for it in self.options.iteritems()))
                self._reset()

        st = ParserState()

        for pos, char in enumerate(line):
            if st.escaping:
                st.escaping = False
                st.block.append(char)

            elif char == '\\':
                st.escaping = True

            elif char in ['"', "'"]:
                if st.state == IN_FIELD_OPTION_VALUE:
                    if st.quote:  # Already in a quoted block
                        if char == st.quote:
                            st.leave_option_value()
                        else:
                            st.block.append(char)

                    elif not st.block:  # First char of the block
                        st.quote = char
                        continue

                    else:
                        raise FormatError("Unexpected '%s' at %d in %s" %
                            (char, pos, line))

                elif st.state == OUT_FIELD:
                    st.block.append(char)

                else:
                    raise FormatError("Unexpected '%s' at %d in %s" %
                        (char, pos, line))

            elif char == '{':
                if st.state == OUT_FIELD:
                    if st.block:
                        st.save_fixed_text()
                    st.enter_field()

                elif st.state == IN_FIELD_OPTION_VALUE and st.quote:
                    st.block.append(char)

                else:
                    raise FormatError("Unexpected '{' at %d in %s" % (pos, line))

            elif char == '}':
                if st.state == IN_FIELD_KIND:
                    st.leave_kind()
                    st.leave_field()

                elif st.state == IN_FIELD_OPTION_NAME:
                    raise FormatError("Missing option value for %s at %d in %s"
                        % (''.join(st.block), pos, line))

                elif st.state == IN_FIELD_OPTION_VALUE:
                    if st.quote:
                        st.block.append(char)
                    else:
                        st.leave_option_value()
                        st.leave_field()

                elif st.state == OUT_FIELD:
                    raise FormatError("Unexpected '}' at %d in %s" % (pos, line))

            elif char == ' ':
                if st.state == IN_FIELD_KIND:
                    if not st.block:
                        raise FormatError("Missing field kind at %s in %s"
                            % (pos, line))

                    st.leave_kind()

                elif st.state == IN_FIELD_OPTION_VALUE and st.quote:
                    st.block.append(char)

                elif st.state == OUT_FIELD:
                    st.block.append(char)

                else:
                    raise FormatError("Unexpected ' ' at %d in %s" % (pos, line))

            elif char == ',':
                if st.state == IN_FIELD_OPTION_NAME:
                    if st.block:
                        raise FormatError("Missing option value for %s at %d in %s"
                            % (''.join(st.block), pos, line))
                    else:
                        # At the beginning of a new option
                        continue

                elif st.state == IN_FIELD_KIND:
                    raise FormatError(
                        "Unexpected ',' in field definition %s at %d in %s" %
                        (st.kind, pos, line))

                elif st.state == IN_FIELD_OPTION_VALUE:
                    if st.quote:
                        st.block.append(char)
                    elif st.block:
                        st.leave_option_value()
                    else:
                        raise FormatError(
                            "Missing option value for %s at %d in %s"
                            % (st.option_name, pos, line))

                else:  # OUT_FIELD
                    st.block.append(char)

            elif char == '=':
                if st.state == IN_FIELD_OPTION_NAME:
                    if st.block:
                        st.leave_option_name()

                    else:
                        raise FormatError(
                            "Missing option name at %d in %s" % (pos, line))

                elif st.state == OUT_FIELD:
                    st.block.append(char)

                elif st.state == IN_FIELD_OPTION_VALUE:
                    if st.quote:
                        st.block.append(char)

                    elif not st.block:
                        # At the beginning of an option
                        continue

                    else:
                        raise FormatError(
                            "Unexpected '=' in option value for %s at %d in %s"
                            % (st.option_name, pos, line))

                else:
                    raise FormatError("Unexpected '=' at %d in %s" % (pos, line))

            else:
                st.block.append(char)

        if st.state != OUT_FIELD:
            raise FormatError("Unclosed field at %d in '%s'; block: '%s'"
                % (pos, line, ''.join(st.block)))

        if st.block:
            st.save_fixed_text()

        return st.fields
