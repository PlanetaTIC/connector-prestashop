# Copyright 2021 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models, api
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import (
    mapping, external_to_m2o, only_create)
from odoo.addons.queue_job.exception import FailedJobError


class ProductTemplateImporter(Component):
    _inherit = 'prestashop.product.template.importer'

    def _import_dependencies(self):
        super(ProductTemplateImporter, self)._import_dependencies()
        self._import_bundle_dependencies()

    def _import_bundle_dependencies(self):
        # Import products included in the bundle (product_pack):
        prestashop_record = self.prestashop_record
        associations = prestashop_record.get('associations', {})

        ps_key = self.backend_record.get_version_ps_key('product_bundle')
        bundle = associations.get('product_bundle', {}).get(ps_key, [])

        if not isinstance(bundle, list):
            bundle = [bundle]
        for ps_packed_product in bundle:
            self._import_dependency(
                ps_packed_product['id'],
                'prestashop.product.template',
                always=True)
            if ps_packed_product.get('id_product_attribute', '0') != '0':
                self._import_dependency(
                    ps_packed_product['id_product_attribute'],
                    'prestashop.product.combination',
                    always=True)

    def _after_import(self, binding):
        super(ProductTemplateImporter, self)._after_import(binding)
        self.import_bundle(binding)

    def import_bundle(self, binding):
        prestashop_record = self._get_prestashop_data()
        associations = prestashop_record.get('associations', {})

        ps_key = self.backend_record.get_version_ps_key('product_bundle')
        bundle = associations.get('product_bundle', {}).get(ps_key, [])

        if not isinstance(bundle, list):
            bundle = [bundle]
        template_binder = self.binder_for('prestashop.product.template')
        combination_binder = self.binder_for('prestashop.product.combination')

        pack_lines_vals = [(5, False, False)]
        pack_ok = False
        pack_type = False
        pack_component_price = False
        for ps_packed_product in bundle:
            pack_ok = True
            pack_type = 'detailed'
            pack_component_price = 'ignored'

            packed_product_tmpl = template_binder.to_internal(
                ps_packed_product['id'],
                unwrap=True,
            )
            if ps_packed_product.get('id_product_attribute', '0') == '0':
                packed_product = packed_product_tmpl.product_variant_ids[0]
            else:
                # get product combination:
                packed_product = combination_binder.to_internal(
                    ps_packed_product['id_product_attribute'])
            pack_line_vals = {
                'product_id': packed_product.id,
                'quantity': ps_packed_product['quantity'],
            }
            pack_lines_vals.append((0, False, pack_line_vals))
        binding.odoo_id.write({
            'pack_ok': pack_ok,
            'pack_type': pack_type,
            'pack_line_ids': pack_lines_vals,
            'pack_component_price': pack_component_price,
        })


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

        product_tmpl_binder = self.binder_for('prestashop.product.template')
        combination_binder = self.binder_for('prestashop.product.combination')
        pack_lines_vals = [(5, False, False)]
        for ps_packed_product in ps_packed_products:
            packed_product_tmpl = product_tmpl_binder.to_internal(
                ps_packed_product['id'],
                unwrap=True,
            )
            if ps_packed_product.get('id_product_attribute', '0') == '0':
                packed_product = packed_product_tmpl.product_variant_ids[0]
            else:
                # get product combination:
                packed_product = combination_binder.to_internal(
                    ps_packed_product['id_product_attribute'])
            if not packed_product:
                raise FailedJobError(_("Missing packed product"))
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
