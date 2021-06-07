# Copyright 2021 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models, api
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import (
    mapping, external_to_m2o, only_create)


class TemplateMapper(Component):
    _inherit = 'prestashop.product.template.mapper'

    @mapping
    def pack_line_ids(self, record):
        ps_packed_products = record['associations'].get('product_bundle', {}).\
            get(self.backend_record.get_version_ps_key('product'), [])
        if not isinstance(ps_packed_products, list):
            ps_packed_products = [ps_packed_products]
        if not ps_packed_products:
            return {
                'pack_ok': False,
                'pack_line_ids': False,
            }

        binder = self.binder_for('prestashop.product.template')
        pack_lines_vals = [(5, False, False)]
        for ps_packed_product in ps_packed_products:
            packed_product_tmpl = binder.to_internal(
                ps_packed_product['id'],
                unwrap=True,
            )
            if ps_packed_product.get('id_product_attribute', '0') == '0':
                packed_product = packed_product_tmpl.product_variant_ids[0]
            else:
                # get product combination:
                binder = self.binder_for('prestashop.product.combination')
                packed_product = binder.to_internal(
                    ps_packed_product['id_product_attribute'])
            pack_line_vals = {
                'product_id': packed_product.id,
                'quantity': ps_packed_product['quantity'],
            }
            pack_lines_vals.append((0, False, pack_line_vals))
        res = {
            'pack_ok': True,
            'pack_type': 'non_detailed',
            'pack_line_ids': pack_lines_vals}
        return res
