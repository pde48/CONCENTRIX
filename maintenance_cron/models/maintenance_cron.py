from odoo import fields, models, api
from datetime import datetime, timedelta
from dateutil.relativedelta import *


class maintenance_cron(models.Model):
    _inherit = "maintenance.request"


    @api.depends('crear_programada', 'secuencia')
    def _compute_programada(self):
        for rec in self:
            if rec.plan_id == 0 and rec.crear_programada and rec.secuencia == 0:
                sql = '''SELECT MAX(plan_id) FROM maintenance_request'''
                self.env.cr.execute(sql)
                max_value = self.env.cr.fetchall()
                if max_value:
                    max_value = max_value[0][0]
                    rec.plan_id = int(max_value)+1
                
            if not rec.crear_programada and rec.secuencia == 0:
                rec.plan_id = 0

    crear_programada = fields.Boolean(string='Crear futuras solicitudes Programadas')
    periodicidad = fields.Integer(string='Periodicidad en meses')
    plan_id =  fields.Integer(string='Id Solicitud',default=0, compute='_compute_programada', store=True)
    secuencia = fields.Integer(string='Secuencia',default=0)


    def auto_maintenance(self):
        state_done_ids = self.env['maintenance.stage'].search([('done','=',True)])
        state_ids = []
        if state_done_ids:
            state_ids = [i.id for i in state_done_ids]

        state_new_ids = self.env['maintenance.stage'].search([('new_stage','=',True)])
        state_new = []
        if state_new_ids:
            state_new = [i.id for i in state_new_ids][0]
  
        hoy = datetime.now()
        maintenance_ids = self.env['maintenance.request'].search([('crear_programada','=',True),('periodicidad','>=',1),('stage_id','in',state_ids),('plan_id','!=',0)])
        planificaciones_ids = [i.plan_id for i in maintenance_ids]
        
        if planificaciones_ids:
            planificaciones_ids = set(planificaciones_ids)
            
            for i in planificaciones_ids:
                sin_finalizar = self.env['maintenance.request'].search([('plan_id','=',i),('stage_id','not in',state_ids)])
                
                if not sin_finalizar:
                    maintenance_ids = self.env['maintenance.request'].search([('stage_id','in',state_ids),('plan_id','=',i)], order='schedule_date desc')
                    if maintenance_ids:
                        last_maintenance_id = maintenance_ids[0]
                        
                        if last_maintenance_id.schedule_date and last_maintenance_id.crear_programada:
                            fecha_siguiente = last_maintenance_id.schedule_date + relativedelta(months=+int(last_maintenance_id.periodicidad)) 
                            #hoy_f= datetime.strptime(hoy, '%Y-%m-%d')
                            resta_dias = fecha_siguiente - hoy
                            faltan_dias = resta_dias / timedelta(days=1)

                            if faltan_dias<=31:
                                new_record = last_maintenance_id.copy()
                                sec = last_maintenance_id.secuencia + 1
                                new_record.update({'plan_id':last_maintenance_id.plan_id,'schedule_date':fecha_siguiente,'request_date':hoy.strftime("%Y-%m-%d"),'secuencia':sec, 'color':11, 'stage_id':state_new})                    
                                


class maintenance_stage(models.Model):
    _inherit = "maintenance.stage"
    new_stage = fields.Boolean(string='Solicitudes Nuevas')





    ##1) Es necesario marcar una etapa como inicial "new_satage"
    ##2) Las nuevas solicitudes tendran un ID de planificacion que sera heredado a sus hijos.
    ##  Cada hijo generara +1 en secuencia
    ##3) Si por Id de planificacion existen sin terminar solicitudes no se generan nuevas
    ##4) El ultimo hijo puede terminar la cadea de "Solicitudes automaticas", quitando el check 
    ##5) Visualmente las programadas tienen color violeta.
    ##6) Cuando falte 31 dias para la siguiente solicitud ahi se crea.
    ##
    ##
