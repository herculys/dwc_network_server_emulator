"""DWC Network Server Emulator

    Copyright (C) 2014 polaris-
    Copyright (C) 2014 ToadKing
    Copyright (C) 2014 AdmiralCurtiss
    Copyright (C) 2015 Sepalani

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import copy


def parse_gamespy_message(message):
    """Parse a GameSpy message."""
    stack = []
    messages = {}
    msg = message

    while len(msg) > 0 and msg[0] == '\\' and "\\final\\" in msg:
        # Find the command
        # Don't search for more commands if there isn't a \final\, save the
        # left over for the next packet
        found_command = False
        while len(msg) > 0 and msg[0] == '\\':
            keyEnd = msg[1:].index('\\') + 1
            key = msg[1:keyEnd]
            msg = msg[keyEnd + 1:]

            if key == "final":
                break

            if '\\' in msg:
                if msg[0] == '\\':
                    value = ""
                else:
                    valueEnd = msg[1:].index('\\')
                    value = msg[:valueEnd + 1]
                    msg = msg[valueEnd + 1:]
            else:
                value = msg

            if not found_command:
                messages['__cmd__'] = key
                messages['__cmd_val__'] = value
                found_command = True

            messages[key] = value

        stack.append(messages)
        messages = {}

    # Return msg so we can prepend any leftover commands to the next packet.
    return stack, msg


def create_gamespy_message_from_dict(messages_orig):
    """Generate a list based on the input dictionary.

    The main command must also be stored in __cmd__ for it to put the
    parameter at the beginning.
    """
    # Deep copy the dictionary because we don't want the original to be
    # modified
    messages = copy.deepcopy(messages_orig)

    if "__cmd__" in messages:
        cmd = messages['__cmd__']
        messages.pop('__cmd__', None)
    else:
        cmd = ""

    if "__cmd_val__" in messages:
        cmd_val = messages['__cmd_val__']
        messages.pop('__cmd_val__', None)
    else:
        cmd_val = ""

    if cmd in messages:
        messages.pop(cmd, None)

    l = [("__cmd__", cmd), ("__cmd_val__", cmd_val)]
    l.extend([(message, messages[message]) for message in messages])

    return l


def create_gamespy_message_from_list(messages):
    """Generate a string based on the input list."""
    d = {}
    cmd = ""
    cmd_val = ""

    query = ""
    for message in messages:
        if len(message) == 1:
            query += str(message[0])
        elif message[0] == "__cmd__":
            cmd = str(message[1]).strip('\\')
        elif message[0] == "__cmd_val__":
            cmd_val = str(message[1]).strip('\\')
        else:
            query += "\\%s\\%s" % (str(message[0]).strip('\\'),
                                   str(message[1]).strip('\\'))

    if cmd:
        # Prepend the main command if one was found.
        query = "\\%s\\%s%s" % (cmd, cmd_val, query)

    return query


def create_gamespy_message(messages, id=None):
    """Create a message based on a dictionary (or list) of parameters."""
    query = ""

    if isinstance(messages, dict):
        messages = create_gamespy_message_from_dict(messages)

    # Check for an id if the id needs to be updated.
    # If it already exists in the list then update it, else add it
    if id is not None:
        for message in messages:
            if message[0] == "id":
                messages.pop(messages.index(message))
                messages.append(("id", str(id)))
                id = None  # Updated id, so don't add it to the query later
                break  # Found id, stop searching list

    query = create_gamespy_message_from_list(messages)

    if id is not None:
        query += create_gamespy_message_from_list([("id", id)])

    query += "\\final\\"

    return query
