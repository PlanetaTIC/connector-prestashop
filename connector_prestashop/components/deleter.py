# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import threading

from odoo.tools.translate import _
from odoo.addons.component.core import AbstractComponent


class PrestashopDeleter(AbstractComponent):
    """ Base deleter for PrestaShop """

    _name = 'prestashop.deleter'
    _inherit = 'base.deleter'
    _usage = 'record.exporter.deleter'

    def run(self, model_name, prestashop_id, record=None):
        """ Run the synchronization

        :param binding_id: identifier of the binding record to export
        """
        self.prestashop_id = prestashop_id

        result = self._run(prestashop_id, record)

        # commit so we keep the external ID removed if several cascading
        # exports are called and one of them fails
        # do never commit during tests
        if not getattr(threading.currentThread(), 'testing', False):
            self.env.cr.commit()  # pylint: disable=invalid-commit

        return result
