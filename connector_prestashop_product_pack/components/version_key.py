# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models
from odoo.addons.component.core import Component


class VersionKey1616(Component):
    _inherit = '_prestashop.version.key.1.6.1.6'

    keys = {
        'product_bundle': 'product',
    }
