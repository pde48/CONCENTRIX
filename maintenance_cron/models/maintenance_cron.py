# Copyright 2019 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class MaintenanceTeam(models.Model):
    _inherit = "maintenance.request"

    crear_programada = fields.Boolean(string='Crear solicitud Programadas')
    periodicidad = fields.Integer(string='Periodicidad en meses')
