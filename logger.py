#
# logger
#
# Copyright (c) 2020 Daniel Dean <dd@danieldean.uk>.
#
# Licensed under The MIT License a copy of which you should have
# received. If not, see:
#
# http://opensource.org/licenses/MIT
#

class Logger:

    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, message):
        if message != '\n' and not message.isspace():
            self.logger.log(self.level, message.rstrip())

    def flush(self):
        pass
