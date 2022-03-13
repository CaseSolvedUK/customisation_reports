# Copyright (c) 2022, CaseSolved and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from ..utils import *

sql_truthy = "COALESCE(SUM(CASE WHEN `{field}` IS NULL THEN 0 WHEN CAST(`{field}` AS CHAR) IN ('0', '0.0', '') THEN 0 ELSE 1 END), 0) AS used"

df_fields = {
	('Module Def',): ['app_name'],
	('DocType',): ['module', 'issingle', 'name as dt'],
	('DocField',): ['label', 'fieldname', 'fieldtype', 'reqd']
}

def execute(filters=None):
	from pymysql import Error

	# Get DocField list
	fieldstr = get_fieldstr(df_fields)
	where_clause, remainder_filters = process_filters(fieldstr, filters)

	if where_clause:
		where_clause += ' AND '
	else:
		where_clause = 'WHERE '
	where_clause += f'df.fieldtype NOT IN {ignore_fieldtypes}'

	docfields = frappe.db.sql(f"""
		SELECT {fieldstr}
		FROM `tabDocField` df
		LEFT JOIN `tabDocType` dt ON df.parent=dt.name
		LEFT JOIN `tabModule Def` md ON dt.module=md.module_name
		{where_clause}
		ORDER BY dt.name asc
	""", as_dict=1)

	columns = get_columns(df_fields)

	# Count DocField values that are 'truthy'
	filtered = []
	for row in docfields:
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

	columns.append({"label": _("Used Rows"), "fieldname": "used", "fieldtype": "Int"})
	columns.append({"label": _("Total Rows"), "fieldname": "total", "fieldtype": "Int"})
	columns.append({"label": _("Usage %"), "fieldname": "usage", "fieldtype": "Percent"})
	columns.append({"label": _("SQL Error"), "fieldname": "error", "fieldtype": "Data"})

	return columns, filtered
