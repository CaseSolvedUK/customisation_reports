# Copyright (c) 2022, CaseSolved and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from ..utils import *

sql_truthy = "SUM(CASE WHEN `{field}` IS NULL THEN 0 WHEN CAST(`{field}` AS CHAR) IN ('0', '0.0', '') THEN 0 ELSE 1 END)"

df_fields = {
	('Module Def',): ['app_name'],
	('DocType',): ['module', 'issingle', 'name as dt'],
	('DocField',): ['label', 'fieldname', 'fieldtype', 'reqd']
}

def execute(filters=None):
	from pymysql import MySQLError

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
			# Set mariadb max statement time=3s for large tables
			sql  =  'SET STATEMENT max_statement_time=3 FOR SELECT COUNT(*) AS total, '
			truthy = sql_truthy.format(field=fn)
			sql +=  f'COALESCE({truthy}, 0) AS used '
			sql += f'FROM `tab{dt}` '
			data = frappe.db.sql(sql, as_dict=0)[0]
			total, used = data
		except MySQLError as e:
			used = 0
			total = 0
			# Unknown column or query timeout
			if e.args[0] in (1054, 1969):
				error = e.args[1]
			# Table doesn't exist
			elif e.args[0] == 1146 and row.get('issingle'):
				truthy = sql_truthy.format(field='value')
				used = frappe.db.sql(f"""SELECT {truthy} FROM `tabSingles` WHERE doctype='{dt}' AND field='{fn}' """, as_dict=0)[0][0]
				if used is None:
					used, total = 0, 0
					# Mimic Unknown column
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
