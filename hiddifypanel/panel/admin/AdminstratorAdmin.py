from hiddifypanel.panel.auth import login_required
import hiddifypanel.panel.auth as auth
from wtforms.validators import Regexp
from hiddifypanel.models import *
from wtforms.validators import Regexp, ValidationError
from .adminlte import AdminLTEModelView
from flask_babelex import gettext as __
from flask_babelex import lazy_gettext as _
from hiddifypanel.panel import hiddify
from flask import Markup, current_app, request
from flask import g
import datetime
from wtforms import SelectField
import hiddifypanel.panel.auth as auth


class AdminModeField(SelectField):
    def __init__(self, label=None, validators=None, **kwargs):
        super(AdminModeField, self).__init__(label, validators, **kwargs)
        if g.account.mode in [AdminMode.agent, AdminMode.admin]:
            self.choices = [(AdminMode.agent.value, 'agent')]
        elif g.account.mode == AdminMode.admin:
            self.choices = [(AdminMode.agent.value, 'agent'), (AdminMode.admin.value, 'Admin'),]
        elif g.account.mode == AdminMode.super_admin:
            self.choices = [(AdminMode.agent.value, 'agent'), (AdminMode.admin.value, 'Admin'), (AdminMode.super_admin.value, 'Super Admin')]


class SubAdminsField(SelectField):
    def __init__(self, label=None, validators=None, *args, **kwargs):
        kwargs.pop("allow_blank")
        super().__init__(label, validators, *args, **kwargs)
        self.choices = [(admin.id, admin.name) for admin in g.account.sub_admins]
        self.choices += [(g.account.id, g.account.name)]


