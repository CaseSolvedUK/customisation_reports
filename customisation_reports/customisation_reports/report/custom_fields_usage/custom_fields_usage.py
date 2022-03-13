# Copyright (c) 2022, CaseSolved and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from ..utils import *

sql_truthy = "COALESCE(SUM(CASE WHEN `{field}` IS NULL THEN 0 WHEN CAST(`{field}` AS CHAR) IN ('0', '0.0', '') THEN 0 ELSE 1 END), 0) AS used"

cf_fields = {
	('Module Def',): ['app_name'],
	('DocType',): ['module', 'issingle'],
	('Custom Field',): ['dt', 'label', 'fieldname', 'fieldtype', 'name as custom_field_name']
}

def execute(filters=None):
	from pymysql import Error

	# Get Custom Field list
	fieldstr = get_fieldstr(cf_fields)
	where_clause, remainder_filters = process_filters(fieldstr, filters)

	custom_fields = frappe.db.sql(f"""
		SELECT {fieldstr}
		FROM `tabCustom Field` cf
		LEFT JOIN `tabDocType` d ON cf.dt=d.name
		LEFT JOIN `tabModule Def` md ON d.module=md.module_name
		{where_clause}
		ORDER BY d.name asc
	""", as_dict=1)

	columns = get_columns(cf_fields, modify_report_columns)

	# Count Custom Field values that are 'truthy'
	filtered = []
	for row in custom_fields:
		dt = row.get('dt')
		fn = row.get('fieldname')
		try:
			error = ''
			sql  =  ' SELECT COUNT(*) AS total, '
			sql +=  sql_truthy.format(field=fn)
			sql += f' FROM `tab{dt}` '
			data = frappe.db.sql(sql, as_dict=0)[0]
			total, used = data
		except Error as e:
			used = 0
			total = 0
			if e.args[0] == 1054:
				error = e.args[1]
			elif row.get('issingle'):
				sql = sql_truthy.format(field='value')
				used = frappe.db.sql(f"""SELECT {sql} FROM `tabSingles` WHERE doctype='{dt}' AND field='{fn}' """, as_dict=0)[0][0]
				total = 1
			else:
				raise

		usage = ((100 * used) / total) if used else 0.0
		row['used'] = used
		row['total'] = total
		row['usage'] = usage
		row['error'] = error
		# Filter
		for filt_field, filt_value in remainder_filters.items():
			if filt_field == 'usage' and usage > filt_value:
				break
			if filt_field == 'error' and filt_value not in error:
				break
		else:
			filtered.append(row)

	columns.append({"label": _("Used"), "fieldname": "used", "fieldtype": "Int"})
	columns.append({"label": _("Total"), "fieldname": "total", "fieldtype": "Int"})
	columns.append({"label": _("Usage %"), "fieldname": "usage", "fieldtype": "Percent"})
	columns.append({"label": _("Error"), "fieldname": "error", "fieldtype": "Data"})

	return columns, filtered

def modify_report_columns(doctype, field, column):
	"Changes to match any data manipulation or missing column info"
	if doctype in ("Custom Field"):
		if field == "custom_field_name":
			return {"label": _("Custom Field Name"), "fieldname": "custom_field_name", "fieldtype": "Link", "options": "Custom Field"}
	return column
