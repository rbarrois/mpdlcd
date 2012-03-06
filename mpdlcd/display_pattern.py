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
    """A screen pattern description.

    Attributes:
        lines (str list): the lines of the pattern
        line_fields (mpdlcd.display_fields.Field list list): List of the fields
            for each line.
        widgets (dict(mpdlcd.display_fields.Field => lcdproc.Widget)): widget to
            use for each field
        field_registry (mpdlcd.display_fields.FieldRegistry): the registry of
            available fields.
    """

    def __init__(self, lines, field_registry):
        self.lines = lines
        self.line_fields = []
        self.widgets = {}
        self.field_registry = field_registry

    def parse(self):
        """Parse the lines, and fill self.line_fields accordingly."""
        for line in self.lines:
            # Parse the line
            field_defs = self.parse_line(line)
            fields = []

            # Convert field parameters into Field objects
            for (kind, options) in field_defs:
                logger.debug("Creating field %s(%r)", kind, options)
                fields.append(self.field_registry.create(kind, **options))

            # Add the list of Field objects to the 'fields per line'.
            self.line_fields.append(fields)

            # Pre-fill the list of widgets
            for field in fields:
                self.widgets[field] = None

    @classmethod
    def compute_positions(cls, screen_width, line):
        """Compute the relative position of the fields on a given line.

        Args:
            screen_width (int): the width of the screen
            line (mpdlcd.display_fields.Field list): the list of fields on the
                line

        Returns:
            ((int, mpdlcd.display_fields.Field) list): the positions of fields,
                as (position, field) tuples.

        Raises:
            FormatError: if the line contains more than one flexible field, or
                is too long for the screen size.
        """
        # First index
        left = 1
        # Last index
        right = screen_width + 1
        # Current 'flexible' field
        flexible = None

        # Compute the space to the left and to the right of the (optional)
        # flexible field.
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

        # Available space for the 'flexible' field
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
        """Add the pattern to a screen.

        Also fills self.widgets.

        Args:
            screen_width (int): the width of the screen
            screen (lcdprod.Screen): the screen to fill.
        """
        for lineno, fields in enumerate(self.line_fields):
            for left, field in self.compute_positions(screen_width, fields):
                logger.debug("Adding field %s to screen %s at x=%d->%d, y=%d",
                    field, screen.ref, left, left+field.width - 1, 1 + lineno)

                self.widgets[field] = field.add_to_screen(screen,
                    left, 1 + lineno)

    def time_changed(self, elapsed, total):
        """Called whenever the elapsed/total time of MPD changed."""
        for field, widget in self.widgets.iteritems():
            field.time_changed(widget, elapsed, total)

    def state_changed(self, new_state):
        """Called whenever the state of MPD changed."""
        for field, widget in self.widgets.iteritems():
            field.state_changed(widget, new_state)

    def song_changed(self, new_song):
        """Called whenever the current song changed."""
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
            """Holds the current state of the parser.

            Attributes:
                quote (str): the current quote character, or None
                escaping (bool): whether the next character should be escaped
                block (char list): the content of the current 'block'
                kind (str): the kind of the current field, or ''
                option_name (str): the name of the current option, or ''
                options (dict(str => str)): maps option name to option value for
                    the current field
                state (int): state of the parser,one of OUT_FIELD/IN_FIELD_*
                fields ((str, dict(str => str)) list): list of fields, as
                    (kind, options) tuples.
            """

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
                """Reset buffered state (quote/escape/block)."""
                self.quote = None
                self.escaping = False
                self.block = []

            def _register_field(self, kind, options):
                """Register a completed field."""
                self.fields.append((kind, dict(options)))

            def debug(self, msg, *args, **kwargs):
                """Print a debug message."""
                self.logger.debug(msg, *args, **kwargs)

            def save_fixed_text(self):
                """Register a completed, fixed text, field."""
                assert self.state == OUT_FIELD
                self._register_field(FIXED_TEXT_FIELD,
                    {'text': ''.join(self.block)})

            def enter_field(self):
                """Enter a new field."""
                self.debug('Entering new field')
                self.state = IN_FIELD_KIND
                self.kind = ''
                self.options = {}
                self.option_name = ''
                self._reset()

            def leave_kind(self):
                """Leave the field kind."""
                self.state = IN_FIELD_OPTION_NAME
                self.kind = ''.join(self.block)
                self.debug("Got widget kind '%s'", self.kind)
                self._reset()

            def leave_option_name(self):
                """Leave an option name."""
                self.state = IN_FIELD_OPTION_VALUE
                self.option_name = ''.join(self.block)
                self.debug("Got option name '%s' for '%s'",
                    self.option_name, self.kind)
                self._reset()

            def leave_option_value(self):
                """Leave an option value."""
                self.state = IN_FIELD_OPTION_NAME
                option_value = ''.join(self.block)
                self.options[self.option_name] = option_value
                self.debug("Got option '%s=%s' for '%s'",
                    self.option_name, option_value, self.kind)
                self._reset()

            def leave_field(self):
                """Leave a field definition."""
                self.state = OUT_FIELD
                self._register_field(self.kind, self.options)
                self.debug("Got widget '%s(%s)'", self.kind,
                    ', '.join('%s=%r' % it for it in self.options.iteritems()))
                self._reset()

        st = ParserState()

        for pos, char in enumerate(line):

            # Escaping
            if st.escaping:
                st.escaping = False
                st.block.append(char)

            elif char == '\\':
                st.escaping = True

            # Quoting
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

            # Entering a field
            elif char == '{':
                if st.state == OUT_FIELD:
                    if st.block:
                        st.save_fixed_text()
                    st.enter_field()

                elif st.state == IN_FIELD_OPTION_VALUE and st.quote:
                    st.block.append(char)

                else:
                    raise FormatError("Unexpected '{' at %d in %s" % (pos, line))

            # Leaving a field
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

            # Between kind and option name
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

            # Between options
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

            # Between option name and option value
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

            # Everything else
            else:
                st.block.append(char)

        # All input parsed
        if st.state != OUT_FIELD:
            raise FormatError("Unclosed field at %d in '%s'; block: '%s'"
                % (pos, line, ''.join(st.block)))

        if st.block:
            st.save_fixed_text()

        return st.fields


