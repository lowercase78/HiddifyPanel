from .ProxyDetailsAdmin import ProxyDetailsAdmin
# from .CommercialSettings import CommercialSettings
from hiddifypanel.panel import hiddify
from hiddifypanel.models import *
from hiddifypanel.panel.database import db
from hiddifypanel import Events, hutils

commercial = False


def init_app(app):
    from .restapi import v1 as restapi_v1
    restapi_v1.init_app(app)
    from .restapi.v2 import admin as api_v2_admin
    from .restapi.v2 import user as api_v2_user
    from .restapi.v2 import hello as api_v2_hello
    api_v2_admin.init_app(app)
    api_v2_user.init_app(app)
    api_v2_hello.init_app(app)
    return


def is_valid():
    return True


def config_changed_event(conf, old_value):
    if conf.key == ConfigEnum.is_parent:
        if conf.value and not is_valid():
            set_hconfig(ConfigEnum.is_parent, False)
        if not old_value and conf.value:
            Domain.query.delete()
            new_domain = hutils.get_ip(hutils.AF_INET)+".sslip.io"
            if not ParentDomain.query.filter(ParentDomain.domain == new_domain).first():
                db.session.add(ParentDomain(domain=hutils.get_ip(hutils.AF_INET)+".sslip.io"))
                db.session.commit()


Events.config_changed.subscribe(config_changed_event)


# def db_init_event(db_version):
#     # if not is_valid():
#     #     db.add(BoolConfig(ConfigEnum.db_version,10,child_id=0))
#     #     db.add(BoolConfig(ConfigEnum.db_version,11,child_id=0))
#     #     return
#     if hconfig(ConfigEnum.is_parent) and ParentDomain.query.count()==0:
#         external_ip=hiddify.get_ip(4)
#         db.session.add(ParentDomain(domain=f"{external_ip}.sslip.io",show_domains=[]))
# Events.db_init_event.subscribe(db_init_event)


def admin_prehook(flaskadmin, admin_bp):
    from .ParentDomainAdmin import ParentDomainAdmin
    flaskadmin.add_view(ParentDomainAdmin(ParentDomain, db.session))
    flaskadmin.add_view(ProxyDetailsAdmin(Proxy, db.session))
    # CommercialSettings.register(admin_bp)


Events.admin_prehook.subscribe(admin_prehook)


# def db_prehook():
# flaskadmin.add_view(ParentDomainAdmin(ParentDomain, db.session))
# from . import ProxyDominAdmin
# CommercialSettings.register(admin_bp)

# Events.db_prehook.subscribe(db_prehook)
