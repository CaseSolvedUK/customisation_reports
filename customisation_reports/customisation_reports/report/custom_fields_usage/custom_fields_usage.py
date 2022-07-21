# Copyright (c) 2022, CaseSolved and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from ..utils import *
from frappe.model import no_value_fields

sql_truthy = "SUM(CASE WHEN `{field}` IS NULL THEN 0 WHEN CAST(`{field}` AS CHAR) IN ('0', '0.0', '') THEN 0 ELSE 1 END)"

cf_fields = {
	('Module Def',): ['app_name'],
	('DocType',): ['module', 'issingle'],
	('Custom Field',): ['dt', 'label', 'fieldname', 'fieldtype', 'options', 'reqd', 'name as custom_field_name']
}

def execute(filters=None):
	from pymysql import Error

	# Get Custom Field list
	fieldstr = get_fieldstr(cf_fields)
	where_clause, remainder_filters = process_filters(fieldstr, filters)
	if where_clause:
		where_clause += ' AND '
	else:
		where_clause = 'WHERE '
	where_clause += f'cf.fieldtype NOT IN {no_value_fields}'


	custom_fields = frappe.db.sql(f"""
		SELECT {fieldstr}
		FROM `tabCustom Field` cf
		LEFT JOIN `tabDocType` dt ON cf.dt=dt.name
		LEFT JOIN `tabModule Def` md ON dt.module=md.module_name
		{where_clause}
		ORDER BY dt.name asc
	""", as_dict=1)

	columns = get_columns(cf_fields)

	# Count Custom Field values that are 'truthy'
	filtered = []
	for row in custom_fields:
		dt = row.get('dt')
		fn = row.get('fieldname')
		try:
			error = ''
			sql  =  ' SELECT COUNT(*) AS total, '
			truthy = sql_truthy.format(field=fn)
			sql +=  f'COALESCE({truthy}, 0) AS used '
			sql += f'FROM `tab{dt}` '
			data = frappe.db.sql(sql, as_dict=0)[0]
			total, used = data
		except Error as e:
			used = 0
			total = 0
			if e.args[0] == 1054:
				error = e.args[1]
			elif row.get('issingle'):
				truthy = sql_truthy.format(field='value')
				used = frappe.db.sql(f"""SELECT {truthy} FROM `tabSingles` WHERE doctype='{dt}' AND field='{fn}' """, as_dict=0)[0][0]
				if used is None:
					used, total = 0, 0
					error = f"Unknown column '{fn}' in 'field list'"
				else:
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

	columns.append({"label": _("Used Rows"), "fieldname": "used", "fieldtype": "Int"})
	columns.append({"label": _("Total Rows"), "fieldname": "total", "fieldtype": "Int"})
	columns.append({"label": _("Usage %"), "fieldname": "usage", "fieldtype": "Percent"})
	columns.append({"label": _("SQL Error"), "fieldname": "error", "fieldtype": "Data"})

	return columns, filtered