class ScreenPatternList(object):
    """Hold a list of possible patterns.

    Attributes:
        patterns (dict(int => str list)): maps a pattern length to the pattern
            text (as a list of lines)
        min_patterns (dict(int => str list)): same as patterns, but holds
            'stripped' patterns.
        field_registry (mpdlcd.display_fields.FieldRegistry): registry of known
            fields.
    """

    def __init__(self, field_registry, *args, **kwargs):
        super(ScreenPatternList, self).__init__(*args, **kwargs)

        self.patterns = {}
        self.min_patterns = {}
        self.field_registry = field_registry

    def add(self, pattern_txt):
        """Add a pattern to the list.

        Args:
            pattern_txt (str list): the pattern, as a list of lines.
        """
        self.patterns[len(pattern_txt)] = pattern_txt

        low = 0
        high = len(pattern_txt) - 1

        while not pattern_txt[low]:
            low += 1

        while not pattern_txt[high]:
            high -= 1

        min_pattern = pattern_txt[low:high + 1]
        self.min_patterns[len(min_pattern)] = min_pattern

    def __getitem__(self, key):
        """Retrieve the best pattern for a given size.

        The algorithm is:
        - If a pattern is registered for the size, use it
        - Otherwise, find the longest registered pattern shorter thant size, add
            some blank lines before, and return it
        - If no shorter pattern exist, return a blank pattern.

        Args:
            key (int): the target size

        Returns:
            ScreenPattern: the best pattern available for that size
        """
        if key in self.patterns:
            return ScreenPattern(self.patterns[key], self.field_registry)
        for shorter in xrange(key, 0, -1):
            if shorter in self.min_patterns:
                pattern = self.min_patterns[shorter]

                # Try to vertically center the pattern
                prefix = [''] * (key - shorter / 2)
                return ScreenPattern(prefix + pattern, self.field_registry)
        return ScreenPattern([], self.field_registry)