class AdminstratorAdmin(AdminLTEModelView):
    column_hide_backrefs = False
    column_list = ["name", 'UserLinks', 'mode', 'can_add_admin', 'max_active_users', 'max_users', 'online_users', 'comment']
    form_columns = ["name", 'mode', 'can_add_admin', 'max_active_users', 'max_users', 'comment', "uuid"]
    list_template = 'model/admin_list.html'
    # edit_modal = True
    # form_overrides = {'work_with': Select2Field}

    form_overrides = {
        'mode': AdminModeField,
        'parent_admin': SubAdminsField
    }
    column_labels = {
        "Actions": _("actions"),
        "UserLinks": _("user.user_links"),
        "name": _("user.name"),
        "mode": _("Mode"),
        "uuid": _("user.UUID"),
        "comment": _("Note"),
        'max_active_users': _("Max Active Users"),
        'max_users': _('Max Users'),
        "online_users": _("Online Users"),
        'can_add_admin': _("Can add sub admin")

    }
    form_args = {
        'uuid': {
            'validators': [Regexp(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', message=__("Should be a valid uuid"))]
            #     'label': 'First Name',
            #     'validators': [required()]
        }}

    column_descriptions = dict(
        comment=_("Add some text that is only visible to super_admin."),
        mode=_("Define the admin mode. "),
    )
    # create_modal = True
    can_export = False

    # column_list = ["domain",'sub_link_only', "mode","alias", "domain_ip", "cdn_ip"]
    # column_editable_list=["domain"]
    # column_filters=["domain","mode"]

    column_searchable_list = ["name", "uuid"]

    # form_columns=['domain','sub_link_only','alias','mode','cdn_ip','show_domains']

    def _ul_formatter(view, context, model, name):

        return Markup(" ".join([hiddify.get_html_user_link(model, d) for d in get_panel_domains()]))

    @property
    def can_create(self):
        return g.account.can_add_admin or g.account.mode == AdminMode.super_admin

    def _name_formatter(view, context, model, name):

        d = request.host
        if d:

            href = hiddify.get_account_panel_link(model, d) + f'#{model.name}'
            link = f"<a target='_blank' class='share-link' data-copy='{href}' href='{href}'>{model.name} <i class='fa-solid fa-arrow-up-right-from-square'></i></a>"
            if model.parent_admin:
                return Markup(model.parent_admin.name + "&rlm;&lrm; / &rlm;&lrm;"+link)
            return Markup(link)
        else:
            return model.name

    def _online_users_formatter(view, context, model, name):
        last_day = datetime.datetime.now()-datetime.timedelta(days=1)
        u = model.recursive_users_query().filter(User.last_online > last_day).count()
        t = model.recursive_users_query().count()
        # actives=[u for u in model.recursive_users_query().all() if u.is_active]
        # allusers=model.recursive_users_query().count()
        # onlines=[p for p in  users  if p.last_online and p.last_online>last_day]
        # return Markup(f"<a class='btn btn-xs btn-default' href='{url_for('flask.user.index_view',admin_id=model.id)}'> {_('Online')}: {onlines}</a>")
        rate = round(u*100/(t+0.000001))
        state = "danger" if u >= t else ('warning' if rate > 80 else 'success')
        color = "#ff7e7e" if u >= t else ('#ffc107' if rate > 80 else '#9ee150')
        return Markup(f"""
        <div class="progress progress-lg position-relative" style="min-width: 100px;">
          <div class="progress-bar progress-bar-striped" role="progressbar" style="width: {rate}%;background-color: {color};" aria-valuenow="{rate}" aria-valuemin="0" aria-valuemax="100"></div>
              <span class='badge position-absolute' style="left:auto;right:auto;width: 100%;font-size:1em">{u} {_('user.home.usage.from')} {t}</span>

        </div>
        """)

    def _max_users_formatter(view, context, model, name):
        u = model.recursive_users_query().count()
        if model.mode == AdminMode.super_admin:
            return f"{u} / ∞"
        t = model.max_users
        rate = round(u*100/(t+0.000001))
        state = "danger" if u >= t else ('warning' if rate > 80 else 'success')
        color = "#ff7e7e" if u >= t else ('#ffc107' if rate > 80 else '#9ee150')
        return Markup(f"""
        <div class="progress progress-lg position-relative" style="min-width: 100px;">
          <div class="progress-bar progress-bar-striped" role="progressbar" style="width: {rate}%;background-color: {color};" aria-valuenow="{rate}" aria-valuemin="0" aria-valuemax="100"></div>
              <span class='badge position-absolute' style="left:auto;right:auto;width: 100%;font-size:1em">{u} {_('user.home.usage.from')} {t}</span>

        </div>
        """)

    def _max_active_users_formatter(view, context, model, name):

        actives = [u for u in model.recursive_users_query().all() if u.is_active]
        u = len(actives)
        if model.mode == AdminMode.super_admin:
            return f"{u} / ∞"
        t = model.max_active_users
        rate = round(u*100/(t+0.000001))
        state = "danger" if u >= t else ('warning' if rate > 80 else 'success')
        color = "#ff7e7e" if u >= t else ('#ffc107' if rate > 80 else '#9ee150')
        return Markup(f"""
        <div class="progress progress-lg position-relative" style="min-width: 100px;">
          <div class="progress-bar progress-bar-striped" role="progressbar" style="width: {rate}%;background-color: {color};" aria-valuenow="{rate}" aria-valuemin="0" aria-valuemax="100"></div>
              <span class='badge position-absolute' style="left:auto;right:auto;width: 100%;font-size:1em">{u} {_('user.home.usage.from')} {t}</span>

        </div>
        """)

    column_formatters = {
        'name': _name_formatter,
        'online_users': _online_users_formatter,
        'max_users': _max_users_formatter,
        'max_active_users': _max_active_users_formatter,
        'UserLinks': _ul_formatter

    }

    def search_placeholder(self):
        return f"{_('search')} {_('user.UUID')} {_('user.name')}"

    # @login_required(roles={Role.super_admin, Role.admin})
    def is_accessible(self):
        if login_required(roles={Role.super_admin, Role.admin})(lambda: True)() != True:
            return False
        return True

    def inaccessible_callback(self, name, **kwargs):
        return auth.redirect_to_login()  # type: ignore

    def get_query(self):
        # Get the base query
        query = super().get_query()

        admin_ids = g.account.recursive_sub_admins_ids()
        query = query.filter(AdminUser.id.in_(admin_ids))

        return query

    # Override get_count_query() to include the filter condition in the count query
    def get_count_query(self):
        # Get the base count query
        query = super().get_count_query()

        admin_ids = g.account.recursive_sub_admins_ids()
        query = query.filter(AdminUser.id.in_(admin_ids))

        return query

    def on_model_change(self, form, model, is_created):

        # if model.id==1:
        #     model.parent_admin_id=0
        #     model.parent_admin=None
        # else:
        #     model.parent_admin_id=1
        #     model.parent_admin=AdminUser.query.filter(AdminUser.id==1).first()
        if model.id != 1 and model.parent_admin == None:
            model.parent_admin_id = g.account.id
            model.parent_admin = g.account

        if g.account.mode != AdminMode.super_admin and model.mode == AdminMode.super_admin:
            raise ValidationError("Sub-Admin can not have more power!!!!")
        if model.mode == AdminMode.agent and model.mode != AdminMode.agent:
            raise ValidationError("Sub-Admin can not have more power!!!!")

    def on_model_delete(self, model):
        model.remove()

    def get_query_for_parent_admin(self):
        admin_user_id = self.get_pk_value()
        sub_admins_ids = set(recursive_sub_admins_ids(AdminUser.query.get(admin_user_id)))
        return AdminUser.query.filter(AdminUser.id.in_(sub_admins_ids)).with_entities(AdminUser.id, AdminUser.name)

    def on_form_prefill(self, form, id=None):

        if g.account.mode != AdminMode.super_admin:
            del form.mode
            del form.can_add_admin

        if g.account.id == form._obj.id:
            del form.max_users
            del form.max_active_users
            del form.comment
            del form.can_add_admin
            if getattr(form, 'mode'):
                del form.mode
        elif form._obj.mode == AdminMode.super_admin:
            del form.max_users
            del form.max_active_users
            del form.can_add_admin
