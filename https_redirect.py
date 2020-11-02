#!/usr/bin/python3

#
# https_redirect
#
# Copyright (c) 2020 Daniel Dean <dd@danieldean.uk>.
#
# Licensed under The MIT License a copy of which you should have
# received. If not, see:
#
# http://opensource.org/licenses/MIT
#

import web

urls = (
    '/.*', 'redirect'
)

app = web.application(urls, globals())


class redirect:
    def GET(self):
        raise web.redirect('https://' + web.ctx.host + web.ctx.path + web.ctx.query)


if __name__ == "__main__":
    web.httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", 8080))
